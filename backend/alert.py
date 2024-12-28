# This software is licensed under a dual license:
#
# 1. Creative Commons Attribution-NonCommercial (CC BY-NC)
#    for individuals and open source projects.
# 2. Commercial License for business use.
#
# For commercial inquiries, contact: license@tradiny.com
#
# For more details, refer to the LICENSE.md file in the root directory of this project.

import queue
import threading
import db
import websockets
import json
import asyncio
import logging
from datetime import datetime, timedelta, timezone
from fastapi import Depends

from log import setup_logging
from config import Config

from alert_evaluate import alert_evaluate

ALERT_DATA = {}  # Empty dict to store alert metadata


# Websocket Subscribe
async def websocket_subscribe(task_queue, alert, i):
    # url = f"ws://{alert['settings']['dataProviderConfig']['url']}/websocket/"
    url = alert["settings"]["dataProviderConfig"]["full_url"]
    logging.info(f"Connecting to {url}")

    for _ in range(3):  # try 3 times
        try:
            async with websockets.connect(url) as ws:
                alert_id = alert["id"]
                ALERT_DATA[alert_id] = {"websocket_client": ws}
                # Send data to the WebSocket server
                logging.info(
                    f"subscribing to... {alert['settings']['dataProviderConfig']['data']}"
                )
                await ws.send(
                    json.dumps(alert["settings"]["dataProviderConfig"]["data"])
                )

                # Listen for updates from the WebSocket server
                async for message in ws:
                    task_queue.put_nowait(
                        {"action": "update", "message": message, "alert": alert}
                    )  # Add message to the task_queue

            break  # if connection is successful, break the loop

        except ConnectionRefusedError:
            logging.error(f"Connection failed. Retrying... {url}")
            await asyncio.sleep(1)  # wait for 1 second before retrying

    else:
        logging.error(f"Failed to connect after 3 attempts: {url}")


# Process new tasks as they arrive
async def process_queue(async_queue: asyncio.Queue, i: int):
    dbconn = db.create_connection(Config.DB)
    while True:
        try:
            task = await async_queue.get()

            action = task["action"]

            if action == "done":
                break
            elif action == "new_alert":
                expire_date = datetime.now(timezone.utc) + timedelta(
                    minutes=int(Config.EXPIRE_ALERT_IN_MINUTES)
                )
                alert = db.add_alert(dbconn, task["settings"], expire_date)
                asyncio.create_task(websocket_subscribe(async_queue, alert, i))
            elif action == "alert":
                alert = db.get_alert_by_id(dbconn, task["alert_id"])
                asyncio.create_task(websocket_subscribe(async_queue, alert, i))
            elif action == "update":
                message = json.loads(task["message"])
                alert = task["alert"]
                data = ALERT_DATA[alert["id"]]

                try:
                    alert_evaluate(dbconn, message, alert, data)
                except Exception as e:
                    logging.error(f"Failed to evaluate alert {alert['id']}: {e}")

        except Exception as e:
            logging.error(f"Error processing task: {e}")
            raise


def queue_to_async(async_queue, task_queue, loop):
    while True:
        task = task_queue.get()  # blocking get
        asyncio.run_coroutine_threadsafe(async_queue.put(task), loop)


class WorkerThread(threading.Thread):
    def __init__(self, task_queue: queue.Queue, i: int):
        super().__init__()
        self.loop = asyncio.new_event_loop()
        self.task_queue = task_queue
        self.i = i

    def run(self):
        asyncio.set_event_loop(self.loop)
        try:
            self.loop.run_until_complete(self.main())
        finally:
            self.loop.close()
            asyncio.set_event_loop(None)

    async def main(self):
        # Create asyncio queue
        async_queue = asyncio.Queue()

        # Create a new thread that will block on get() calls on the task_queue.
        threading.Thread(
            target=queue_to_async, args=(async_queue, self.task_queue, self.loop)
        ).start()

        # Process incoming tasks
        await process_queue(async_queue, self.i)


def spawn_workers(num):
    task_queue = queue.Queue()

    threads = []
    for i in range(num):
        worker_thread = WorkerThread(task_queue, i)
        threads.append(worker_thread)
        worker_thread.start()

    return task_queue, threads


def trigger_worker(task_queue, task):
    task_queue.put_nowait(task)


# Call this function when you want to stop the workers.
def stop_workers(task_queue, threads):
    for _ in threads:
        task_queue.put({"action": "done"})

    for t in threads:
        t.join()


def init_alerts(task_queue, dbconn):
    alerts = db.get_alerts(dbconn)
    logging.info(f"Number of alerts: {len(alerts)}")
    for alert in alerts:
        trigger_worker(task_queue, {"action": "alert", "alert_id": str(alert["id"])})


class AlertQueueWrapper:
    instance = None

    def __init__(self):
        if not AlertQueueWrapper.instance:
            AlertQueueWrapper.instance = self

            self.queue = spawn_workers(int(Config.ALERT_WORKERS))
            dbconn = db.create_connection(Config.DB)
            init_alerts(self.queue[0], dbconn)


def get_queue_wrapper():
    if not AlertQueueWrapper.instance:
        AlertQueueWrapper()
    return AlertQueueWrapper.instance.queue


def init():
    get_queue_wrapper()
