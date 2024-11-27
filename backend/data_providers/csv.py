# This software is licensed under a dual license:
#
# 1. Creative Commons Attribution-NonCommercial (CC BY-NC)
#    for individuals and open source projects.
# 2. Commercial License for business use.
#
# For commercial inquiries, contact: license@tradiny.com
#
# For more details, refer to the LICENSE.md file in the root directory of this project.

from datetime import datetime, timedelta, timezone
import threading

import time
import re
import logging

from provider import Provider
from config import Config

import os


def replace_non_alphanumeric(text):
    # Use regex to replace all non-alphanumeric characters with '-'
    result = re.sub(r"[^a-zA-Z0-9]", "-", text)
    return result


def clean_header(filepath, date_column, lines_to_check=300):
    with open(filepath, "r", encoding="utf-8") as f:
        header = f.readline().strip().split(",")

        # Initialize a dictionary to count numeric occurrences for each column
        numeric_count = {col: 0 for col in header if col != date_column}

        # Track the total number of lines successfully read
        total_lines_checked = 0

        for _ in range(lines_to_check):
            line = f.readline().strip()
            if not line:
                break

            total_lines_checked += 1
            row = line.split(",")

            for i, value in enumerate(row):
                if i >= len(header):
                    break

                column_name = header[i]
                if column_name == date_column:
                    continue

                if value.strip() != "":
                    try:
                        float(value)
                        numeric_count[column_name] += 1
                    except ValueError:
                        continue

        # Determine the threshold for numeric columns
        threshold = total_lines_checked * 0.1

        # Filter header to only include columns with numeric values exceeding the threshold
        filtered_header = [
            col for col, count in numeric_count.items() if count >= threshold
        ]

    return filtered_header


