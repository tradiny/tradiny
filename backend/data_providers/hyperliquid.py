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

from datetime import datetime, timedelta, timezone
import logging
import threading
import json
import time
import httpx
import websocket

from config import Config
from provider import Provider


class HyperliquidProvider(Provider):
    key = "Hyperliquid"
    type = "candlestick"
    client = None
    lock = threading.Lock()
    ws_clients = {}  # Maps (symbol, interval) to list of clients
    streams = {}  # Maps (symbol, interval) to stream
    streams_started_at = {}
    streams_stopped_at = {}
    streams_scheduled = {}

    # Hyperliquid API endpoints
    BASE_URL = "https://api.hyperliquid.xyz"
    REST_URL = f"{BASE_URL}"
    WS_URL = "wss://api.hyperliquid.xyz/ws"

    # Interval map
    interval_map = {
        "1m": "1m",
        "3m": "3m",
        "5m": "5m",
        "15m": "15m",
        "30m": "30m",
        "1h": "1h",
        "2h": "2h",
        "4h": "4h",
        "8h": "8h",
        "12h": "12h",
        "1d": "1d",
        "3d": "3d",
        "1w": "1w",
        "1M": "1M",
    }

    def init(self):
        """Initialize the Hyperliquid client."""
        HyperliquidProvider.client = httpx.Client(
            base_url=self.REST_URL,
            headers={
                "Content-Type": "application/json",
                "User-Agent": "tradiny-bot/1.0",
            },
        )

    def get_dataset(self):
        """Get all available assets from Hyperliquid."""
        self.init()

        symbols = []
        try:
            # Get all assets
            response = self._fetch_all_assets()

            if response and "universe" in response:
                for asset in response["universe"]:
                    symbol = asset["name"]

                    # Create name label from base and quote assets
                    name_label = f"{symbol}"

                    symbols.append(
                        {
                            "source": HyperliquidProvider.key,
                            "name": symbol,
                            "name_label": name_label,
                            "type": HyperliquidProvider.type,
                            "categories": ["Crypto"],
                            "intervals": [
                                "1m",
                                "3m",
                                "5m",
                                "15m",
                                "30m",
                                "1h",
                                "2h",
                                "4h",
                                "8h",
                                "12h",
                                "1d",
                                "3d",
                                "1w",
                                "1M",
                            ],
                            "outputs": [
                                {"name": "open", "y_axis": "price"},
                                {"name": "high", "y_axis": "price"},
                                {"name": "low", "y_axis": "price"},
                                {"name": "close", "y_axis": "price"},
                                {"name": "volume", "y_axis": "volume"},
                            ],
                        }
                    )
        except Exception as e:
            logging.error(f"Error fetching Hyperliquid assets: {e}")

        return symbols

    def _fetch_all_assets(self):
        """Fetch all assets from Hyperliquid API."""
        try:
            response = HyperliquidProvider.client.post("/info", json={"type": "meta"})
            return response.json()
        except Exception as e:
            logging.error(f"Error fetching assets: {e}")
            return None

    def schedule_message(self, delay, message):
        """Schedule a message to be sent after a delay."""

        def delayed_execution():
            time.sleep(delay)
            self.respond(message)

        thread = threading.Thread(target=delayed_execution)
        thread.start()

    def start_streaming(self, ws_client, symbol, interval):
        """Start streaming data for a symbol and interval."""

        if (symbol, interval) in HyperliquidProvider.streams_stopped_at:
            # Hyperliquid implementation needs recovery time
            diff = (
                datetime.now(timezone.utc)
                - HyperliquidProvider.streams_stopped_at[(symbol, interval)]
            )
            seconds = 5
            if diff <= timedelta(seconds=seconds):
                if (symbol, interval) not in HyperliquidProvider.streams_scheduled:
                    HyperliquidProvider.streams_scheduled[(symbol, interval)] = True
                    return self.schedule_message(
                        seconds - diff.total_seconds(),
                        {
                            "action": "start_streaming",
                            "args": (ws_client, symbol, interval),
                        },
                    )
                else:
                    return

        if (symbol, interval) in HyperliquidProvider.streams_stopped_at:
            del HyperliquidProvider.streams_stopped_at[(symbol, interval)]

        start = False
        with HyperliquidProvider.lock:
            if (symbol, interval) not in HyperliquidProvider.ws_clients:
                HyperliquidProvider.ws_clients[(symbol, interval)] = []
            if ws_client not in HyperliquidProvider.ws_clients[(symbol, interval)]:
                if ws_client is not None:
                    HyperliquidProvider.ws_clients[(symbol, interval)].append(ws_client)
                start = True

        if start:
            self._start_hyperliquid_stream(symbol, interval)

    def format_datapoint(self, symbol, interval, k):
        """Format a single datapoint."""
        # Handle both timestamp formats (seconds and milliseconds)
        timestamp = k[0]
        if timestamp < 1000000000000:  # If timestamp is in seconds
            timestamp = timestamp * 1000

        date_str = datetime.fromtimestamp(timestamp / 1000, timezone.utc).strftime(
            "%Y-%m-%d %H:%M:%S"
        )
        return {
            "date": date_str,
            f"{HyperliquidProvider.key}-{symbol}-{interval}-open": k[1],
            f"{HyperliquidProvider.key}-{symbol}-{interval}-high": k[2],
            f"{HyperliquidProvider.key}-{symbol}-{interval}-low": k[3],
            f"{HyperliquidProvider.key}-{symbol}-{interval}-close": k[4],
            f"{HyperliquidProvider.key}-{symbol}-{interval}-volume": k[5],
        }

    def no_update(self, symbol, interval):
        """Handle no update scenario."""
        logging.info(f"No update for {symbol} {interval}, restarting...")

        if (symbol, interval) in HyperliquidProvider.streams:
            stream = HyperliquidProvider.streams[(symbol, interval)]
            del HyperliquidProvider.streams[(symbol, interval)]

            HyperliquidProvider.streams_stopped_at[(symbol, interval)] = datetime.now(
                timezone.utc
            )

        self.start_streaming(None, symbol, interval)

    def _start_hyperliquid_stream(self, symbol, interval):
        """Start Hyperliquid WebSocket stream."""

        try:
            # Convert interval to Hyperliquid format
            hl_interval = HyperliquidProvider.interval_map.get(interval, "1h")

            # Use websocket-client library
            def on_message(ws, message):
                try:
                    msg = json.loads(message)

                    # Handle subscription confirmation
                    if msg.get("type") == "subscription":
                        logging.info(f"Subscribed to {symbol} {interval}")
                        return

                    # Handle candle data
                    if (
                        msg.get("channel") == "candle"
                        and msg.get("data", {}).get("s") == symbol
                    ):
                        data = msg.get("data", {})
                        if data and all(
                            key in data for key in ["o", "h", "l", "c", "v"]
                        ):
                            # Candle format from Hyperliquid: timestamp in ms, open, high, low, close, volume
                            k = [
                                data.get("t", 0),  # timestamp start in ms
                                float(data.get("o", 0)),  # open
                                float(data.get("h", 0)),  # high
                                float(data.get("l", 0)),  # low
                                float(data.get("c", 0)),  # close
                                float(data.get("v", 0)),  # volume
                            ]

                            # Convert to the format expected by format_datapoint
                            # format_datapoint expects [timestamp_ms, open, high, low, close, volume]
                            formatted_k = [
                                k[0],  # timestamp already in ms
                                k[1],
                                k[2],
                                k[3],
                                k[4],
                                k[5],
                            ]

                            data_point = self.format_datapoint(
                                symbol, interval, formatted_k
                            )

                            self.respond(
                                {
                                    "action": "update_in_cache",
                                    "args": (
                                        HyperliquidProvider.key,
                                        symbol,
                                        interval,
                                        [data_point],
                                    ),
                                }
                            )

                            ws_clients = HyperliquidProvider.ws_clients.get(
                                (symbol, interval), []
                            )

                            if len(ws_clients) > 0:
                                self.respond(
                                    {
                                        "action": "write_message",
                                        "ws_clients": ws_clients,
                                        "source": HyperliquidProvider.key,
                                        "name": symbol,
                                        "interval": interval,
                                        "args": [
                                            json.dumps(
                                                {
                                                    "type": "data_update",
                                                    "source": HyperliquidProvider.key,
                                                    "name": symbol,
                                                    "interval": interval,
                                                    "data": data_point,
                                                }
                                            )
                                        ],
                                    }
                                )
                except json.JSONDecodeError:
                    pass
                except Exception as e:
                    logging.error(f"Error processing WebSocket message: {e}")

            def on_error(ws, error):
                logging.error(f"WebSocket error: {error}")

            def on_close(ws, close_status_code, close_msg):
                logging.info(f"WebSocket closed for {symbol} {interval}")
                HyperliquidProvider.streams_stopped_at[(symbol, interval)] = (
                    datetime.now(timezone.utc)
                )
                # Try to restart after a delay
                self.schedule_message(
                    5,
                    {
                        "action": "start_streaming",
                        "args": (None, symbol, interval),
                    },
                )

            def on_open(ws):
                logging.info(f"WebSocket connected for {symbol} {interval}")
                HyperliquidProvider.streams_started_at[(symbol, interval)] = (
                    datetime.now(timezone.utc)
                )

                # Subscribe to candles using the correct format
                subscription = {
                    "method": "subscribe",
                    "subscription": {
                        "type": "candle",
                        "coin": symbol,  # Use "coin" instead of "symbol"
                        "interval": hl_interval,
                    },
                }
                ws.send(json.dumps(subscription))

            # Store the WebSocket connection
            ws_url = "wss://api.hyperliquid.xyz/ws"
            ws = websocket.WebSocketApp(
                ws_url,
                on_open=on_open,
                on_message=on_message,
                on_error=on_error,
                on_close=on_close,
            )
            # Store the stream
            with HyperliquidProvider.lock:
                HyperliquidProvider.streams[(symbol, interval)] = ws

            def run_ws():
                try:
                    ws.run_forever(ping_interval=30, ping_timeout=10)
                except Exception as e:
                    logging.error(
                        f"WebSocket thread crashed for {symbol} {interval}: {e}"
                    )

            thread = threading.Thread(target=run_ws)
            thread.daemon = True
            thread.start()

        except Exception as e:
            logging.error(f"Failed to start stream {(symbol, interval)}: {e}")
            HyperliquidProvider.streams_stopped_at[(symbol, interval)] = datetime.now(
                timezone.utc
            )

    def get_history(self, symbol, interval, start_time_query, end_time_query, count):
        """Get historical data for a symbol and interval."""
        try:
            # Convert interval to Hyperliquid format
            hl_interval = HyperliquidProvider.interval_map.get(interval, "1h")

            # Handle "now UTC" string
            if start_time_query == "now UTC":
                start_time_query = datetime.now(timezone.utc)
            elif isinstance(start_time_query, str):
                start_time_query = datetime.fromisoformat(
                    start_time_query.replace("Z", "+00:00")
                )

            if end_time_query == "now UTC":
                end_time_query = datetime.now(timezone.utc)
            elif isinstance(end_time_query, str):
                end_time_query = datetime.fromisoformat(
                    end_time_query.replace("Z", "+00:00")
                )

            # Calculate start and end timestamps in milliseconds
            start_timestamp = int(start_time_query.timestamp() * 1000)
            end_timestamp = int(end_time_query.timestamp() * 1000)

            # Fetch historical klines using the correct endpoint format
            response = HyperliquidProvider.client.post(
                "/info",
                json={
                    "type": "candleSnapshot",
                    "req": {  # Changed from "request" to "req"
                        "coin": symbol,
                        "interval": hl_interval,
                        "startTime": start_timestamp,
                        "endTime": end_timestamp,
                    },
                },
            )

            # Check response status
            if response.status_code != 200:
                logging.error(
                    f"Error fetching history: HTTP {response.status_code} - {response.text}"
                )
                return []

            data = response.json()

            # The response is an array directly, not nested in "candles"
            klines = data if isinstance(data, list) else data.get("candles", [])

            # Convert to the format expected by format_datapoint
            formatted_klines = []
            for k in klines:
                if isinstance(k, dict):
                    # Handle object format: {t: timestamp, o: open, h: high, l: low, c: close, v: volume}
                    formatted_k = [
                        k.get("t", 0),  # timestamp start in ms
                        float(k.get("o", 0)),  # open
                        float(k.get("h", 0)),  # high
                        float(k.get("l", 0)),  # low
                        float(k.get("c", 0)),  # close
                        float(k.get("v", 0)),  # volume
                    ]
                elif len(k) >= 6:
                    # Handle array format: [timestamp, open, high, low, close, volume]
                    formatted_k = k[:6]
                else:
                    continue

                formatted_klines.append(formatted_k)

            return [
                self.format_datapoint(symbol, interval, k) for k in formatted_klines
            ]
        except Exception as e:
            logging.error(f"Error fetching history for {symbol} {interval}: {e}")
            return []

    def on_close(self, ws_client, symbol, interval):
        """Handle WebSocket client disconnection."""
        with HyperliquidProvider.lock:
            if (symbol, interval) in HyperliquidProvider.ws_clients:
                if ws_client in HyperliquidProvider.ws_clients[(symbol, interval)]:
                    HyperliquidProvider.ws_clients[(symbol, interval)].remove(ws_client)

        if (symbol, interval) in HyperliquidProvider.streams_started_at:
            # Hyperliquid implementation needs recovery time
            diff = (
                datetime.now(timezone.utc)
                - HyperliquidProvider.streams_started_at[(symbol, interval)]
            )
            seconds = 60 * 5
            if diff <= timedelta(seconds=seconds):
                HyperliquidProvider.streams_started_at[(symbol, interval)] = (
                    datetime.now(timezone.utc)
                )
                schedule_in_seconds = (seconds - diff.total_seconds()) + 5
                return self.schedule_message(
                    schedule_in_seconds,
                    {"action": "on_close", "args": (ws_client, symbol, interval)},
                )

        with HyperliquidProvider.lock:
            if (symbol, interval) in HyperliquidProvider.streams_started_at:
                del HyperliquidProvider.streams_started_at[(symbol, interval)]

            if (symbol, interval) in HyperliquidProvider.ws_clients:
                logging.info(
                    f"{symbol} {interval} running {len(HyperliquidProvider.ws_clients[(symbol, interval)])} clients..."
                )

                if (
                    len(HyperliquidProvider.ws_clients[(symbol, interval)]) == 0
                ):  # No more clients interested
                    del HyperliquidProvider.ws_clients[(symbol, interval)]

                    if (symbol, interval) in HyperliquidProvider.streams:
                        logging.info(f"{symbol} {interval} stopping streaming...")
                        stream = HyperliquidProvider.streams[(symbol, interval)]
                        try:
                            stream.close()
                        except Exception as e:
                            logging.warning(
                                f"Failed to close WebSocket for {symbol} {interval}: {e}"
                            )

                        del HyperliquidProvider.streams[(symbol, interval)]

                        HyperliquidProvider.streams_stopped_at[(symbol, interval)] = (
                            datetime.now(timezone.utc)
                        )
