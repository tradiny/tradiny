# This software is licensed under a dual license:
#
# 1. Creative Commons Attribution-NonCommercial (CC BY-NC)
#    for individuals and open source projects.
# 2. Commercial License for business use.
#
# For commercial inquiries, contact: license@tradiny.com
#
# For more details, refer to the LICENSE.md file in the root directory of this project.

from multiprocessing import Process, Queue

import concurrent.futures
import time
import logging
from queue import Empty


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
