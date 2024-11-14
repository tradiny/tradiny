# This software is licensed under a dual license:
#
# 1. Creative Commons Attribution-NonCommercial (CC BY-NC)
#    for individuals and open source projects.
# 2. Commercial License for business use.
#
# For commercial inquiries, contact: license@tradiny.com
#
# For more details, refer to the LICENSE.md file in the root directory of this project.

import pandas as pd
import pandas_ta as ta
import numpy as np

from indicators.data.indicator import Indicator


class TSI(Indicator):
    name = "True Strength Index"
    categories = ["Momentum"]
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
        {"name": "fast", "space": list(range(5, 20)), "default": [13]},
        {"name": "slow", "space": list(range(13, 40)), "default": [25]},
        {"name": "drift", "space": list(range(1, 10)), "default": [1]},
        {"name": "mamode", "space": list(range(0, len(mamode))), "default": [1]},
    ]

    outputs = [
        {
            "name": "True Strength Index",
            "y_axis": "tsi",
        },
        {
            "name": "True Strength Index signal",
            "y_axis": "tsi",
        },
    ]

    def calc(self, data, fast, slow, drift, mamode):
        df = pd.DataFrame(data)
        df.columns = ["Date"] + self.columns
        df.set_index(pd.DatetimeIndex(df["Date"]), inplace=True)
        df[df.columns.difference(["Date"])] = (
            df[df.columns.difference(["Date"])]
            .apply(pd.to_numeric, errors="coerce")
            .astype(np.float64)
        )
        df.ta.tsi(
            fast=int(fast),
            slow=int(slow),
            drift=int(drift),
            mamode=TSI.mamode[int(mamode)],
            cumulative=True,
            append=True,
        )
        tsi = df.columns[-2]
        tsi_s = df.columns[-1]
        df.dropna()
        # help(df.ta)

        return [
            [[r["Date"], r[tsi]] for r in df.to_dict(orient="records")],
            [[r["Date"], r[tsi_s]] for r in df.to_dict(orient="records")],
        ]
