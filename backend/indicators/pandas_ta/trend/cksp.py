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


class CKSP(Indicator):
    name = "Chande Kroll Stop (CKSP)"
    categories = ["Trend"]
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

    columns = ["high", "low", "close"]

    inputs = [
        {"name": "p", "space": list(range(1, 50)), "default": [10]},
        {"name": "x", "space": list(range(1, 50)), "default": [3]},
        {"name": "q", "space": list(range(1, 50)), "default": [20]},
        {"name": "mamode", "space": list(range(0, len(mamode))), "default": [9]},
    ]

    outputs = [
        {
            "name": "Chande Kroll Stop (CKSP) Long",
            "y_axis": "price",
        },
        {
            "name": "Chande Kroll Stop (CKSP) Short",
            "y_axis": "price",
        },
    ]

    def calc(self, data, p, x, q, mamode):
        df = pd.DataFrame(data)
        df.columns = ["Date"] + self.columns
        df.set_index(pd.DatetimeIndex(df["Date"]), inplace=True)
        df[df.columns.difference(["Date"])] = (
            df[df.columns.difference(["Date"])]
            .apply(pd.to_numeric, errors="coerce")
            .astype(np.float64)
        )
        df.ta.cksp(
            p=int(p),
            x=float(x),
            q=int(q),
            mamode=CKSP.mamode[int(mamode)],
            cumulative=True,
            append=True,
        )
        CKSPl = df.columns[-2]
        CKSPs = df.columns[-1]
        df.dropna()
        # help(df.ta)

        return [
            [[r["Date"], r[CKSPl]] for r in df.to_dict(orient="records")],
            [[r["Date"], r[CKSPs]] for r in df.to_dict(orient="records")],
        ]
