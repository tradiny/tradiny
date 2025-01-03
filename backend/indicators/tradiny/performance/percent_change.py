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
import pandas_ta as ta
import numpy as np

from indicators.data.indicator import Indicator


def get_change(previous, current):
    if current == previous:
        return 0.0
    try:
        return (abs(current - previous) / previous) * 100.0
    except ZeroDivisionError:
        return 0.0


class PERCENTCHANGE(Indicator):
    name = "Percent Change Indicator"
    categories = ["Performance"]

    columns = ["close"]

    inputs = [{"name": "length", "space": list(range(1, 300)), "default": [1]}]

    outputs = [
        {
            "name": "Percent Change",
            "y_axis": "percent_change",
        }
    ]

    def calc(self, data, length):
        df = pd.DataFrame(data)
        df.columns = ["Date"] + self.columns
        df.set_index(df["Date"], inplace=True)

        percent_changes = []

        for i in range(int(length), len(df)):
            prev_close = df.iloc[i - int(length)]["close"]
            curr_close = df.iloc[i]["close"]

            if pd.notna(prev_close) and pd.notna(curr_close):
                change = get_change(prev_close, curr_close)
                if prev_close > curr_close:
                    change *= -1

                percent_changes.append([df.index[i], change])

        return [percent_changes]
