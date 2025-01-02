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

import logging
import json
import asyncio
from queue import Queue
from datetime import datetime, timedelta, timezone
from collections import defaultdict
from fastapi import APIRouter
from fastapi import Depends
from fastapi import WebSocket
from fastapi import WebSocketDisconnect

from db import search_data_entities, get_metadata
from config import Config
from openai_gpt import query, query_reply
from alert import (
    get_queue_wrapper as get_alert_queue_wrapper,
    trigger_worker as trigger_alert_worker,
)
from vapid import get as get_vapid_public_key

from .connection import safe_send_message

from .connection import conn
from .globals import dbconn, providers, indicator_fetcher
from .handlers import send_historical_data, send_indicator_data
from scanner import (
    get_queue_wrapper as get_scanner_queue_wrapper,
    trigger_worker as trigger_scanner_worker,
)

from utils import register_request, is_request_allowed

websocket_router = APIRouter()

ip_conns = {}
last_alert_created = datetime.now(timezone.utc).strftime("%Y-%m-%d")
ip_alerts = {}
ip_requests = defaultdict(list)
data_requests = defaultdict(list)


@websocket_router.websocket("/websocket/")
async def websocket_endpoint(
    websocket: WebSocket,
    alert_queue=Depends(get_alert_queue_wrapper),
    scanner_queue=Depends(get_scanner_queue_wrapper),
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
            text = await websocket.receive_text()
            data = json.loads(text)
            await handle_message(websocket, data, alert_queue, scanner_queue)
    except WebSocketDisconnect:
        pass
    except Exception as e:
        raise e
        logging.error(f"WebSocket error: {e}")
    finally:
        if client_ip in ip_conns:
            ip_conns[client_ip] -= 1

        conn.disconnect(websocket)


async def handle_message(
    websocket: WebSocket, data: dict, alert_queue: Queue, scanner_queue: Queue
):
    handle_first = ["data"]
    tasks = []

    # Handle 'data' type messages first
    for d in [d for d in data if d.get("type") in handle_first]:
        task = asyncio.create_task(
            process_message(websocket, d, alert_queue, scanner_queue)
        )
        tasks.append(task)

    # Await all 'data' type message handling tasks
    await asyncio.gather(*tasks, return_exceptions=True)

    # Handle all other types of messages
    for d in [d for d in data if d.get("type") not in handle_first]:
        task = asyncio.create_task(
            process_message(websocket, d, alert_queue, scanner_queue)
        )
        await task


async def process_message(
    websocket: WebSocket, d: dict, alert_queue: Queue, scanner_queue: Queue
):
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
            results = search_data_entities(dbconn, d.get("search"), type="data")
            await safe_send_message(
                websocket, json.dumps({"type": "search_data_done", "results": results})
            )

        elif d.get("type") == "search_indicators":
            results = search_data_entities(dbconn, d.get("search"), type="indicator")
            await safe_send_message(
                websocket,
                json.dumps({"type": "search_indicators_done", "results": results}),
            )

        elif d.get("type") == "data":

            stream = d.get("stream", True)

            if stream:
                key = (d.get("source"), d.get("name"), d.get("interval"))
                if key not in conn.get_data_subscriptions(websocket):
                    conn.add_data_subscription(websocket, key)

            metadata = get_metadata(dbconn, d.get("source"), d.get("name"))

            await send_historical_data(
                websocket,
                d.get("source"),
                d.get("name"),
                d.get("interval"),
                d.get("count", 300),
                metadata=metadata,
            )

            if stream:
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

            stream = d.get("stream", True)

            if d.get("type") == "indicator":
                message_type = "indicator_init"
                if stream:
                    conn.add_indicator_subscription(websocket, d)

            else:
                message_type = "indicator_history"

            m = await indicator_fetcher.fetch(
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

            task = {"action": "new_alert", "settings": d}
            logging.info(f"Adding task {task['action']} to {alert_queue[0]}")
            trigger_alert_worker(alert_queue[0], task)

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

        elif d.get("type") == "scan":

            task = {"action": "scan", "settings": d, "client_id": id(websocket)}
            logging.info(f"Adding task {task['action']} to {scanner_queue[0]}")
            trigger_scanner_worker(scanner_queue[0], task)

        elif d.get("type") == "scan_stop":

            task = {"action": "scan_stop", "client_id": id(websocket)}
            logging.info(f"Adding task {task['action']} to {scanner_queue[0]}")
            trigger_scanner_worker(scanner_queue[0], task)

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
