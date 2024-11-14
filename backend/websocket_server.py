# This software is licensed under a dual license:
#
# 1. Creative Commons Attribution-NonCommercial (CC BY-NC)
#    for individuals and open source projects.
# 2. Commercial License for business use.
#
# For commercial inquiries, contact: license@tradiny.com
#
# For more details, refer to the LICENSE.md file in the root directory of this project.

import json
import threading
import asyncio
import db
import logging
import time
from config import Config

dbconn = db.create_connection(Config.DB)

import numpy as np
from db import indicators
from concurrent.futures import ThreadPoolExecutor
from queue import Empty, Queue
import pandas as pd
from datetime import datetime, timedelta, timezone
from collections import defaultdict

from starlette.websockets import WebSocket, WebSocketState
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Depends, APIRouter
from fastapi_utils.tasks import repeat_every
from fastapi.staticfiles import StaticFiles
from typing import List, Dict, Tuple

from utils import (
    determine_data_needs,
    get_last_n_items,
    filter_data,
    filter_df,
    get_lookback_period,
    get_current_date,
    resource_path,
)
from utils import register_request, is_request_allowed
from openai_gpt import query, query_reply

#
# GLOBALS
#

app = FastAPI()
websocket_router = APIRouter()

from vapid import get as get_vapid_public_key

historical_data_cache = {}
providers = {}
clients = {}
lock = threading.Lock()
futures = {}
last_update = {}
startup_actions = []
periodic_tasks = []


def generate_method_key(method_name, *args, **kwargs):
    # Convert positional arguments to strings
    args_str = "_".join(str(arg) for arg in args)

    # Convert keyword arguments to strings, sorted by key for consistency
    kwargs_str = "_".join(f"{key}={value}" for key, value in sorted(kwargs.items()))

    # Combine method name, args, and kwargs strings to form the method key
    if args_str and kwargs_str:
        method_key = f"{method_name}_{args_str}_{kwargs_str}"
    elif args_str:
        method_key = f"{method_name}_{args_str}"
    else:
        method_key = f"{method_name}_{kwargs_str}"

    return method_key


#
# PERIODIC
#


async def _periodic():
    # cleanup not connected websockets
    for _, c in clients.items():
        if c["websocket"].client_state != WebSocketState.CONNECTED:
            conn.disconnect(c["websocket"])

    subscriptions = []
    for _, c in clients.items():
        for s in c["subscriptions"]["data"]:
            subscriptions.append(s)
    subscriptions = list(set(subscriptions))

    if len(subscriptions) > 0:
        logging.info(f"All subscriptions: {subscriptions}")

    cleaned_keys = []
    with lock:
        cache_keys = list(historical_data_cache.keys())
        for key in cache_keys:
            if key not in subscriptions:
                cleaned_keys.append(key)

                del historical_data_cache[key]  # remove cache, not needed anymore

    if len(cleaned_keys) > 0:
        logging.info(f"Released cache: {cleaned_keys}")

    now = datetime.now(timezone.utc)
    for s in subscriptions:
        source, name, interval = s
        if s in last_update and last_update[s] < now - timedelta(seconds=60):
            last_update[s] = now

            providers[source].send_to(
                {
                    "action": "no_update",
                    "args": [name, interval],
                    "source": source,
                    "name": name,
                    "interval": interval,
                }
            )


def periodic():
    asyncio.create_task(_periodic())


#
# PROVIDER QUEUE HANDLING
#


