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
from queue import Empty
from datetime import datetime, timedelta, timezone
import numpy as np
import pandas as pd
import json
import random

from fastapi import WebSocket

from utils import (
    determine_data_needs,
    get_last_n_items,
    filter_data,
    filter_df,
    get_lookback_period,
    get_current_date,
    resource_path,
    generate_method_key,
)
from db import indicators
from .data import update_in_cache, merge_data
from .globals import (
    providers,
    clients,
    historical_data_cache,
    last_update,
    lock,
    indicator_fetcher,
)
from .connection import safe_send_message


futures = {}


async def send_historical_data(
    websocket: WebSocket,
    source,
    name,
    interval,
    count=300,
    end="now UTC",
    metadata=None,
    force_request_data=False,
):
    key = generate_method_key(
        "send_historical_data",
        source,
        name,
        interval,
        count=300,
        end="now UTC",
        r=random.randint(1, 999999),
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

    if force_request_data or (
        not request_recent_data_and_has_last_date and (start_needed or end_needed)
    ):
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


async def handle_message_from_provider(queue):
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

                                    m = await indicator_fetcher.fetch(
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

                                    m = await indicator_fetcher.fetch(
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
            logging.error(f"Error in handle_message_from_provider(): {e} {message}")
        except Empty:
            continue
