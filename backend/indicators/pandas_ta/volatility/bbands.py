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


class BBANDS(Indicator):
    name = "Bollinger Bands (BBANDS)"
    categories = ["Volatility"]
    mamode = [
        "dema",
        "ema",
        "fwma",
        "hma",
        "linreg",
        "midpoint",
        "pwma",
        "rma",
        "sinwma",
        "sma",
        "swma",
        "t3," "tema",
        "trima",
        "vidya",
        "wma",
        "zlma",
    ]

    columns = ["close"]

    inputs = [
        {"name": "length", "space": list(range(1, 300)), "default": [5]},
        {"name": "std", "space": [x * 0.5 for x in range(1, 25)], "default": [2.0]},
        {"name": "mamode", "space": list(range(0, len(mamode))), "default": [9]},
    ]
    outputs = [
        {
            "name": "Bollinger Bands (BBANDS) Lower",
            "y_axis": "price",
        },
        {
            "name": "Bollinger Bands (BBANDS) Mid",
            "y_axis": "price",
        },
        {
            "name": "Bollinger Bands (BBANDS) Upper",
            "y_axis": "price",
        },
        {
            "name": "Bollinger Bands (BBANDS) Bandwidth",
            "y_axis": "bbands_bandwidth",
        },
        {
            "name": "Bollinger Bands (BBANDS) Percent",
            "y_axis": "bbands_percent",
        },
    ]

    def calc(self, data, length, std, mamode):
        df = pd.DataFrame(data)
        df.columns = ["Date"] + self.columns
        df.set_index(pd.DatetimeIndex(df["Date"]), inplace=True)
        df[df.columns.difference(["Date"])] = (
            df[df.columns.difference(["Date"])]
            .apply(pd.to_numeric, errors="coerce")
            .astype(np.float64)
        )
        df.ta.bbands(
            length=int(length),
            std=float(std),
            mamode=BBANDS.mamode[int(mamode)],
            cumulative=True,
            append=True,
        )
        bbands_lower = df.columns[-5]
        bbands_mid = df.columns[-4]
        bbands_upper = df.columns[-3]
        bbands_bandwidth = df.columns[-2]
        bbands_percent = df.columns[-1]
        df.dropna()
        # help(df.ta)

        return [
            [[r["Date"], r[bbands_lower]] for r in df.to_dict(orient="records")],
            [[r["Date"], r[bbands_mid]] for r in df.to_dict(orient="records")],
            [[r["Date"], r[bbands_upper]] for r in df.to_dict(orient="records")],
            [[r["Date"], r[bbands_bandwidth]] for r in df.to_dict(orient="records")],
            [[r["Date"], r[bbands_percent]] for r in df.to_dict(orient="records")],
        ]