class CSVProvider(Provider):
    key = "csv"
    type = "line"
    lock = threading.Lock()
    ws_clients = {}  # Maps (symbol, interval) to list of clients

    def __init__(self):

        if Config.CSV_DATE_COLUMN_FORMATTER == "ISO-8601":

            def _(d):
                try:
                    datetime_object = datetime.strptime(d, "%Y-%m-%dT%H:%M:%S.%fZ")
                    return datetime_object.strftime("%Y-%m-%d %H:%M:%S")
                except ValueError as e:
                    return d

            date_column_formatter = _

        else:

            def _(d):
                return d

            date_column_formatter = _

        self.folderpath = Config.CSV_FOLDER_PATH
        self.date_column = Config.CSV_DATE_COLUMN
        self.date_column_formatter = date_column_formatter

        super().__init__()

    def init(self):
        pass

    def get_csv_files(self):
        csv_files = []
        for root, dirs, files in os.walk(self.folderpath):
            for file in files:
                if file.endswith(".csv"):
                    csv_files.append(os.path.join(root, file))
        return csv_files

    def get_dataset(self):

        dataset = []

        for filepath in self.get_csv_files():
            name = replace_non_alphanumeric(os.path.basename(filepath).rstrip(".csv"))
            header = clean_header(filepath, self.date_column)

            if "open" in header:  # candlestick type
                print(f"Creating candlestick {filepath}")
                dataset.append(
                    {
                        "source": CSVProvider.key,
                        "name": name,
                        "name_label": f"{name}.csv, OHLCV",
                        "path": filepath,
                        "type": "candlestick",
                        "categories": ["CSV"],
                        "outputs": [
                            {"name": f"open", "y_axis": f"price"},
                            {"name": f"high", "y_axis": f"price"},
                            {"name": f"low", "y_axis": f"price"},
                            {"name": f"close", "y_axis": f"price"},
                            {"name": f"volume", "y_axis": f"volume"},
                        ],
                    }
                )

            excluded_values = ["date", "open", "high", "low", "close", "volume"]
            additional_values = [
                value for value in header if value not in excluded_values
            ]

            for value in additional_values:

                print(f"Creating line {value}")
                dataset.append(
                    {
                        "source": CSVProvider.key,
                        "name": f"{name}__{value}",
                        "name_label": f"{name}.csv, column {value}",
                        "path": filepath,
                        "type": "line",
                        "categories": ["CSV"],
                        "outputs": [{"name": value, "y_axis": value}],
                    }
                )

        return dataset

    def schedule_message(self, delay, message):
        def delayed_execution():
            time.sleep(delay)
            self.send_to(message)

        thread = threading.Thread(target=delayed_execution)
        thread.start()

    def no_update(self, symbol, interval):
        pass

    def start_streaming(self, ws_client, name, interval):
        pass

    def format_datapoint(self, name, interval, k, file_path):
        d = {"date": k["date"]}
        for c, _ in k.items():
            if len(name) == 1:
                d[f"{CSVProvider.key}-{name[0]}-{interval}-{c}"] = k[c]

            if len(name) == 2:
                d[f"{CSVProvider.key}-{name[0]}__{name[1]}-{interval}"] = k[c]

        return d

    def find_filepath_by_name(self, directory, name):
        """Find file path based on the processed name."""
        csv_files = self.get_csv_files()
        for filepath in csv_files:
            csv_name = replace_non_alphanumeric(
                os.path.basename(filepath).rstrip(".csv")
            )
            if csv_name == name:
                return filepath

            header = clean_header(filepath, self.date_column)
            excluded_values = ["date", "open", "high", "low", "close", "volume"]
            additional_values = [
                value for value in header if value not in excluded_values
            ]

            for value in additional_values:
                name_column = f"{csv_name}__{value}"
                if name_column == name:
                    return filepath
        return None

    def get_history(self, name, interval, start_time_query, end_time_query, count=300):
        name = name.split("__")
        file_path = self.find_filepath_by_name(self.folderpath, name[0])

        try:
            new_klines = self.read_last_n_lines_with_date_filter(
                file_path=file_path,
                n_lines=count,
                skip_lines=0,
                date_column=self.date_column,
                date_column_formatter=self.date_column_formatter,
                start_time_query=start_time_query,
                end_time_query=end_time_query,
            )
        except Exception as e:
            logging.error(f"Error {e}")

        new_klines = [
            self.format_datapoint(name, interval, k, file_path) for k in new_klines
        ]

        return new_klines

    def on_close(self, ws_client, name, interval):
        pass

    def read_last_n_lines_with_date_filter(
        self,
        file_path,
        n_lines,
        skip_lines=0,
        date_column="",
        date_column_formatter=lambda x: x,
        start_time_query="",
        end_time_query="",
    ):

        def is_date_in_range(date_str, start_time_query, end_time_query):
            formatted_date = date_column_formatter(date_str)
            return start_time_query <= formatted_date <= end_time_query

        def get_date_column_index(header, date_column_name):
            columns = header.split(",")
            for idx, col in enumerate(columns):
                if col.strip() == date_column_name:
                    return idx
            return -1

        with open(file_path, "rb") as f:
            f.seek(0, os.SEEK_END)
            end_pointer = f.tell()

            # Read the first line to extract header and determine the date column index
            f.seek(0)
            header = f.readline().decode("utf-8").strip()
            data_columns = header.split(",")
            data_columns.remove(self.date_column)

            date_column_index = get_date_column_index(header, date_column)
            if date_column_index == -1:
                raise ValueError(f"Date column '{date_column}' not found in header")

            map_columns_index = {}
            for col in data_columns:
                column_index = get_date_column_index(header, col)
                if column_index == -1:
                    raise ValueError(f"Column '{col}' not found in header")
                map_columns_index[col] = column_index

            buffer = bytearray()
            pointer_location = end_pointer
            lines_found = 0
            lines_to_skip = skip_lines
            filtered_lines = []

            while pointer_location >= 0 and len(filtered_lines) < n_lines:
                f.seek(pointer_location)
                new_byte = f.read(1)
                if new_byte == b"\n" and pointer_location != end_pointer:
                    lines_found += 1
                    line = buffer[::-1].decode("utf-8").strip()

                    buffer.clear()

                    # Split line into columns
                    columns = line.split(",")
                    if len(columns) - 1 > date_column_index:
                        date_str = columns[date_column_index].strip()
                        formatted_date = date_column_formatter(date_str)

                        d = {"date": formatted_date}
                        for col in data_columns:
                            idx = map_columns_index[col]
                            d[col] = columns[idx]

                        if len(filtered_lines) >= n_lines:
                            break

                        if end_time_query == "now UTC":
                            if lines_found > lines_to_skip:
                                filtered_lines.append(d)
                        else:
                            if is_date_in_range(
                                formatted_date, start_time_query, end_time_query
                            ):
                                if lines_found > lines_to_skip:
                                    filtered_lines.append(d)

                buffer.extend(new_byte)
                pointer_location -= 1

            filtered_lines.reverse()
            return filtered_lines