async def receive_message(queue):
    loop = asyncio.get_running_loop()
    while True:
        try:
            message = await loop.run_in_executor(None, queue.get)

            if message["action"] == "write_message":
                for ws_client_key in message["ws_clients"]:
                    if ws_client_key in clients:
                        source = message["source"]
                        name = message["name"]
                        interval = message["interval"]

                        key = (source, name, interval)
                        last_update[key] = datetime.now(timezone.utc)

                        await safe_send_message(
                            clients[ws_client_key]["websocket"], *message["args"]
                        )

                        for indicator in clients[ws_client_key]["subscriptions"][
                            "indicators"
                        ]:
                            for key, d in indicator.get("dataMap").items():
                                if (
                                    d["source"] == source
                                    and d["name"] == name
                                    and d["interval"] == interval
                                ):

                                    m = await fetcher.fetch(
                                        send_indicator_data,
                                        (
                                            "indicator_update",
                                            indicator.get("id"),
                                            indicator.get("indicator"),
                                            indicator.get("inputs"),
                                            indicator.get("dataMap"),
                                            None,
                                            1,
                                        ),
                                    )
                                    await safe_send_message(
                                        clients[ws_client_key]["websocket"], m
                                    )

            elif message["action"] == "data_update_merge":
                for ws_client_key in message["ws_clients"]:
                    if ws_client_key in clients:
                        key = (message["source"], message["name"], message["interval"])
                        last_update[key] = datetime.now(timezone.utc)

                        cached_data = historical_data_cache.get(
                            cache_key,
                            {
                                "cached_df": pd.DataFrame(),
                                "last_fetched_time": datetime.now(timezone.utc),
                            },
                        )

                        last_datapoint_df = cached_data["cached_df"].iloc[-1]
                        last_datapoint = last_datapoint_df.to_dict()
                        last_datapoint["date"] = last_datapoint_df.name.strftime(
                            "%Y-%m-%d %H:%M:%S"
                        )

                        source = message["source"]
                        name = message["name"]
                        interval = message["name"]

                        if (
                            last_datapoint
                            and last_datapoint["date"] == message["data"]["date"]
                        ):
                            for key in message["data"].keys():
                                if (
                                    key.endswith("high")
                                    and message["data"][key] > last_datapoint[key]
                                ):
                                    last_datapoint[key] = message["data"][key]
                                if (
                                    key.endswith("low")
                                    and message["data"][key] < last_datapoint[key]
                                ):
                                    last_datapoint[key] = message["data"][key]
                                if key.endswith("close"):
                                    last_datapoint[key] = message["data"][key]
                                if key.endswith("volume"):
                                    last_datapoint[key] += message["data"][key]

                            await safe_send_message(
                                clients[ws_client_key]["websocket"],
                                json.dumps(
                                    {
                                        "type": "data_update",
                                        "source": source,
                                        "name": name,
                                        "interval": interval,
                                        "data": last_datapoint,
                                    }
                                ),
                            )
                        else:

                            await safe_send_message(
                                clients[ws_client_key]["websocket"],
                                json.dumps(
                                    {
                                        "type": "data_update",
                                        "source": source,
                                        "name": name,
                                        "interval": interval,
                                        "data": message["data"],
                                    }
                                ),
                            )

                        for indicator in clients[ws_client_key]["subscriptions"][
                            "indicators"
                        ]:
                            for key, d in indicator.get("dataMap").items():
                                if (
                                    d["source"] == source
                                    and d["name"] == name
                                    and d["interval"] == interval
                                ):

                                    m = await fetcher.fetch(
                                        send_indicator_data,
                                        (
                                            "indicator_update",
                                            indicator.get("id"),
                                            indicator.get("indicator"),
                                            indicator.get("inputs"),
                                            indicator.get("dataMap"),
                                            None,
                                            1,
                                        ),
                                    )
                                    await safe_send_message(
                                        clients[ws_client_key]["websocket"], m
                                    )

            elif message["action"] == "history":
                if message["ws_client"] in clients:
                    new_klines = message["new_klines"]
                    downloaded = len(new_klines)

                    cache_key = (
                        message["source"],
                        message["name"],
                        message["interval"],
                    )
                    cached_data = historical_data_cache.get(
                        cache_key,
                        {
                            "cached_df": pd.DataFrame(),
                            "last_fetched_time": datetime.now(timezone.utc),
                        },
                    )

                    with lock:
                        merge_data(
                            message["source"],
                            message["name"],
                            message["interval"],
                            cached_data,
                            new_klines,
                        )

                    cached_data = historical_data_cache.get(cache_key)

                    required_start_time = message["range"][0]
                    required_end_time = message["range"][1]

                    if message["end"] == "now UTC":
                        data_to_return = get_last_n_items(cached_data, message["count"])
                    else:
                        data_to_return = filter_data(
                            cached_data, required_start_time, required_end_time
                        )
                        logging.info(
                            f"historical data downloaded {downloaded} returned {len(data_to_return)}"
                        )

                    if message["ws_client"] in clients:
                        m = json.dumps(
                            {
                                "type": message["message_type"],
                                "source": message["source"],
                                "name": message["name"],
                                "interval": message["interval"],
                                "metadata": message["metadata"],
                                "data": data_to_return,
                            }
                        )
                        await safe_send_message(
                            clients[message["ws_client"]]["websocket"], m
                        )

            elif message["action"] == "update_in_cache":
                update_in_cache(*message["args"])

            else:
                logging.info(f"Unknown action: {message['action']}")

            if (
                "future_key" in message
                and message["future_key"] in futures
                and not futures[message["future_key"]].done()
            ):
                futures[message["future_key"]].set_result("Done!")

        except Exception as e:
            logging.error(f"Error in receive_message(): {e} {message}")
        except Empty:
            continue


