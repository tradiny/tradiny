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
import asyncio
import httpx

from binance import Client, ThreadedWebsocketManager
import time

from config import Config
from provider import Provider

###
### This is a fix for ThreadedWebsocketManager
###
import asyncio


async def start_listener(self, socket, path: str, callback):
    async with socket as s:
        while path in self._socket_running and self._socket_running[path]:
            try:
                msg = await asyncio.wait_for(s.recv(), 3)
            except asyncio.TimeoutError:
                ...
                continue
            else:
                if not msg:
                    continue
                callback(msg)
    if path in self._socket_running:  # fix KeyError
        del self._socket_running[path]


ThreadedWebsocketManager.start_listener = start_listener
###
###
###


def fetch_binance_asset_data():
    url = "https://www.binance.com/bapi/asset/v2/public/asset/asset/get-all-asset"
    asset_metadata = {}

    headers = {"accept": "*/*", "user-agent": "curl/8.5.0"}

    try:
        # Use httpx to support HTTP/2 and session initiation
        with httpx.Client(http2=True) as client:
            # Directly access the target URL
            response = client.get(url, headers=headers)
            response.raise_for_status()  # Raise an error if status != 200
            data = response.json()
            for d in data.get(
                "data", []
            ):  # Assume JSON might have a 'data' key, adjust as per API response
                asset_metadata[d["assetCode"]] = d
    except Exception as e:
        logging.error(f"An error occurred: {e}")

    return asset_metadata


