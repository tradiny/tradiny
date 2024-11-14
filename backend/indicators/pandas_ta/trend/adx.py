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


class ADX(Indicator):
    name = "ADX"
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
        {"name": "length", "space": list(range(1, 300)), "default": [14]},
        {"name": "lensig", "space": list(range(1, 300)), "default": [14]},
        {"name": "mamode", "space": list(range(0, len(mamode))), "default": [0]},
        {"name": "scalar", "space": list(range(50, 150)), "default": [100]},
        {"name": "drift", "space": list(range(1, 10)), "default": [1]},
    ]

    outputs = [
        {
            "name": "ADX",
            "y_axis": "adx",
        },
        {
            "name": "DMP",
            "y_axis": "adx",
        },
        {
            "name": "DMN",
            "y_axis": "adx",
        },
    ]

    def calc(self, data, length, lensig, mamode, scalar, drift):
        df = pd.DataFrame(data)
        df.columns = ["Date"] + self.columns
        df.set_index(pd.DatetimeIndex(df["Date"]), inplace=True)
        df[df.columns.difference(["Date"])] = (
            df[df.columns.difference(["Date"])]
            .apply(pd.to_numeric, errors="coerce")
            .astype(np.float64)
        )
        df.ta.adx(
            length=int(length),
            lensig=int(lensig),
            scalar=float(scalar),
            drift=int(drift),
            mamode=ADX.mamode[int(mamode)],
            cumulative=True,
            append=True,
        )

        adx = df.columns[-3]
        DMP = df.columns[-2]
        DMN = df.columns[-1]
        df.dropna()
        # help(df.ta)

        return [
            [[r["Date"], r[adx]] for r in df.to_dict(orient="records")],
            [[r["Date"], r[DMP]] for r in df.to_dict(orient="records")],
            [[r["Date"], r[DMN]] for r in df.to_dict(orient="records")],
        ]