def register_provider(provider):
    providers[provider.key] = provider

    asyncio.ensure_future(receive_message(provider.from_queue))


#
# BLOCKING FETCHER
#


class BlockingFetcher:
    def __init__(self):
        self.executor = ThreadPoolExecutor(max_workers=int(Config.INDICATOR_WORKERS))

    async def fetch(self, fn, args):
        loop = asyncio.get_running_loop()
        result = await loop.run_in_executor(
            self.executor, fn, *args  # The blocking function
        )
        return result


fetcher = BlockingFetcher()


#
# FASTAPI SERVER
#


# This class will encapsulate the alert queue

from alert import spawn_workers, trigger_worker, init_alerts


class AlertQueueWrapper:
    instance = None

    def __init__(self):
        if not AlertQueueWrapper.instance:
            AlertQueueWrapper.instance = self

            self.queue = spawn_workers(int(Config.ALERT_WORKERS))
            init_alerts(self.queue[0], dbconn)


def get_queue_wrapper() -> AlertQueueWrapper:
    if not AlertQueueWrapper.instance:
        AlertQueueWrapper()
    return AlertQueueWrapper.instance.queue


queue_wrapper = Depends(get_queue_wrapper)

# Immediately trigger the creation of the queue and workers when the application starts
get_queue_wrapper()


def register_startup_action(action):
    startup_actions.append(action)


def register_periodic_task(task):
    periodic_tasks.append(task)


async def periodic_task():
    periodic()


register_periodic_task(periodic_task)


async def run_periodic_tasks():
    while True:
        for task in periodic_tasks:
            await task()
        await asyncio.sleep(60)


@app.on_event("startup")
async def custom_startup():
    logging.info("Starting up...")
    # Execute all registered startup actions
    for action in startup_actions:
        await action()
    # Start periodic tasks
    app.state.periodic_task_runner = asyncio.create_task(run_periodic_tasks())


@app.on_event("shutdown")
async def custom_shutdown():
    logging.info("Shutting down...")
    # Cancel periodic tasks on shutdown
    app.state.periodic_task_runner.cancel()
    await app.state.periodic_task_runner


class ConnectionManager:

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        clients[id(websocket)] = {
            "websocket": websocket,
            "subscriptions": {"data": [], "indicators": []},
        }

    def disconnect(self, websocket: WebSocket):
        subscriptions = self.get_data_subscriptions(websocket)
        for source, name, interval in subscriptions:
            providers[source].send_to(
                {"action": "on_close", "args": (id(websocket), name, interval)}
            )

        clients.pop(id(websocket), None)

    async def send_message(self, websocket: WebSocket, message: str):
        if websocket.client_state == WebSocketState.CONNECTED:
            await websocket.send_text(message)

    def add_data_subscription(self, websocket: WebSocket, subscription: Tuple):
        if id(websocket) in clients:
            clients[id(websocket)]["subscriptions"]["data"].append(subscription)

    def get_data_subscriptions(self, websocket: WebSocket) -> List[Tuple]:
        return clients.get(id(websocket), {"subscriptions": {"data": []}})[
            "subscriptions"
        ]["data"]

    def add_indicator_subscription(self, websocket: WebSocket, subscription: dict):
        if id(websocket) in clients:
            clients[id(websocket)]["subscriptions"]["indicators"].append(subscription)


conn = ConnectionManager()
ip_conns = {}
last_alert_created = datetime.now(timezone.utc).strftime("%Y-%m-%d")
ip_alerts = {}
ip_requests = defaultdict(list)
data_requests = defaultdict(list)


