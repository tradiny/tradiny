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
import pandas as pd
from collections import OrderedDict
import time
import socket

from pathlib import Path
import sys


def find_free_port(host, start_port=8000):
    port = start_port
    while True:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            if sock.connect_ex((host, port)) != 0:
                return port
            port += 1


def get_private_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        # Connect to an external server, here Google DNS, just to determine the network interface.
        s.connect(("8.8.8.8", 80))
        private_ip = s.getsockname()[0]
    except Exception:
        private_ip = "127.0.0.1"  # Fallback to localhost in case of error.
    finally:
        s.close()
    return private_ip


# Get the base path, works for both bundled and non-bundled modes
def resource_path(relative_path):
    # PyInstaller creates a temp folder and stores path in _MEIPASS
    base_path = getattr(sys, "_MEIPASS", Path("."))
    return Path(base_path).joinpath(relative_path)


class LimitedSizeDict(OrderedDict):
    def __init__(self, max_size, *args, **kwargs):
        self.max_size = max_size
        super().__init__(*args, **kwargs)

    def __setitem__(self, key, value):
        if key in self:
            del self[key]  # Remove existing item to update position
        elif len(self) >= self.max_size:
            self.popitem(last=False)  # Remove the oldest item
        super().__setitem__(key, value)


def clean_old_requests(obj):
    current_time = time.time()
    cutoff_time = current_time - 3600  # 1 hour
    for ip in list(obj.keys()):
        # Remove requests older than 1 hour
        obj[ip] = [t for t in obj[ip] if t > cutoff_time]
        # Remove the IP entry if no recent requests
        if not obj[ip]:
            del obj[ip]


def register_request(obj, ip):
    clean_old_requests(obj)
    obj[ip].append(time.time())


def is_request_allowed(maximum, obj, ip):
    clean_old_requests(obj)
    return len(obj[ip]) < int(maximum)


def determine_data_needs(cached_data, start_time, end_time):
    # Convert start_time and end_time to datetime objects
    if isinstance(start_time, str):
        start_time = pd.to_datetime(start_time).replace(tzinfo=timezone.utc)
    if isinstance(end_time, str):
        end_time = pd.to_datetime(end_time).replace(tzinfo=timezone.utc)

    # If cached_df is empty, return the full range
    if "cached_df" not in cached_data or cached_data["cached_df"].empty:
        return start_time, end_time

    # Extract the first and last dates from the cached DataFrame
    cached_df = cached_data["cached_df"]
    first_cached = cached_df.index.min().replace(tzinfo=timezone.utc)
    last_cached = cached_df.index.max().replace(tzinfo=timezone.utc)

    # Determine the data needs
    start_needed = start_time if start_time < first_cached else None
    end_needed = end_time if end_time > last_cached else None

    return start_needed, end_needed


def get_last_n_items(cached_data, n):
    # Ensure 'cached_df' exists in cached_data and is not empty
    if (
        cached_data is None
        or "cached_df" not in cached_data
        or cached_data["cached_df"].empty
    ):
        return []

    # Get the last n items from the DataFrame
    last_n_df = cached_data["cached_df"].tail(n).copy()

    # Convert the index back to a column and convert dates to strings
    last_n_df = last_n_df.reset_index()
    if "date" in last_n_df.columns and pd.api.types.is_datetime64_any_dtype(
        last_n_df["date"]
    ):
        last_n_df["date"] = last_n_df["date"].dt.strftime("%Y-%m-%d %H:%M:%S")

    # Convert the DataFrame to a list of dictionaries
    data_to_return = last_n_df.to_dict("records")

    return data_to_return


