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


class MACD(Indicator):
    name = "Moving Average, Convergence/Divergence (MACD)"
    categories = ["Momentum"]

    columns = ["close"]

    inputs = [
        {"name": "fast", "space": list(range(5, 20)), "default": [12]},
        {"name": "slow", "space": list(range(5, 50)), "default": [26]},
        {"name": "signal", "space": list(range(1, 20)), "default": [9]},
    ]

    outputs = [
        {
            "name": "MACD",
            "y_axis": "macd",
        },
        {
            "name": "MACD signal",
            "y_axis": "macd",
        },
        {
            "name": "MACD histogram",
            "y_axis": "macd",
        },
    ]

    def calc(self, data, fast, slow, signal):
        df = pd.DataFrame(data)
        df.columns = ["Date"] + self.columns
        df.set_index(pd.DatetimeIndex(df["Date"]), inplace=True)
        df[df.columns.difference(["Date"])] = (
            df[df.columns.difference(["Date"])]
            .apply(pd.to_numeric, errors="coerce")
            .astype(np.float64)
        )
        df.ta.macd(
            fast=int(fast),
            slow=int(slow),
            signal=int(signal),
            cumulative=True,
            append=True,
        )
        macd = df.columns[-3]
        macd_s = df.columns[-2]
        macd_h = df.columns[-1]
        df.dropna()
        # help(df.ta)

        return [
            [[r["Date"], r[macd]] for r in df.to_dict(orient="records")],
            [[r["Date"], r[macd_s]] for r in df.to_dict(orient="records")],
            [[r["Date"], r[macd_h]] for r in df.to_dict(orient="records")],
        ]