@websocket_router.websocket("/websocket/")
async def websocket_endpoint(
    websocket: WebSocket, alert_queue=Depends(get_queue_wrapper)
):
    await conn.connect(websocket)

    client_ip = websocket.client.host

    if not is_request_allowed(
        Config.MAX_REQUESTS_PER_IP_PER_HOUR, ip_requests, client_ip
    ):
        logging.warning(f"Too many requests: {client_ip}")
        await safe_send_message(
            websocket,
            json.dumps({"type": "notification", "message": "Error: Too many requests"}),
        )
        conn.disconnect(websocket)
        return

    if client_ip not in Config.WHITELIST_IP:
        register_request(ip_requests, client_ip)

    if client_ip in ip_conns and ip_conns[client_ip] >= int(
        Config.MAX_SIMULTANEOUS_CONNECTIONS_PER_IP
    ):
        logging.warning(f"Max simultaneous connections reached: {client_ip}")
        await safe_send_message(
            websocket,
            json.dumps(
                {
                    "type": "notification",
                    "message": "Error: Max simultaneous connections reached",
                }
            ),
        )
        conn.disconnect(websocket)
        return

    if client_ip not in Config.WHITELIST_IP:
        if not client_ip in ip_conns:
            ip_conns[client_ip] = 0
        ip_conns[client_ip] += 1
        logging.info(f"{client_ip} connected {ip_conns[client_ip]}x")

    try:
        while True:
            data = json.loads(await websocket.receive_text())
            await handle_message(websocket, data, alert_queue)
    except WebSocketDisconnect:
        pass
    except Exception as e:
        raise e
        logging.error(f"WebSocket error: {e}")
    finally:
        if client_ip in ip_conns:
            ip_conns[client_ip] -= 1

        conn.disconnect(websocket)


app.include_router(websocket_router)

app.mount("/", StaticFiles(directory=resource_path("dist"), html=True), name="static")


async def handle_message(websocket: WebSocket, data: dict, alert_queue: Queue):
    handle_first = ["data"]
    tasks = []

    # Handle 'data' type messages first
    for d in [d for d in data if d.get("type") in handle_first]:
        task = asyncio.create_task(process_message(websocket, d, alert_queue))
        tasks.append(task)

    # Await all 'data' type message handling tasks
    await asyncio.gather(*tasks, return_exceptions=True)

    # Handle all other types of messages
    for d in [d for d in data if d.get("type") not in handle_first]:
        task = asyncio.create_task(process_message(websocket, d, alert_queue))
        await task


