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

import threading
import re
from datetime import datetime, timedelta, timezone
import logging

from polygon import RESTClient
from polygon import WebSocketClient
from typing import List

from provider import Provider
from config import Config


class PolygonProvider(Provider):
    interval_map = {
        "1m": {"timespan": "minute", "multiplier": 1},
        "3m": {"timespan": "minute", "multiplier": 3},
        "5m": {"timespan": "minute", "multiplier": 5},
        "15m": {"timespan": "minute", "multiplier": 15},
        "30m": {"timespan": "minute", "multiplier": 30},
        "1h": {"timespan": "hour", "multiplier": 1},
        "2h": {"timespan": "hour", "multiplier": 2},
        "4h": {"timespan": "hour", "multiplier": 4},
        "6h": {"timespan": "hour", "multiplier": 6},
        "8h": {"timespan": "hour", "multiplier": 8},
        "12h": {"timespan": "hour", "multiplier": 12},
        "1d": {"timespan": "day", "multiplier": 1},
        "3d": {"timespan": "day", "multiplier": 3},
        "1w": {"timespan": "week", "multiplier": 1},
        "1M": {"timespan": "month", "multiplier": 1},
    }
    intervals_date_formats = {
        "1m": "%Y-%m-%d %H:%M:00",
        "3m": "%Y-%m-%d %H:%M:00",
        "5m": "%Y-%m-%d %H:%M:00",
        "15m": "%Y-%m-%d %H:%M:00",
        "30m": "%Y-%m-%d %H:%M:00",
        "1h": "%Y-%m-%d %H:00:00",
        "2h": "%Y-%m-%d %H:00:00",
        "3h": "%Y-%m-%d %H:00:00",
        "4h": "%Y-%m-%d %H:00:00",
        "6h": "%Y-%m-%d %H:00:00",
        "8h": "%Y-%m-%d %H:00:00",
        "12h": "%Y-%m-%d %H:00:00",
        "1d": "%Y-%m-%d 00:00:00",
        "3d": "%Y-%m-%d 00:00:00",
        "1w": "%Y-%m-%d 00:00:00",
        "1M": "%Y-%m-01 00:00:00",
    }
    key = "polygon_io"
    type = "candlestick"
    client = "not initialized"
    twm = "not initialized"
    lock = threading.Lock()
    ws_clients = {}  # Maps (symbol, interval) to list of clients
    streams = {}  # Maps (symbol, interval) to stream
    streams_started_at = {}
    streams_stopped_at = {}
    streams_scheduled = {}
    symbol_intervals_map = {}
    cache = {}

    def init(self):
        PolygonProvider.client = RESTClient(api_key=Config.POLYGON_IO_API_KEY)
        PolygonProvider.wsclient = WebSocketClient(
            api_key=Config.POLYGON_IO_API_KEY, feed="delayed.polygon.io"
        )

        # approach taken from the Polygon examples
        # https://github.com/polygon-io/client-python/blob/master/examples/websocket/stocks-ws_extra.py
        def run_wsclient():
            PolygonProvider.wsclient.run(self.handle_msg)

        wsclient_thread = threading.Thread(target=run_wsclient)
        wsclient_thread.start()

    def get_dataset(self):
        tickers = []
        PolygonProvider.client = RESTClient(api_key=Config.POLYGON_IO_API_KEY)

        def to_ticker(t):
            return {
                "source": PolygonProvider.key,
                "source_label": t.primary_exchange,
                "name": t.ticker,
                "name_label": t.name,
                "type": PolygonProvider.type,
                "categories": [t.market.capitalize()],
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
                    "3d",
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

        limit = 1000
        data = Config.POLYGON_MARKETS.split(",")

        logging.info("Started fetching tickers from Polygon.")

        markets = {
            "options": {
                "params": {"market": "options"},
                "message": "Fetching options.",
            },
            "indices": {
                "params": {"market": "indices"},
                "message": "Fetching indices.",
            },
            "fx": {"params": {"market": "fx"}, "message": "Fetching fx."},
            "crypto": {"params": {"market": "crypto"}, "message": "Fetching crypto."},
            "stocks": {
                "params": {"market": "stocks", "type": "CS", "active": True},
                "message": "Fetching stocks (this might take a while).",
            },
        }

        for key, value in markets.items():
            if key in data:
                logging.info(f'{value["message"]}')
                for t in PolygonProvider.client.list_tickers(
                    limit=limit, **value["params"]
                ):
                    tickers.append(to_ticker(t))

        logging.info("Done fetching tickers from Polygon.")
        return tickers

    def format_datapoint(self, ticker, interval, k):
        return {
            "date": k["date"],
            f"{PolygonProvider.key}-{ticker}-{interval}-open": k["open"],
            f"{PolygonProvider.key}-{ticker}-{interval}-high": k["high"],
            f"{PolygonProvider.key}-{ticker}-{interval}-low": k["low"],
            f"{PolygonProvider.key}-{ticker}-{interval}-close": k["close"],
            f"{PolygonProvider.key}-{ticker}-{interval}-volume": k["volume"],
        }

    def interval_date(self, interval, date_str):

        date = datetime.strptime(date_str, "%Y-%m-%d %H:%M:%S").replace(
            tzinfo=timezone.utc
        )

        if interval in ["3m", "5m", "15m", "30m"]:
            n = int(re.findall(r"\d+", interval)[0])
            m = date.minute - (date.minute % n)
            date = date.replace(minute=m)
        if interval in ["2h", "4h", "6h", "8h", "12h"]:
            n = int(re.findall(r"\d+", interval)[0])
            h = date.hour - (date.hour % n)
            date = date.replace(hour=h)
        if interval in ["3d"]:
            n = int(re.findall(r"\d+", interval)[0])
            d = date.day - (date.day % n)
            if d == 0:
                d = 1
            date = date.replace(day=d)

        date_str = date.strftime(PolygonProvider.intervals_date_formats[interval])

        return date_str

    def get_history(self, ticker, interval, start_time_query, end_time_query, count):
        f = datetime.strptime(
            self.interval_date(interval, start_time_query), "%Y-%m-%d %H:%M:%S"
        ).replace(tzinfo=timezone.utc)

        if end_time_query == "now UTC":
            t = datetime.now(timezone.utc)
        else:
            t = datetime.strptime(end_time_query, "%Y-%m-%d %H:%M:%S").replace(
                tzinfo=timezone.utc
            )

        def to_dict(a):
            date = datetime.fromtimestamp(a.timestamp / 1000, timezone.utc).strftime(
                "%Y-%m-%d %H:%M:%S"
            )
            return {
                "date": date,
                "open": a.open,
                "high": a.high,
                "low": a.low,
                "close": a.close,
                "volume": a.volume,
            }

        return [
            self.format_datapoint(ticker, interval, to_dict(a))
            for a in PolygonProvider.client.list_aggs(
                ticker,
                PolygonProvider.interval_map[interval]["multiplier"],
                PolygonProvider.interval_map[interval]["timespan"],
                int(f.timestamp() * 1000),
                int(t.timestamp() * 1000),
                adjusted=True,
                sort="asc",
                limit=50000,
            )
        ]

    def update_symbol_intervals_map(self):

        for k in PolygonProvider.ws_clients.keys():
            s, i = k

            if s not in PolygonProvider.symbol_intervals_map:
                PolygonProvider.symbol_intervals_map[s] = []

            if i not in PolygonProvider.symbol_intervals_map[s]:
                PolygonProvider.symbol_intervals_map[s].append(i)

    def start_streaming(self, ws_client, symbol, interval):

        try:

            with PolygonProvider.lock:
                if (symbol, interval) not in PolygonProvider.ws_clients:
                    PolygonProvider.ws_clients[(symbol, interval)] = []

                if ws_client not in PolygonProvider.ws_clients[(symbol, interval)]:

                    if ws_client is not None:
                        PolygonProvider.ws_clients[(symbol, interval)].append(ws_client)

                    self.update_symbol_intervals_map()

                    if (symbol, interval) not in PolygonProvider.streams:
                        logging.info(f"starting streaming for {symbol}, {interval}")
                        PolygonProvider.streams_started_at[(symbol, interval)] = (
                            datetime.now(timezone.utc)
                        )

                        PolygonProvider.streams[(symbol, interval)] = f"A.{symbol}"
                        PolygonProvider.wsclient.subscribe(f"A.{symbol}")

        except Exception as e:
            logging.error(f"Failed to start stream {(symbol, interval)}: {e}")

    def handle_msg(self, msgs):
        for m in msgs:
            symbol = m.symbol
            open = m.open
            close = m.close
            high = m.high
            low = m.low
            volume = m.volume
            date = datetime.fromtimestamp(m.start_timestamp / 1000, timezone.utc)

            if symbol in PolygonProvider.symbol_intervals_map:
                intervals = PolygonProvider.symbol_intervals_map[symbol]
                for interval in intervals:

                    ws_clients = PolygonProvider.ws_clients.get((symbol, interval), [])
                    if len(ws_clients) > 0:
                        _date = self.interval_date(
                            interval, date.strftime("%Y-%m-%d %H:%M:%S")
                        )

                        if (symbol, interval) not in PolygonProvider.cache:
                            PolygonProvider.cache[(symbol, interval)] = {}

                        if (
                            "date" in PolygonProvider.cache[(symbol, interval)]
                            and _date
                            == PolygonProvider.cache[(symbol, interval)]["date"]
                        ):
                            if high > PolygonProvider.cache[(symbol, interval)]["high"]:
                                PolygonProvider.cache[(symbol, interval)]["high"] = high
                            if low < PolygonProvider.cache[(symbol, interval)]["low"]:
                                PolygonProvider.cache[(symbol, interval)]["low"] = low
                            PolygonProvider.cache[(symbol, interval)]["close"] = close
                            PolygonProvider.cache[(symbol, interval)][
                                "volume"
                            ] += volume
                        else:
                            PolygonProvider.cache[(symbol, interval)] = {
                                "date": _date,
                                "open": open,
                                "high": high,
                                "low": low,
                                "close": close,
                                "volume": volume,
                            }

                        self.send_from(
                            {
                                "action": "data_update_merge",
                                "ws_clients": ws_clients,
                                "source": PolygonProvider.key,
                                "name": symbol,
                                "interval": interval,
                                "data": self.format_datapoint(
                                    symbol,
                                    interval,
                                    PolygonProvider.cache[(symbol, interval)],
                                ),
                            }
                        )

    def on_close(self, ws_client, symbol, interval):

        with PolygonProvider.lock:
            if (symbol, interval) in PolygonProvider.ws_clients:
                if ws_client in PolygonProvider.ws_clients[(symbol, interval)]:
                    PolygonProvider.ws_clients[(symbol, interval)].remove(ws_client)

        with PolygonProvider.lock:
            if (symbol, interval) in PolygonProvider.streams_started_at:
                del PolygonProvider.streams_started_at[(symbol, interval)]

            if (symbol, interval) in PolygonProvider.ws_clients:
                logging.info(
                    f"{symbol} {interval} running {len(PolygonProvider.ws_clients[(symbol, interval)])} clients..."
                )

                if (
                    len(PolygonProvider.ws_clients[(symbol, interval)]) == 0
                ):  # No more clients interested
                    del PolygonProvider.ws_clients[(symbol, interval)]

                    if (symbol, interval) in PolygonProvider.streams:
                        logging.info(f"{symbol} {interval} stopping streaming...")
                        stream = PolygonProvider.streams[(symbol, interval)]
                        del PolygonProvider.streams[(symbol, interval)]

                        PolygonProvider.wsclient.unsubscribe(stream)

    def no_update(self, symbol, interval):
        logging.info(f"No update for {symbol} {interval}, restarting...")

        if (symbol, interval) in PolygonProvider.streams:
            stream = PolygonProvider.streams[(symbol, interval)]
            del PolygonProvider.streams[(symbol, interval)]

            PolygonProvider.streams_stopped_at[(symbol, interval)] = datetime.now(
                timezone.utc
            )
            PolygonProvider.wsclient.unsubscribe(stream)

        self.start_streaming(None, symbol, interval)
