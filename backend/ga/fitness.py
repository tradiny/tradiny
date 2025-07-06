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
import time
import sys
import websocket

import pandas as pd
import pandas_ta as ta


class OscillatorFitness:
    best_fitness = None

    def __init__(
        self,
        source,
        name,
        interval,
        genetic_indicator,
        indicator,
        data_map,
        history,
        ws,
    ):
        self.source = source
        self.name = name
        self.interval = interval
        self.genetic_indicator = genetic_indicator
        self.indicator = indicator
        self.data_map = data_map
        self.history = history
        self.ws = ws

    def receive_message(self, expected_message, data_request, timeout=10):

        try:
            self.ws.send(json.dumps([data_request]))
            start_time = time.time()

            while time.time() - start_time < timeout:
                message = self.ws.recv()

                if message:
                    message = json.loads(message)
                    if message["type"] == expected_message:
                        return message

        except websocket.WebSocketTimeoutException:
            logging.warning(f"Connection timeouted: {e}")
            return None

        except Exception as e:
            logging.error(f"Error in fitness receive_message(): {e}")
            return None

        return None

    def get_func(self):

        data = self.receive_message(
            "data_init",
            {
                "type": "data",
                "source": self.source,
                "name": self.name,
                "interval": self.interval,
                "stream": False,
                "count": self.history + 300,
            },
        )
        if data == None:
            logging.error("Error: cannot get the data")
            return

        high_key = f"{self.source}-{self.name}-{self.interval}-high"
        low_key = f"{self.source}-{self.name}-{self.interval}-low"
        close_key = f"{self.source}-{self.name}-{self.interval}-close"

        df_data = pd.DataFrame(data["data"])

        df_data[high_key] = pd.to_numeric(df_data[high_key], errors="coerce")
        df_data[low_key] = pd.to_numeric(df_data[low_key], errors="coerce")
        df_data[close_key] = pd.to_numeric(df_data[close_key], errors="coerce")

        df_data.dropna(inplace=True)

        df_data.sort_values(by="date", inplace=True)

        df_data["ATR"] = ta.atr(
            df_data[high_key], df_data[low_key], df_data[close_key], length=24
        )

        first_output = ""
        for i, output in enumerate(self.genetic_indicator.outputs):
            first_output = output["name"]
        indicator_id = self.indicator["id"]
        indicator_key = f"{indicator_id}-{first_output}"

        def fitness_func(pygad_instance, solution, solution_idx):
            if not data:
                return -sys.float_info.max

            inputs = {}
            for i, input in enumerate(self.genetic_indicator.inputs):
                inputs[input["name"]] = solution[i]

            indicator_data = self.receive_message(
                "indicator_history",
                {
                    "type": "indicator_history",
                    "id": self.indicator["id"],
                    "indicator": self.indicator,
                    "inputs": inputs,
                    "dataMap": self.data_map,
                    "count": self.history,
                    "render": {},
                },
            )
            if data and indicator_data:
                try:
                    df_indicator_data = pd.DataFrame(indicator_data["data"])
                    df_merged = pd.merge(
                        df_data, df_indicator_data, on="date", how="left"
                    )
                    return self.simulate_trading(df_merged, close_key, indicator_key)
                except Exception as e:
                    raise e

            return -sys.float_info.max

        return fitness_func

    def simulate_trading(self, df, close_key, indicator_key):

        holding = False
        entry_price = 0
        fitness = 0
        trades_count = 0

        for _, row in df.iterrows():
            close_price = float(row[close_key])
            indicator_value = row.get(indicator_key)
            atr_value = row["ATR"]

            # Check buy/sell conditions
            if indicator_value is not None:
                if not holding and indicator_value > 70:
                    holding = True
                    entry_price = close_price
                    trades_count += 1

                elif holding:
                    # Calculate drawdown based on entry price as a monetary difference
                    drawdown = close_price - entry_price
                    max_drawdown_value = -atr_value  # Using ATR as the threshold

                    # Execute sell on either indicator condition or drawdown condition
                    if indicator_value < 30 or drawdown < max_drawdown_value:
                        holding = False
                        profit_loss = close_price - entry_price
                        fitness += profit_loss
                        trades_count += 1

        if trades_count <= 1:
            return -sys.float_info.max

        return fitness