async def process_message(websocket: WebSocket, d: dict, alert_queue: Queue):
    global data_requests
    global last_alert_created
    global ip_alerts

    def send_message_in_parts(websocket):
        async def _(chunk):
            if chunk:
                await safe_send_message(
                    websocket,
                    json.dumps({"type": "prompt_response", "response": chunk}),
                )
                logging.debug(f"Sent chunk: {chunk}")

        return _

    if d.get("type") in ["data", "data_history", "indicator", "indicator_history"]:
        client_ip = websocket.client.host

        if not is_request_allowed(
            Config.MAX_DATA_REQUESTS_PER_IP_PER_HOUR, data_requests, client_ip
        ):
            logging.warning(f"Too many data requests: {client_ip}")
            await safe_send_message(
                websocket,
                json.dumps(
                    {"type": "notification", "message": "Error: Too many data requests"}
                ),
            )
            return

        if client_ip not in Config.WHITELIST_IP:
            register_request(data_requests, client_ip)

    try:
        if d.get("type") == "search_data":
            results = db.search_data_entities(dbconn, d.get("search"), type="data")
            await safe_send_message(
                websocket, json.dumps({"type": "search_data_done", "results": results})
            )

        elif d.get("type") == "search_indicators":
            results = db.search_data_entities(dbconn, d.get("search"), type="indicator")
            await safe_send_message(
                websocket,
                json.dumps({"type": "search_indicators_done", "results": results}),
            )

        elif d.get("type") == "data":

            key = (d.get("source"), d.get("name"), d.get("interval"))
            if key not in conn.get_data_subscriptions(websocket):
                conn.add_data_subscription(websocket, key)

            metadata = db.get_metadata(dbconn, d.get("source"), d.get("name"))

            await send_historical_data(
                websocket,
                d.get("source"),
                d.get("name"),
                d.get("interval"),
                d.get("count", 300),
                metadata=metadata,
            )

            providers[d.get("source")].send_to(
                {
                    "action": "start_streaming",
                    "args": (id(websocket), d.get("name"), d.get("interval")),
                }
            )

        elif (
            d.get("type") == "data_history"
            and d.get("name")
            and d.get("interval")
            and d.get("end")
        ):
            await send_historical_data(
                websocket,
                d.get("source"),
                d.get("name"),
                d.get("interval"),
                d.get("count"),
                d.get("end"),
            )

        elif d.get("type") == "indicator" or d.get("type") == "indicator_history":

            if d.get("type") == "indicator":
                message_type = "indicator_init"
                conn.add_indicator_subscription(websocket, d)

            else:
                message_type = "indicator_history"

            m = await fetcher.fetch(
                send_indicator_data,
                (
                    message_type,
                    d.get("id"),
                    d.get("indicator"),
                    d.get("inputs"),
                    d.get("dataMap"),
                    d.get("range", None),
                    d.get("count", 300),
                ),
            )
            await safe_send_message(websocket, m)

        elif d.get("type") == "alert":

            if datetime.now(timezone.utc).strftime("%Y-%m-%d") != last_alert_created:
                ip_alerts = {}  # reset each day
                last_alert_created = datetime.now(timezone.utc).strftime(
                    "%Y-%m-%d"
                )  # update

            client_ip = websocket.client.host

            if client_ip in ip_alerts and ip_alerts[client_ip] >= int(
                Config.MAX_ALERTS_PER_IP_PER_DAY
            ):
                logging.warning(f"Max alerts reached: {client_ip}")
                await safe_send_message(
                    websocket,
                    json.dumps(
                        {"type": "notification", "message": "Error: Max alerts reached"}
                    ),
                )
                return

            if client_ip not in Config.WHITELIST_IP:
                if client_ip not in ip_alerts:
                    ip_alerts[client_ip] = 0
                ip_alerts[client_ip] += 1

            if client_ip in ip_alerts:
                logging.info(f"{client_ip} number of alerts: {ip_alerts[client_ip]}")

            trigger_worker(alert_queue[0], {"action": "new_alert", "settings": d})

        elif d.get("type") == "vapid_public_key":
            await safe_send_message(
                websocket,
                json.dumps(
                    {
                        "type": "vapid_public_key",
                        "vapid_public_key": get_vapid_public_key(),
                    }
                ),
            )

        elif d.get("type") == "prompt":

            client_ip = websocket.client.host
            conversation_id = d.get("conversation_id")
            description = d.get("description")
            prompt = d.get("prompt")
            img = d.get("img")

            response = await query(
                client_ip,
                conversation_id,
                f"""
                You are a data analyst specializing in technical analysis, interpreting market data to identify trends and make decisions based on chart patterns, indicators, and statistical metrics.
                Your task is to analyze the provided chart.
                The provided chart includes:
                {description}
                """,
                f"""{prompt}""",
                img,
                model="gpt-4-turbo",
                max_tokens=1000,
                on_chunk=send_message_in_parts(websocket),
            )

        elif d.get("type") == "prompt_reply":

            client_ip = websocket.client.host
            conversation_id = d.get("conversation_id")
            prompt = d.get("prompt")
            response = await query_reply(
                client_ip,
                conversation_id,
                f"""{prompt}""",
                model="gpt-4-turbo",
                max_tokens=1000,
                on_chunk=send_message_in_parts(websocket),
            )

    except asyncio.CancelledError:
        logging.error("Task was cancelled")


