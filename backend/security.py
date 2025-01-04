import docker
import ipaddress
import time
from collections import OrderedDict

_docker_network_cache = {
    "networks": [],
    "last_refresh": 0,
    "refresh_interval": 60 * 60,  # Cache refresh time in seconds
}


class LimitedSizeDict(OrderedDict):
    def __init__(self, max_size, *args, **kwargs):
        self.max_size = max_size
        super().__init__(*args, **kwargs)

    def __setitem__(self, key, value):
        if key in self:
            del self[key]  # Remove existing item to update position
        elif len(self) >= self.max_size:
            self.popitem(last=False)  # Remove the oldest item
        super().__setitem__(key, value)


def clean_old_requests(obj):
    current_time = time.time()
    cutoff_time = current_time - 3600  # 1 hour
    for ip in list(obj.keys()):
        # Remove requests older than 1 hour
        obj[ip] = [t for t in obj[ip] if t > cutoff_time]
        # Remove the IP entry if no recent requests
        if not obj[ip]:
            del obj[ip]


def register_request(obj, ip):
    clean_old_requests(obj)
    obj[ip].append(time.time())


def is_request_allowed(maximum, obj, ip):
    clean_old_requests(obj)
    return len(obj[ip]) < int(maximum)


def is_ip_address_whitelisted(client_ip, WHITELIST_IP):
    if (
        client_ip == "127.0.0.1"
        or client_ip in WHITELIST_IP
        or is_client_ip_in_docker_networks(client_ip)
    ):
        return True
    else:
        return False


def get_docker_networks():
    current_time = time.time()
    # Check if cache needs to be refreshed
    if (
        current_time - _docker_network_cache["last_refresh"]
        > _docker_network_cache["refresh_interval"]
    ):
        refresh_docker_networks_cache()
    return _docker_network_cache["networks"]


def refresh_docker_networks_cache():
    client = docker.from_env()
    networks = []
    for network in client.networks.list():
        ipam_config = network.attrs.get("IPAM", {}).get("Config", [])
        for ipam in ipam_config:
            subnet = ipam.get("Subnet")
            if subnet:
                networks.append(ipaddress.IPv4Network(subnet))
    _docker_network_cache["networks"] = networks
    _docker_network_cache["last_refresh"] = time.time()


def is_client_ip_in_docker_networks(client_ip):
    client_ip_address = ipaddress.IPv4Address(client_ip)
    for docker_subnet in get_docker_networks():
        if client_ip_address in docker_subnet:
            return True
    return False
