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
from typing import List, Dict, Tuple

from fastapi import WebSocket
from starlette.websockets import WebSocketState, WebSocketDisconnect

from .globals import clients, providers


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
            if source in providers:
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


async def safe_send_message(websocket: WebSocket, message: str):
    try:
        await websocket.send_text(message)
    except WebSocketDisconnect:
        logging.error("Attempted to write to a disconnected WebSocket.")
    except Exception as e:
        logging.error(f"Error while sending message: {e}")


conn = ConnectionManager()
