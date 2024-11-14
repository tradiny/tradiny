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


class FISHER(Indicator):
    name = "Fisher Transform"
    categories = ["Momentum"]

    columns = ["high", "low"]

    inputs = [
        {"name": "length", "space": list(range(5, 15)), "default": [9]},
        {"name": "signal", "space": list(range(1, 52)), "default": [1]},
    ]

    outputs = [
        {
            "name": "FISHER",
            "y_axis": "fisher",
        },
        {
            "name": "FISHER Shift",
            "y_axis": "fisher",
        },
    ]

    def calc(self, data, length, signal):
        df = pd.DataFrame(data)
        df.columns = ["Date"] + self.columns
        df.set_index(pd.DatetimeIndex(df["Date"]), inplace=True)
        df[df.columns.difference(["Date"])] = (
            df[df.columns.difference(["Date"])]
            .apply(pd.to_numeric, errors="coerce")
            .astype(np.float64)
        )
        df.ta.fisher(
            length=int(length), signal=int(signal), cumulative=True, append=True
        )
        fisher = df.columns[-2]
        fisher_s = df.columns[-1]
        df.dropna()
        # help(df.ta)

        return [
            [[r["Date"], r[fisher]] for r in df.to_dict(orient="records")],
            [[r["Date"], r[fisher_s]] for r in df.to_dict(orient="records")],
        ]
