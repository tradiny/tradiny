# This software is licensed under a dual-license model:
# 1. Under the Affero General Public License (AGPL) for open-source use.
# 2. With additional terms tailored to individual users (e.g., traders and investors):
#
#    - Individual users may use this software for personal profit (e.g., trading/investing)
#      without releasing proprietary strategies.
#
#    - Redistribution, public tools, or commercial use require compliance with AGPL
#      or a commercial license. Contact: license@tradiny.com
#
# For full details, see the LICENSE.md file in the root directory of this project.

import ipaddress
import time
from collections import OrderedDict


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
        or is_client_ip_in_local_network(client_ip)
    ):
        return True
    else:
        return False


def is_client_ip_in_local_network(client_ip):
    private_networks = [
        ipaddress.IPv4Network("10.0.0.0/8"),
        ipaddress.IPv4Network("172.16.0.0/12"),
        ipaddress.IPv4Network("192.168.0.0/16"),
    ]
    client_ip_address = ipaddress.IPv4Address(client_ip)

    # Check if the IP is in any of the private network ranges
    for private_network in private_networks:
        if client_ip_address in private_network:
            return True
    return False
