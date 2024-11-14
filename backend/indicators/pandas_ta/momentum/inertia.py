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


class INERTIA(Indicator):
    name = "Inertia"
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

    columns = ["close", "high", "low"]

    inputs = [
        {"name": "length", "space": list(range(5, 35)), "default": [20]},
        {"name": "rvi_length", "space": list(range(7, 21)), "default": [14]},
        {"name": "scalar", "space": list(range(50, 150)), "default": [100]},
        {"name": "refined", "space": [0, 1], "default": [0]},
        {"name": "thirds", "space": [0, 1], "default": [0]},
        {"name": "mamode", "space": list(range(0, len(mamode))), "default": [1]},
    ]

    outputs = [
        {
            "name": "INERTIA",
            "y_axis": "inertia",
        }
    ]

    def calc(self, data, length, rvi_length, scalar, refined, thirds, mamode):
        df = pd.DataFrame(data)
        df.columns = ["Date"] + self.columns
        df.set_index(pd.DatetimeIndex(df["Date"]), inplace=True)
        df[df.columns.difference(["Date"])] = (
            df[df.columns.difference(["Date"])]
            .apply(pd.to_numeric, errors="coerce")
            .astype(np.float64)
        )
        df.ta.inertia(
            length=int(length),
            rvi_length=int(rvi_length),
            scalar=float(scalar),
            refined=bool(refined),
            thirds=bool(thirds),
            mamode=INERTIA.mamode[int(mamode)],
            cumulative=True,
            append=True,
        )
        out_name = df.columns[-1]
        df.dropna()
        # help(df.ta)

        return [[[r["Date"], r[out_name]] for r in df.to_dict(orient="records")]]
