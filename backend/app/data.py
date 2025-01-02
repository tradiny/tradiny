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

import pandas as pd
from datetime import datetime, timedelta, timezone

from .globals import lock, historical_data_cache


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
