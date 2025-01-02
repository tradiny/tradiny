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
import asyncio
from starlette.websockets import WebSocketState
from datetime import datetime, timedelta, timezone

from config import Config

from .connection import conn
from .globals import (
    clients,
    periodic_tasks,
    providers,
    last_update,
    lock,
    historical_data_cache,
)

last_used_historical_cache = {}


def cleanup_websockets():
    # cleanup not connected websockets
    for _, c in clients.items():
        if c["websocket"].client_state != WebSocketState.CONNECTED:
            conn.disconnect(c["websocket"])


def get_subscriptions():
    subscriptions = []
    for _, c in clients.items():
        for s in c["subscriptions"]["data"]:
            subscriptions.append(s)
    subscriptions = list(set(subscriptions))

    if len(subscriptions) > 0:
        logging.info(f"All subscriptions: {subscriptions}")

    return subscriptions


def release_historical_cache(subscriptions):
    cleaned_keys = []
    with lock:
        cache_keys = list(historical_data_cache.keys())
        for key in cache_keys:
            if key in subscriptions:
                last_used_historical_cache[key] = datetime.now(timezone.utc)
            else:  # nobody is connected
                if key not in last_used_historical_cache:
                    last_used_historical_cache[key] = datetime.now(timezone.utc)
                else:
                    if (
                        datetime.now(timezone.utc)
                        - timedelta(
                            minutes=int(Config.RELEASE_HISTORICAL_CACHE_MINUTES)
                        )
                        > last_used_historical_cache[key]
                    ):
                        cleaned_keys.append(key)

                        del historical_data_cache[
                            key
                        ]  # remove cache, not used for some time

    if len(cleaned_keys) > 0:
        logging.info(f"Released cache: {cleaned_keys}")

    return cleaned_keys


def send_no_update_to_provider(subscriptions):

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


async def _periodic():
    cleanup_websockets()
    subscriptions = get_subscriptions()

    now = datetime.now(timezone.utc)
    release_historical_cache(subscriptions)

    send_no_update_to_provider(subscriptions)


def periodic():
    asyncio.create_task(_periodic())


def register_periodic_task(task):
    periodic_tasks.append(task)


async def periodic_task():
    periodic()


async def run_periodic_tasks():
    while True:
        for task in periodic_tasks:
            await task()
        await asyncio.sleep(60)