class BinanceProvider(Provider):
    key = "Binance"
    type = "candlestick"
    client = "not initialized"
    twm = "not initialized"
    lock = threading.Lock()
    ws_clients = {}  # Maps (symbol, interval) to list of clients
    streams = {}  # Maps (symbol, interval) to stream
    streams_started_at = {}
    streams_stopped_at = {}
    streams_scheduled = {}

    def init(self):
        BinanceProvider.client = Client(
            Config.BINANCE_API_KEY, Config.BINANCE_API_SECRET
        )
        BinanceProvider.twm = ThreadedWebsocketManager(
            api_key=Config.BINANCE_API_KEY, api_secret=Config.BINANCE_API_SECRET
        )
        BinanceProvider.twm.start()

    def get_dataset(self):
        asset_metadata = fetch_binance_asset_data()

        BinanceProvider.client = Client(
            Config.BINANCE_API_KEY, Config.BINANCE_API_SECRET
        )
        exchange_info = BinanceProvider.client.get_exchange_info()
        symbols = []
        for s in exchange_info["symbols"]:
            if s["status"] == "TRADING":
                symbol = s["symbol"]

                name_label = ""
                base_asset = s["baseAsset"]
                quote_asset = s["quoteAsset"]
                if (
                    base_asset
                    and base_asset in asset_metadata
                    and quote_asset
                    and quote_asset in asset_metadata
                ):
                    name_label = f"{asset_metadata[base_asset]['assetName']} - {asset_metadata[quote_asset]['assetName']}"
                else:
                    name_label = s["symbol"]

                symbols.append(
                    {
                        "source": BinanceProvider.key,
                        "name": s["symbol"],
                        "name_label": name_label,
                        "type": BinanceProvider.type,
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
                            "6h",
                            "8h",
                            "12h",
                            "1d",
                            "1w",
                            "1M",
                        ],
                        "outputs": [
                            {"name": f"open", "y_axis": f"price"},
                            {"name": f"high", "y_axis": f"price"},
                            {"name": f"low", "y_axis": f"price"},
                            {"name": f"close", "y_axis": f"price"},
                            {"name": f"volume", "y_axis": f"volume"},
                        ],
                    }
                )
        return symbols

    def schedule_message(self, delay, message):
        def delayed_execution():
            time.sleep(delay)
            self.send_to(message)

        thread = threading.Thread(target=delayed_execution)
        thread.start()

    def start_streaming(self, ws_client, symbol, interval):

        if (symbol, interval) in BinanceProvider.streams_stopped_at:
            # Binance implemention needs at least 5 seconds to recover from the stopped state
            diff = (
                datetime.now(timezone.utc)
                - BinanceProvider.streams_stopped_at[(symbol, interval)]
            )
            seconds = 5
            if diff <= timedelta(seconds=seconds):

                if (
                    symbol,
                    interval,
                ) not in BinanceProvider.streams_stopped_at:  # not scheduled

                    BinanceProvider.streams_stopped_at[(symbol, interval)] = (
                        datetime.now(timezone.utc)
                    )
                    return self.schedule_message(
                        seconds - diff.total_seconds(),
                        {
                            "action": "start_streaming",
                            "args": (ws_client, symbol, interval),
                        },
                    )

                else:
                    return

        if (symbol, interval) in BinanceProvider.streams_stopped_at:
            del BinanceProvider.streams_stopped_at[(symbol, interval)]

        with BinanceProvider.lock:
            if (symbol, interval) not in BinanceProvider.ws_clients:
                BinanceProvider.ws_clients[(symbol, interval)] = []

            if ws_client not in BinanceProvider.ws_clients[(symbol, interval)]:

                if ws_client is not None:
                    BinanceProvider.ws_clients[(symbol, interval)].append(ws_client)

                self._start_binance_stream(
                    symbol, interval
                )  # Send historical data to new subscriber

    def format_datapoint(self, symbol, interval, k):
        date_str = datetime.fromtimestamp(k[0] / 1000, timezone.utc).strftime(
            "%Y-%m-%d %H:%M:%S"
        )
        return {
            "date": date_str,
            f"{BinanceProvider.key}-{symbol}-{interval}-open": k[1],
            f"{BinanceProvider.key}-{symbol}-{interval}-high": k[2],
            f"{BinanceProvider.key}-{symbol}-{interval}-low": k[3],
            f"{BinanceProvider.key}-{symbol}-{interval}-close": k[4],
            f"{BinanceProvider.key}-{symbol}-{interval}-volume": k[5],
        }

    def no_update(self, symbol, interval):
        logging.info(f"No update for {symbol} {interval}, restarting...")

        if (symbol, interval) in BinanceProvider.streams:
            stream = BinanceProvider.streams[(symbol, interval)]
            del BinanceProvider.streams[(symbol, interval)]

            BinanceProvider.streams_stopped_at[(symbol, interval)] = datetime.now(
                timezone.utc
            )
            BinanceProvider.twm.stop_socket(stream)

        self.start_streaming(None, symbol, interval)

    def _start_binance_stream(self, symbol, interval):
        try:

            def handle_stream(msg):
                # return
                if msg["e"] == "kline":
                    # print(msg)
                    data = self.format_datapoint(
                        symbol,
                        interval,
                        [
                            msg["k"]["t"],
                            msg["k"]["o"],
                            msg["k"]["h"],
                            msg["k"]["l"],
                            msg["k"]["c"],
                            msg["k"]["v"],
                        ],
                    )

                    self.send_from(
                        {
                            "action": "update_in_cache",
                            "args": (BinanceProvider.key, symbol, interval, [data]),
                        }
                    )

                    ws_clients = BinanceProvider.ws_clients.get((symbol, interval), [])

                    if len(ws_clients) > 0:

                        self.send_from(
                            {
                                "action": "write_message",
                                "ws_clients": ws_clients,
                                "source": BinanceProvider.key,
                                "name": symbol,
                                "interval": interval,
                                "args": [
                                    json.dumps(
                                        {
                                            "type": "data_update",
                                            "source": BinanceProvider.key,
                                            "name": symbol,
                                            "interval": interval,
                                            "data": data,
                                        }
                                    )
                                ],
                            }
                        )

            if (symbol, interval) not in BinanceProvider.streams:
                logging.info(f"starting streaming for {symbol}, {interval}")
                BinanceProvider.streams_started_at[(symbol, interval)] = datetime.now(
                    timezone.utc
                )
                BinanceProvider.streams[(symbol, interval)] = (
                    BinanceProvider.twm.start_kline_socket(
                        callback=handle_stream, symbol=symbol, interval=interval
                    )
                )

        except Exception as e:
            logging.error(f"Failed to start stream {(symbol, interval)}: {e}")

    def get_history(self, symbol, interval, start_time_query, end_time_query, count):
        new_klines = BinanceProvider.client.get_historical_klines(
            symbol, interval, start_time_query, end_time_query
        )
        return [self.format_datapoint(symbol, interval, k) for k in new_klines]

    def on_close(self, ws_client, symbol, interval):

        with BinanceProvider.lock:
            if (symbol, interval) in BinanceProvider.ws_clients:
                if ws_client in BinanceProvider.ws_clients[(symbol, interval)]:
                    BinanceProvider.ws_clients[(symbol, interval)].remove(ws_client)

        if (symbol, interval) in BinanceProvider.streams_started_at:
            # Binance implemention needs at least 5 seconds to recover from the stopped state
            diff = (
                datetime.now(timezone.utc)
                - BinanceProvider.streams_started_at[(symbol, interval)]
            )
            seconds = 60 * 5
            if diff <= timedelta(seconds=seconds):
                BinanceProvider.streams_started_at[(symbol, interval)] = datetime.now(
                    timezone.utc
                )
                schedule_in_seconds = (seconds - diff.total_seconds()) + 5
                return self.schedule_message(
                    schedule_in_seconds,
                    {"action": "on_close", "args": (ws_client, symbol, interval)},
                )

        with BinanceProvider.lock:
            if (symbol, interval) in BinanceProvider.streams_started_at:
                del BinanceProvider.streams_started_at[(symbol, interval)]

            if (symbol, interval) in BinanceProvider.ws_clients:
                logging.info(
                    f"{symbol} {interval} running {len(BinanceProvider.ws_clients[(symbol, interval)])} clients..."
                )

                if (
                    len(BinanceProvider.ws_clients[(symbol, interval)]) == 0
                ):  # No more clients interested
                    del BinanceProvider.ws_clients[(symbol, interval)]

                    if (symbol, interval) in BinanceProvider.streams:
                        logging.info(f"{symbol} {interval} stopping streaming...")
                        stream = BinanceProvider.streams[(symbol, interval)]
                        del BinanceProvider.streams[(symbol, interval)]

                        BinanceProvider.streams_stopped_at[(symbol, interval)] = (
                            datetime.now(timezone.utc)
                        )
                        BinanceProvider.twm.stop_socket(stream)
