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

from app.globals import clients
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
            new_key = (
                key.replace(target_value, replacement_value)
                if isinstance(key, str)
                else key
            )
            if isinstance(value, str):
                result[new_key] = re.sub(
                    re.escape(target_value), replacement_value, value
                )
            else:
                result[new_key] = replace_all_in_obj(
                    value, target_value, replacement_value, visited
                )
    elif isinstance(obj, Sequence):
        for item in obj:
            result.append(
                replace_all_in_obj(item, target_value, replacement_value, visited)
            )

    return result


async def scan(dbconn, d, client_id, websocket):
    """
    Iterates over data entries from the database, alters the source and name
    in the existing configuration to fetch data, and evaluates it against the
    provided rules. Sends messages with progress and results to the websocket.

    Args:
        dbconn: A connection object to the database.
        d: The entire configuration object.
        client_id: The client ID, used as the websocket ID.
        websocket: The websocket connection to send messages.
    """

    source_replace = None
    name_replace = None
    interval = None
    for data in d["dataProviderConfig"]["data"]:
        if data["type"] == "data":
            source_replace = data["source"]
            name_replace = data["name"]
            interval = data["interval"]

    data_entries = search_data_entities(
        dbconn, d.get("search"), type="data", limit=10**6
    )
    z = len(str(len(data_entries)))

    for i, db_entry in enumerate(data_entries):

        source = db_entry["details"]["source"]
        name = db_entry["details"]["name"]

        if "name_label" in db_entry["details"]:
            name_label = db_entry["details"]["name_label"]
        else:
            name_label = name

        try:
            await websocket.send_text(
                json.dumps(
                    {
                        "type": "scan_progress",
                        "message": f"Scanning {i+1:0{z}}/{len(data_entries)}",
                    }
                )
            )
        except WebSocketDisconnect:
            logging.error("Attempted to write to a disconnected WebSocket.")
            logging.info("Scanning stopped because the client is gone")
            if client_id in scanner_status:
                del scanner_status[client_id]
            return
        except Exception as e:
            logging.error(f"Error while sending message: {e}")
            logging.info(
                "Scanning stopped because could not send message to the client"
            )
            if client_id in scanner_status:
                del scanner_status[client_id]
            return

        di = copy.deepcopy(d)
        if source_replace is not None and source != source_replace:
            di = replace_all_in_obj(di, source_replace, source)
        if name_replace is not None and name != name_replace:
            di = replace_all_in_obj(di, name_replace, name)

        data_request = di["dataProviderConfig"]["data"]
        for dr in data_request:
            dr["stream"] = False  # disable streaming new data
        expected_init_messages = len(data_request)
        actual_init_messages = 0
        errors = []
        timeout = 15

        lastDataPoint = {}

        if expected_init_messages > 0:
            url = d["dataProviderConfig"]["full_url"]

            try:
                async with websockets.connect(url) as ws:

                    async def receive_data():
                        nonlocal actual_init_messages, errors

                        await ws.send(json.dumps(data_request))
                        async for message in ws:
                            message = json.loads(message)

                            if message["type"] == "data_init":
                                if len(message["data"]) == 0:
                                    errors.append("not enough data")
                                else:
                                    lastDataPoint.update(message["data"][-1])
                                actual_init_messages += 1
                                # logging.info(f"Received {message['type']} for {message['source']}, {message['name']}, {message['interval']}")
                            elif message["type"] == "no_data":
                                # logging.info(f"Received {message['type']} for {message}")
                                break
                            elif message["type"] == "indicator_init":
                                if len(message["data"]) == 0:
                                    errors.append("not enough data")
                                else:
                                    lastDataPoint.update(message["data"][-1])
                                actual_init_messages += 1
                                # logging.info(f"Received {message['type']} for {message['id']}")
                            # else:
                            #     logging.info(f"Received {message['type']}")

                            if actual_init_messages == expected_init_messages:
                                break

                    try:
                        await asyncio.wait_for(receive_data(), timeout)
                        # logging.info(f"Got data: {lastDataPoint}")
                    except asyncio.TimeoutError:
                        errors.append(
                            f"Timeout reached: did not receive all {expected_init_messages} expected messages in {timeout} seconds."
                        )

            except Exception as e:
                errors.append(f"Error: {e}")

        if len(errors):
            logging.info(
                f"While scanning {name_label} skipped because {' and '.join(errors)}"
            )
            continue

        rules = di["rules"]
        operators = di["operators"]
        indicators = di["indicators"]

        result, data_values = rules_evaluate(
            rules, operators, indicators, lastDataPoint
        )

        if result:
            try:
                await websocket.send_text(
                    json.dumps(
                        {
                            "type": "scan_result",
                            "data": db_entry,
                            "data_values": data_values,
                        }
                    )
                )
            except WebSocketDisconnect:
                logging.error("Attempted to write to a disconnected WebSocket.")
                logging.info("Scanning stopped because the client is gone")
                if client_id in scanner_status:
                    del scanner_status[client_id]
                return
            except Exception as e:
                logging.error(f"Error while sending message: {e}")
                logging.info(
                    "Scanning stopped because could not send message to the client"
                )
                if client_id in scanner_status:
                    del scanner_status[client_id]
                return

        if scanner_status[client_id] == "stop":
            logging.info(
                f"Scanner for {client_id} stopped because stop signal was received."
            )
            if client_id in scanner_status:
                del scanner_status[client_id]
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
                    scanner_status[task["client_id"]] = "running"
                    await scan(
                        dbconn,
                        task["settings"],
                        task["client_id"],
                        clients[task["client_id"]]["websocket"],
                    )
                except Exception as e:
                    logging.error(f"Failed to scan: {e}")
            elif action == "scan_stop":
                if (
                    task["client_id"] in scanner_status
                    and scanner_status[task["client_id"]] == "running"
                ):
                    scanner_status[task["client_id"]] = "stop"

        except Exception as e:
            logging.error(f"Error processing task: {e}")


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
