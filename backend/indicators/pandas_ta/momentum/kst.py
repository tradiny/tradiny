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


class KST(Indicator):
    name = "Know Sure Thing"
    categories = ["Momentum"]

    columns = ["close"]

    inputs = [
        {"name": "roc1", "space": list(range(1, 50)), "default": [10]},
        {"name": "roc2", "space": list(range(1, 50)), "default": [15]},
        {"name": "roc3", "space": list(range(1, 50)), "default": [20]},
        {"name": "roc4", "space": list(range(1, 50)), "default": [30]},
        {"name": "sma1", "space": list(range(1, 50)), "default": [10]},
        {"name": "sma2", "space": list(range(1, 50)), "default": [10]},
        {"name": "sma3", "space": list(range(1, 50)), "default": [10]},
        {"name": "sma4", "space": list(range(1, 50)), "default": [15]},
        {"name": "signal", "space": list(range(1, 20)), "default": [9]},
    ]

    outputs = [
        {
            "name": "Know Sure Thing",
            "y_axis": "kst",
        },
        {
            "name": "Know Sure Thing signal",
            "y_axis": "kst",
        },
    ]

    def calc(self, data, roc1, roc2, roc3, roc4, sma1, sma2, sma3, sma4, signal):
        df = pd.DataFrame(data)
        df.columns = ["Date"] + self.columns
        df.set_index(pd.DatetimeIndex(df["Date"]), inplace=True)
        df[df.columns.difference(["Date"])] = (
            df[df.columns.difference(["Date"])]
            .apply(pd.to_numeric, errors="coerce")
            .astype(np.float64)
        )
        df.ta.kst(
            roc1=int(roc1),
            roc2=int(roc2),
            roc3=int(roc3),
            roc4=int(roc4),
            sma1=int(sma1),
            sma2=int(sma2),
            sma3=int(sma3),
            sma4=int(sma4),
            signal=int(signal),
            cumulative=True,
            append=True,
        )
        kst = df.columns[-2]
        kst_s = df.columns[-1]
        df.dropna()
        # help(df.ta)

        return [
            [[r["Date"], r[kst]] for r in df.to_dict(orient="records")],
            [[r["Date"], r[kst_s]] for r in df.to_dict(orient="records")],
        ]