async def send_historical_data(
    websocket: WebSocket,
    source,
    name,
    interval,
    count=300,
    end="now UTC",
    metadata=None,
):
    key = generate_method_key(
        "send_historical_data", source, name, interval, count=300, end="now UTC"
    )
    futures[key] = asyncio.Future()

    count = count if count > 300 else 300
    # count += 300 # for indicators

    logging.info(f"requested {count} data points till {end}")
    message_type = "data_history" if end != "now UTC" else "data_init"

    if end != "now UTC":
        end_dt = datetime.strptime(end, "%Y-%m-%d %H:%M:%S").replace(
            tzinfo=timezone.utc
        )
    else:
        end_dt = datetime.now(timezone.utc)

    cache_key = (source, name, interval)
    cached_data = historical_data_cache.get(
        cache_key,
        {"cached_df": pd.DataFrame(), "last_fetched_time": datetime.now(timezone.utc)},
    )

    current_date = get_current_date(interval)
    request_recent_data_and_has_last_date = (
        end == "now UTC"
        and not cached_data["cached_df"].empty
        and len(cached_data["cached_df"]) > 0
        and current_date
        == cached_data["cached_df"].index[-1].strftime("%Y-%m-%d %H:%M:%S")
    )

    required_start_time = get_lookback_period(interval, end_dt, count)
    required_end_time = end_dt

    start_needed, end_needed = determine_data_needs(
        cached_data, required_start_time, required_end_time
    )

    if not request_recent_data_and_has_last_date and (start_needed or end_needed):
        date_format = "%Y-%m-%d %H:%M:%S"  # "%d %b %Y %H:%M:%S"
        start_time_query = (
            start_needed.strftime(date_format)
            if start_needed or cached_data["cached_df"].empty
            else cached_data["cached_df"].index[-1].strftime(date_format)
        )
        # Update only the last candle if end_needed and we have cached data covering up to the latest full candle
        if end_needed and not cached_data["cached_df"].empty:
            last_cached_time = cached_data["cached_df"].index[-1]
            start_time_query = last_cached_time.strftime(date_format)
        end_time_query = (
            end_dt.strftime(date_format)
            if end_needed
            else required_end_time.strftime(date_format)
        )

        if end == "now UTC":
            end_time_query = end

        providers[source].send_to(
            {
                "action": "get_history",
                "args": (name, interval, start_time_query, end_time_query, count),
                "source": source,
                "name": name,
                "interval": interval,
                "metadata": metadata,
                "count": count,
                "end": end,
                "message_type": message_type,
                "ws_client": id(websocket),
                "range": [required_start_time, required_end_time],
                "future_key": key,
            }
        )

        if key in futures:
            await futures[key]
            del futures[key]

    else:
        downloaded = 0
        logging.debug("hit the cache")
        if end == "now UTC":
            data_to_return = get_last_n_items(cached_data, count)
        else:
            data_to_return = filter_data(
                cached_data, required_start_time, required_end_time
            )
            logging.info(
                f"historical data downloaded {downloaded} returned {len(data_to_return)}"
            )

        await safe_send_message(
            websocket,
            json.dumps(
                {
                    "type": message_type,
                    "source": source,
                    "name": name,
                    "interval": interval,
                    "data": data_to_return,
                    "metadata": metadata,
                }
            ),
        )

        if key in futures:
            if not futures[key].done():
                futures[key].set_result("Done!")
            del futures[key]


