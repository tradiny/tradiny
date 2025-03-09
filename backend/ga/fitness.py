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

import websocket
import logging
import json
import time
import pandas as pd
import sys


class OscilatorFitness:
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
        ws_url,
    ):
        self.source = source
        self.name = name
        self.interval = interval
        self.genetic_indicator = genetic_indicator
        self.indicator = indicator
        self.data_map = data_map
        self.history = history
        self.ws_url = ws_url

    def receive_message(self, expected_message, data_request, timeout=10):
        ws = websocket.create_connection(self.ws_url, timeout=timeout)

        try:
            ws.send(json.dumps([data_request]))
            start_time = time.time()

            while time.time() - start_time < timeout:
                message = ws.recv()
                if message:
                    message = json.loads(message)

                    if message["type"] == expected_message:
                        return message

        except websocket.WebSocketTimeoutException:
            return None

        except Exception as e:
            return None

        finally:
            ws.close()

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

        indicator_id = self.indicator["id"]

        first_output = ""
        for i, output in enumerate(self.genetic_indicator.outputs):
            first_output = output["name"]

        def fitness_func(pygad_instance, solution, solution_idx):

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
                    close_key = f"{self.source}-{self.name}-{self.interval}-close"
                    indicator_key = f"{indicator_id}-{first_output}"

                    df_data = pd.DataFrame(data["data"])
                    df_indicator_data = pd.DataFrame(indicator_data["data"])

                    # Merge the dataframes on 'date', performing a left join
                    df_merged = pd.merge(
                        df_data, df_indicator_data, on="date", how="left"
                    )

                    # Sort based on the 'date' column
                    df_merged.sort_values(by="date", inplace=True)

                    return self.simulate_trading(df_merged, close_key, indicator_key)
                except Exception as e:
                    raise e

            return -sys.float_info.max

        return fitness_func

    def simulate_trading(self, df, close_key, indicator_key, max_drawdown_percent=1.0):

        # Initialize variables for simulating trades
        holding = False
        entry_price = 0
        fitness = 0
        trades_count = 0

        for _, row in df.iterrows():
            close_price = float(row[close_key])
            indicator_value = row.get(indicator_key)

            # Check buy/sell conditions
            if indicator_value is not None:
                if not holding and indicator_value > 70:
                    holding = True
                    entry_price = close_price
                    trades_count += 1

                elif holding:
                    # Calculate drawdown from the entry price
                    drawdown = 100 * (entry_price - close_price) / entry_price

                    # Execute sell on either indicator condition or drawdown condition
                    if indicator_value < 30 or drawdown >= max_drawdown_percent:
                        holding = False
                        profit_loss = close_price - entry_price
                        fitness += profit_loss
                        trades_count += 1

        # If trades_count is zero or only made one trade, it can't be a full trade cycle
        if trades_count <= 1:
            return -sys.float_info.max

        if fitness > 0:
            logging.info(f"{indicator_key} profit {fitness}")

        return fitness