def filter_data(cached_data, required_start_time, required_end_time):
    # Ensure 'cached_df' exists in cached_data
    if "cached_df" not in cached_data or cached_data["cached_df"].empty:
        return []

    # Convert start and end times to datetime
    required_start_time = pd.to_datetime(required_start_time)
    required_end_time = pd.to_datetime(required_end_time)

    if required_start_time.tzinfo is not None:
        required_start_time = required_start_time.tz_convert(None)
    if required_end_time.tzinfo is not None:
        required_end_time = required_end_time.tz_convert(None)

    # Filter cached_df within the required time range
    filtered_df = (
        cached_data["cached_df"].loc[required_start_time:required_end_time].copy()
    )

    # Convert the index back to a column and convert dates to strings
    filtered_df = filtered_df.reset_index()
    filtered_df["date"] = filtered_df["date"].dt.strftime("%Y-%m-%d %H:%M:%S")

    # Convert the filtered DataFrame to a list of dictionaries
    data_to_return = filtered_df.to_dict("records")

    return data_to_return


def filter_df(df, required_start_time, required_end_time):
    # Convert start and end times to datetime
    required_start_time = pd.to_datetime(required_start_time)
    required_end_time = pd.to_datetime(required_end_time)

    if required_start_time.tzinfo is not None:
        required_start_time = required_start_time.tz_convert(None)
    if required_end_time.tzinfo is not None:
        required_end_time = required_end_time.tz_convert(None)

    # Filter cached_df within the required time range
    filtered_df = df.loc[required_start_time:required_end_time].copy()

    # Convert the index back to a column and convert dates to strings
    filtered_df = filtered_df.reset_index()
    filtered_df["date"] = filtered_df["date"].dt.strftime("%Y-%m-%d %H:%M:%S")

    return filtered_df


def get_interval_duration(interval):
    # Return the duration in minutes for a given interval
    interval_to_minutes = {
        "1m": 1,
        "3m": 3,
        "5m": 5,
        "15m": 15,
        "30m": 30,
        "1h": 60,
        "2h": 120,
        "4h": 240,
        "6h": 360,
        "8h": 480,
        "12h": 720,
        "1d": 1440,
        "1w": 10080,
        "1M": 43800,
    }
    return interval_to_minutes.get(interval, 0)


def get_lookback_period(interval, from_time=datetime.utcnow(), count=300):
    # Mapping interval names to their total minutes
    interval_to_minutes = {
        "1m": 1,
        "3m": 3,
        "5m": 5,
        "15m": 15,
        "30m": 30,
        "1h": 60,
        "2h": 120,
        "4h": 240,
        "6h": 360,
        "8h": 480,
        "12h": 720,
        "1d": 1440,
        "1w": 10080,
        "1M": 43800,  # Approximate average month in minutes (30.44 days)
    }

    minutes = interval_to_minutes.get(interval)
    if not minutes:
        raise ValueError("Unsupported interval")

    total_minutes = minutes * count
    look_back = timedelta(minutes=total_minutes)
    start_time = from_time - look_back
    return start_time  # Format the datetime to string


def get_current_date(interval):
    intervals = {
        "1m": 1,
        "3m": 3,
        "5m": 5,
        "15m": 15,
        "30m": 30,
        "1h": 60,
        "2h": 120,
        "4h": 240,
        "6h": 360,
        "8h": 480,
        "12h": 720,
        "1d": 1440,
        "1w": 10080,
        "1M": 43800,
    }

    now = datetime.now(timezone.utc)

    if interval not in intervals:
        raise ValueError(
            f"Interval {interval} is not recognized. Please use one of {list(intervals.keys())}"
        )

    minutes = intervals[interval]

    if interval == "1M":  # Special case for monthly interval
        start_of_month = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        return start_of_month.strftime("%Y-%m-%d %H:%M:%S")

    if interval == "1w":  # Special case for weekly interval
        start_of_week = now - timedelta(days=now.weekday())
        start_of_week = start_of_week.replace(hour=0, minute=0, second=0, microsecond=0)
        return start_of_week.strftime("%Y-%m-%d %H:%M:%S")

    # For all other intervals
    delta = timedelta(minutes=minutes)
    current_candle_start = (
        now - (now - datetime.min.replace(tzinfo=timezone.utc)) % delta
    )
    return current_candle_start.strftime("%Y-%m-%d %H:%M:%S")


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
