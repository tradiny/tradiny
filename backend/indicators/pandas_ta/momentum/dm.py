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


class DM(Indicator):
    name = "Directional Movement"
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

    columns = ["high", "low"]

    inputs = [
        {"name": "drift", "space": list(range(1, 10)), "default": [1]},
        {"name": "mamode", "space": list(range(0, len(mamode))), "default": [7]},
    ]

    outputs = [
        {
            "name": "DMP (+DM)",
            "y_axis": "dm",
        },
        {
            "name": "DMN (-DM)",
            "y_axis": "dm",
        },
    ]

    def calc(self, data, drift, mamode):
        df = pd.DataFrame(data)
        df.columns = ["Date"] + self.columns
        df.set_index(pd.DatetimeIndex(df["Date"]), inplace=True)
        df[df.columns.difference(["Date"])] = (
            df[df.columns.difference(["Date"])]
            .apply(pd.to_numeric, errors="coerce")
            .astype(np.float64)
        )
        df.ta.dm(
            drift=int(drift),
            mamode=DM.mamode[int(mamode)],
            cumulative=True,
            append=True,
        )
        plus_dm = df.columns[-2]
        minus_dm = df.columns[-1]
        df.dropna()
        # help(df.ta)

        return [
            [[r["Date"], r[plus_dm]] for r in df.to_dict(orient="records")],
            [[r["Date"], r[minus_dm]] for r in df.to_dict(orient="records")],
        ]
