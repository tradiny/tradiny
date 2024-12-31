import json
import asyncio
import logging
import websockets
import copy
import re
from collections.abc import Mapping, Sequence
from starlette.websockets import WebSocketState, WebSocketDisconnect

from config import Config
import db
from db import search_data_entities
from worker_thread import Worker

from app.globals import (
    clients
)
from app.connection import safe_send_message

from rules_evaluate import rules_evaluate

scanner_status = {}

def replace_all_in_obj(obj, target_value, replacement_value, visited=None):
    if visited is None:
        visited = {}
        
    obj_id = id(obj)
    if obj_id in visited:
        return visited[obj_id]

    if not isinstance(obj, (Mapping, Sequence)) or isinstance(obj, str):
        if isinstance(obj, str):
            return re.sub(re.escape(target_value), replacement_value, obj)
        return replacement_value if obj == target_value else obj

    if isinstance(obj, Sequence):
        result = []
    else:
        result = {}

    visited[obj_id] = result

    if isinstance(obj, Mapping):
        for key, value in obj.items():
            new_key = key.replace(target_value, replacement_value) if isinstance(key, str) else key
            if isinstance(value, str):
                result[new_key] = re.sub(re.escape(target_value), replacement_value, value)
            else:
                result[new_key] = replace_all_in_obj(value, target_value, replacement_value, visited)
    elif isinstance(obj, Sequence):
        for item in obj:
            result.append(replace_all_in_obj(item, target_value, replacement_value, visited))

    return result


async def scan(dbconn, d, client_id, websocket):

    source_replace = None
    name_replace = None
    interval = None
    for data in d["dataProviderConfig"]["data"]:
        if data["type"] == "data":
            source_replace = data["source"]
            name_replace = data["name"]
            interval = data["interval"]

    data_entries = search_data_entities(dbconn, d.get("search"), type="data", limit=10**6)
    z = len(str(len(data_entries)))

    for i, de in enumerate(data_entries):
        if scanner_status[client_id] == 'stop':
            logging.info(f"Scanner for {client_id} stopped.")
            if client_id in scanner_status: del scanner_status[client_id]
            return

        source = de["details"]["source"]
        name = de["details"]["name"]

        if "name_label" in de["details"]:
            name_label = de["details"]["name_label"]
        else:
            name_label = name

        category = ""
        if "categories" in de["details"]:
            category = de["details"]["categories"][0] + " / "
        
        try:
            await websocket.send_text(json.dumps(
                {
                    "type": "scan_progress",
                    "message": f"Scanning {i+1:0{z}}/{len(data_entries)}"
                }
            ))
        except WebSocketDisconnect:
            logging.error("Attempted to write to a disconnected WebSocket.")
            logging.info("Scanning stopped")
            if client_id in scanner_status: del scanner_status[client_id]
            return
        except Exception as e:
            logging.error(f"Error while sending message: {e}")
            logging.info("Scanning stopped")
            if client_id in scanner_status: del scanner_status[client_id]
            return

        di = copy.deepcopy(d)
        if source != source_replace:
            di = replace_all_in_obj(
                di,
                source_replace,
                source
            )
        if name != name_replace:
            di = replace_all_in_obj(
                di,
                name_replace,
                name
            )

        data_request = di["dataProviderConfig"]["data"]
        for dr in data_request:
            dr["stream"] = False # disable streaming new data
        expected_init_messages = len(data_request)
        actual_init_messages = 0
        timeout = 15

        lastDataPoint = {}

        url = d["dataProviderConfig"]["full_url"]
        # logging.info(f"Connecting to {url}")
        async with websockets.connect(url) as ws:
            async def receive_data():
                nonlocal actual_init_messages

                await ws.send(json.dumps(data_request))
                async for message in ws:
                    message = json.loads(message)

                    if message['type'] == "data_init":
                        lastDataPoint.update(message["data"][-1])
                        actual_init_messages += 1
                        # logging.info(f"Received {message['type']} for {message['source']}, {message['name']}, {message['interval']}")
                    elif message['type'] == "no_data":
                        # logging.info(f"Received {message['type']} for {message}")
                        break
                    elif message['type'] == "indicator_init":
                        lastDataPoint.update(message["data"][-1])
                        actual_init_messages += 1
                        # logging.info(f"Received {message['type']} for {message['id']}")
                    # else:
                    #     logging.info(f"Received {message['type']}")
                        
                    if actual_init_messages == expected_init_messages:
                        break

            try:
                await asyncio.wait_for(receive_data(), timeout)
                logging.info(f"Got data: {lastDataPoint}")
            except asyncio.TimeoutError:
                logging.info(f"Timeout reached: did not receive all {expected_init_messages} expected messages in {timeout} seconds.")
                
            
            
        rules = di["rules"]
        operators = di["operators"]
        indicators = di["indicators"]

        result = rules_evaluate(rules, operators, indicators, lastDataPoint)

        if result:
            try:
                await websocket.send_text(json.dumps(
                    {
                        "type": "scan_result",
                        "data": de
                    }
                ))
            except WebSocketDisconnect:
                logging.error("Attempted to write to a disconnected WebSocket.")
                logging.info("Scanning stopped")
                if client_id in scanner_status: del scanner_status[client_id]
                return
            except Exception as e:
                logging.error(f"Error while sending message: {e}")
                logging.info("Scanning stopped")
                if client_id in scanner_status: del scanner_status[client_id]
                return

    


# Process new tasks as they arrive
async def process_queue(async_queue: asyncio.Queue, i: int):
    dbconn = db.create_connection(Config.DB)
    while True:
        try:
            task = await async_queue.get()

            action = task["action"]

            if action == "done":
                break
            elif action == "scan":
                try:
                    scanner_status[task["client_id"]] = 'running'
                    await scan(dbconn, task["settings"], task["client_id"], clients[task["client_id"]]["websocket"])
                except Exception as e:
                    logging.error(f"Failed to scan: {e}")
            elif action == "scan_stop":
                print("SET status", task["client_id"])
                scanner_status[task["client_id"]] = 'stop'

        except Exception as e:
            logging.error(f"Error processing task: {e}")
            raise


def trigger_worker(task_queue, task):
    task_queue.put_nowait(task)


# Call this function when you want to stop the workers.
def stop_workers(task_queue, threads):
    for _ in threads:
        task_queue.put({"action": "done"})

    for t in threads:
        t.join()


def get_queue_wrapper():
    if "scanner" not in Worker.instances:
        Worker("scanner", int(Config.SCANNER_WORKERS), process_queue)
    return Worker.instances["scanner"].queue


def init():
    get_queue_wrapper()
