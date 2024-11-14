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


class PSAR(Indicator):
    name = "Parabolic Stop and Reverse (PSAR)"
    categories = ["Trend"]

    columns = ["high", "low", "close"]

    inputs = [
        {"name": "af0", "space": [x * 0.01 for x in range(1, 25)], "default": [0.02]},
        {"name": "af", "space": [x * 0.01 for x in range(1, 25)], "default": [0.02]},
        {"name": "max_af", "space": [x * 0.1 for x in range(1, 25)], "default": [0.2]},
    ]

    outputs = [
        {
            "name": "Parabolic Stop and Reverse (PSAR) long",
            "y_axis": "price",
        },
        {
            "name": "Parabolic Stop and Reverse (PSAR) short",
            "y_axis": "price",
        },
        {
            "name": "Parabolic Stop and Reverse (PSAR) af",
            "y_axis": "psaraf",
        },
        {
            "name": "Parabolic Stop and Reverse (PSAR) reversal",
            "y_axis": "psarr",
        },
    ]

    def calc(self, data, af0, af, max_af):
        df = pd.DataFrame(data)
        df.columns = ["Date"] + self.columns
        df.set_index(pd.DatetimeIndex(df["Date"]), inplace=True)
        df[df.columns.difference(["Date"])] = (
            df[df.columns.difference(["Date"])]
            .apply(pd.to_numeric, errors="coerce")
            .astype(np.float64)
        )
        df.ta.psar(
            af0=float(af0),
            af=float(af),
            max_af=float(max_af),
            cumulative=True,
            append=True,
        )
        psarl = df.columns[-4]
        psars = df.columns[-3]
        psaraf = df.columns[-2]
        psarr = df.columns[-1]
        df.dropna()
        # help(df.ta)

        return [
            [[r["Date"], r[psarl]] for r in df.to_dict(orient="records")],
            [[r["Date"], r[psars]] for r in df.to_dict(orient="records")],
            [[r["Date"], r[psaraf]] for r in df.to_dict(orient="records")],
            [[r["Date"], r[psarr]] for r in df.to_dict(orient="records")],
        ]
