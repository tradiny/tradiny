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

from threading import Thread, Event
from multiprocessing import Process, Queue

import os
import signal
import asyncio
import concurrent.futures
import time
import logging
from queue import Empty


from config import Config
from app.globals import providers
from app.handlers import handle_message_from_provider

HANDLER_WORKERS = 5


class MonitoringThread(Thread):
    def __init__(self, provider_class, provider_config, threshold=HANDLER_WORKERS + 1):
        super(MonitoringThread, self).__init__()
        self.provider_class = provider_class
        self.provider_config = provider_config
        self.threshold = threshold
        self.provider = None
        self.provider_started_event = Event()

        self.create_queues()

    def create_queues(self):
        # Queue for communicating active request count
        self.monitoring_request_queue = Queue()
        self.monitoring_response_queue = Queue()
        self.request_queue = Queue()
        self.response_queue = Queue()

    def run(self):
        self.provider = self.initialize_provider()
        self.provider_started_event.set()

        while True:
            time.sleep(60)

            try:
                self.monitoring_request_queue.put("get_active_requests")
                active_requests = self.monitoring_response_queue.get(timeout=10)
                if active_requests > self.threshold:
                    logging.info(
                        f"Active requests {active_requests} reached threshold {self.threshold}. Restarting provider."
                    )
                    self.restart_provider()
            except Empty:
                logging.error("No response received for active requests.")
            except Exception as e:
                logging.error(f"Error: {e}")

    def initialize_provider(self):
        self.create_queues()

        provider = self.provider_class()
        provider.set_monitoring_request_queue(self.monitoring_request_queue)
        provider.set_monitoring_response_queue(self.monitoring_response_queue)
        provider.set_request_queue(self.request_queue)
        provider.set_response_queue(self.response_queue)
        provider.start()

        return provider

    def restart_provider(self):
        os.kill(self.provider.pid, signal.SIGTERM)
        self.provider.join()

        self.provider_started_event.clear()
        self.provider = self.initialize_provider()

    def wait_for_provider_start(self):
        self.provider_started_event.wait()

    def request(self, message):
        self.request_queue.put(message)


class Provider(Process):
    def __init__(self):
        super(Provider, self).__init__()

        self.active_requests = 0

    def set_monitoring_request_queue(self, queue):
        self.monitoring_request_queue = queue

    def set_monitoring_response_queue(self, queue):
        self.monitoring_response_queue = queue

    def set_request_queue(self, queue):
        self.request_queue = queue

    def set_response_queue(self, queue):
        self.response_queue = queue

    def run(self):
        logging.info(f"Starting provider {self.key}.")
        self.init()
        with concurrent.futures.ThreadPoolExecutor(
            max_workers=HANDLER_WORKERS
        ) as executor:
            while True:

                try:
                    request = self.monitoring_request_queue.get_nowait()
                    if request == "get_active_requests":
                        self.monitoring_response_queue.put(self.active_requests)

                except Empty:
                    pass
                except Exception as e:
                    logging.error(f"Error: {e}")

                try:
                    self.active_requests += 1
                    message = self.request_queue.get(timeout=5)

                    if message["action"] == "stop":
                        break

                    if message["action"] == "start_streaming":
                        self.start_streaming(*message["args"])

                    elif message["action"] == "on_close":
                        self.on_close(*message["args"])

                    elif message["action"] == "no_update":
                        self.no_update(*message["args"])

                    else:
                        executor.submit(self.handle_message, message)
                except Empty:
                    continue
                except Exception as e:
                    logging.error(f"Error: {e}")
                finally:
                    self.active_requests -= 1

    def handle_message(self, message):
        self.active_requests += 1

        if message["action"] == "get_history":
            try:
                new_klines = self.get_history(*message["args"])
            except Exception as e:
                new_klines = []
                logging.info(f"Error get history: {e}")

            self.respond(
                {
                    "action": "history",
                    "ws_client": message["ws_client"],
                    "source": self.key,
                    "name": message["name"],
                    "interval": message["interval"],
                    "metadata": message["metadata"],
                    "message_type": message["message_type"],
                    "count": message["count"],
                    "end": message["end"],
                    "range": message["range"],
                    "new_klines": new_klines,
                    "future_key": message["future_key"],
                }
            )

        else:
            logging.info(f"Unknown action: {message['action']}")

        self.active_requests -= 1

    def stop_process(self):
        self.response_queue.put({"action": "stop"})
        self.process.join()

    def request(self, message):
        self.request_queue.put(message)

    def respond(self, message):
        self.response_queue.put(message)


def register_provider(provider):
    providers[provider.provider.key] = provider

    asyncio.ensure_future(handle_message_from_provider(provider))


def initialize_provider(config_key, provider_module, provider_class):
    if getattr(Config, config_key):
        provider_cls = getattr(
            __import__(provider_module, fromlist=[provider_class]), provider_class
        )
        logging.info(f"Starting process for provider {provider_cls.key}.")

        # Start monitoring process with provider class
        monitor = MonitoringThread(provider_cls, config_key)
        monitor.start()

        monitor.wait_for_provider_start()

        return monitor
    else:
        return None


def initialize_providers():
    _providers = []
    provider_configs = [
        ("CSV_FOLDER_PATH", "data_providers.csv", "CSVProvider"),
        ("POLYGON_IO_API_KEY", "data_providers.polygon", "PolygonProvider"),
        ("BINANCE_API_KEY", "data_providers.binance", "BinanceProvider"),
    ]

    for env_key, config_path, provider_class in provider_configs:
        provider = initialize_provider(env_key, config_path, provider_class)
        if provider:
            _providers.append(provider)

    return _providers