def send_indicator_data(
    message_type, id, indicator, inputs, data_map, range=None, count=600
):

    length = 0
    if "length" in inputs:
        length = int(inputs["length"])
    if (
        count == 1 and length == 0
    ):  # case when there is no length, we need to calculate from the whole dataset
        count = 300

    df = pd.DataFrame()
    for output, datasource in data_map.items():
        source = datasource["source"]
        name = datasource["name"]
        interval = datasource["interval"]
        column = datasource["value"]
        cache_key = (source, name, interval)
        cached_data = historical_data_cache.get(cache_key, None)
        if cached_data is None:
            return json.dumps({"type": "no_data", "id": id})

        if range:
            f = datetime.strptime(range[0], "%Y-%m-%d %H:%M:%S")
            t = (
                cached_data["cached_df"].index[-1].to_pydatetime()
            )  # datetime.strptime(range[1], "%Y-%m-%d %H:%M:%S")

            # abs_difference = np.abs(cached_data['cached_df'].index.to_pydatetime() - f)
            # index_from = np.argmin(abs_difference)
            # index_from -= (length * 2)
            # if index_from < 0: index_from = 0
            index_from = 0

            abs_difference = np.abs(cached_data["cached_df"].index.to_pydatetime() - t)
            index_to = np.argmin(abs_difference)

            idf = cached_data["cached_df"].iloc[index_from : index_to + 1]
            idf = pd.DataFrame(
                [[index, float(row[column])] for index, row in idf.iterrows()]
            )

        elif count:
            # idf = pd.DataFrame(
            #     [[index, float(row[column])] for index, row in cached_data['cached_df'].tail(count + (length*2)).iterrows()]
            # )
            idf = pd.DataFrame(
                [
                    [index, float(row[column])]
                    for index, row in cached_data["cached_df"].iterrows()
                ]
            )
        else:
            logging.error(f"Error: range nor count found in your request")
            continue
        idf.columns = ["Date", column]
        if df.empty:
            df = idf
        else:
            df = pd.merge(df, idf, on=["Date"], how="inner")

    if df.empty:
        logging.error("Error: No data?")
        return

    df["Date"] = df["Date"].dt.strftime("%Y-%m-%d %H:%M:%S")

    cls = indicators[indicator["id"]]["klass"]
    obj = cls()

    try:
        outputs = obj.calc(df.values, **inputs)
    except Exception as e:
        logging.error(f"Error calculating indicator: {e}")
        return

    df = pd.DataFrame()
    for i, output in enumerate(outputs):
        idf = pd.DataFrame(output)
        idf.columns = ["date", f"{id}-{obj.outputs[i]['name']}"]
        if df.empty:
            df = idf
        else:
            df = pd.merge(df, idf, on=["date"], how="inner")

    df = df.replace({np.nan: None, np.inf: None, -np.inf: None})
    # df = df.dropna()

    if message_type == "indicator_update":
        if len(df) == 0:  # no update
            data = {}
        else:
            data = df.to_dict(orient="records")[-1]
        return json.dumps({"type": message_type, "id": id, "data": data})

    else:
        X = 0
        if "length" in inputs:
            X = int(inputs["length"])
        Y = 0  # select from the end

        if range:
            df.date = pd.to_datetime(df.date)
            df = df.set_index("date")
            df = filter_df(
                df, range[0], datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
            )  # range[1]
        else:
            # count
            Y = count

        if len(df) == 0:  # no update
            data = []
        else:
            # df_sorted = df.sort_values(by='date').reset_index(drop=True)
            data = df.to_dict(orient="records")[X:][-Y:]

        return json.dumps({"type": message_type, "id": id, "data": data})


async def safe_send_message(websocket: WebSocket, message: str):
    try:
        await websocket.send_text(message)
    except WebSocketDisconnect:
        logging.error("Attempted to write to a disconnected WebSocket.")
    except Exception as e:
        logging.error(f"Error while sending message: {e}")


def update_in_cache(source, name, interval, data):
    cache_key = (source, name, interval)
    cached_data = historical_data_cache.get(cache_key, None)
    if cached_data:
        with lock:
            merge_data(source, name, interval, cached_data, data)


def merge_data(source, name, interval, cached_data, new_klines):
    if len(new_klines) == 0:
        return  # nothing to update

    new_df = pd.DataFrame(new_klines)
    new_df.columns = list(new_klines[0].keys())
    new_df.date = pd.to_datetime(new_df.date)
    new_df = new_df.set_index("date")

    # Load cached data into a DataFrame, or create an empty DataFrame if cached_df is not present
    if "cached_df" not in cached_data or cached_data["cached_df"].empty:
        cached_df = pd.DataFrame()
    else:
        cached_df = cached_data["cached_df"]

    # Single kline update check
    if len(new_klines) == 1:
        if not cached_df.empty and cached_df.index[-1] == new_df.index[-1]:
            cached_df.iloc[-1] = new_df.iloc[-1]
            cached_data["cached_df"] = cached_df
            return

    # Concatenate cached_df and new_df and then drop duplicates, keeping the latest entry
    merged_df = pd.concat([cached_df, new_df])
    merged_df = merged_df[~merged_df.index.duplicated(keep="last")]
    merged_df.sort_index(inplace=True)

    # Update the cached data with the merged DataFrame

    cache_key = (source, name, interval)
    if cache_key not in historical_data_cache:
        historical_data_cache[cache_key] = {
            "cached_df": pd.DataFrame(),
            "last_fetched_time": datetime.now(timezone.utc),
        }
    historical_data_cache[cache_key]["cached_df"] = merged_df
