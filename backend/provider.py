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

from multiprocessing import Process, Queue

import asyncio
import concurrent.futures
import time
import logging
from queue import Empty


from config import Config
from app.globals import providers
from app.handlers import handle_message_from_provider


class Provider(Process):
    def __init__(self):
        super(Provider, self).__init__()

        self.to_queue = Queue()
        self.from_queue = Queue()

    def run(self):
        logging.info(f"Starting provider {self.key}.")
        self.init()
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            while True:
                try:
                    message = self.to_queue.get()

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
                except Exception as e:
                    logging.error(f"Error {e}")
                except Empty:
                    continue

    def handle_message(self, message):

        if message["action"] == "get_history":
            try:
                new_klines = self.get_history(*message["args"])
            except Exception as e:
                new_klines = []
                logging.info(f"Error get history: {e}")

            self.send_from(
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

    def send_to(self, message):
        self.to_queue.put(message)

    def send_from(self, message):
        self.from_queue.put(message)

    def stop_process(self):
        self.to_queue.put({"action": "stop"})
        self.process.join()


def register_provider(provider):
    providers[provider.key] = provider

    asyncio.ensure_future(handle_message_from_provider(provider.from_queue))


def initialize_provider(config_key, provider_module, provider_class):
    if getattr(Config, config_key):
        provider = getattr(
            __import__(provider_module, fromlist=[provider_class]), provider_class
        )()
        logging.info(f"Starting process for provider {provider.key}.")
        provider.start()
        return provider
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
