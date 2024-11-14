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


class THERMO(Indicator):
    name = "Elders Thermometer (THERMO)"
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

    columns = ["high", "low"]

    inputs = [
        {"name": "length", "space": list(range(1, 300)), "default": [14]},
        {"name": "mamode", "space": list(range(0, len(mamode))), "default": [1]},
        {"name": "drift", "space": list(range(1, 10)), "default": [1]},
        {"name": "long", "space": [x * 0.1 for x in range(1, 25)], "default": [2]},
        {"name": "short", "space": [x * 0.1 for x in range(1, 25)], "default": [0.5]},
    ]

    outputs = [
        {
            "name": "Elders Thermometer (THERMO)",
            "y_axis": "thermo",
        },
        {
            "name": "Elders Thermometer (THERMO) Ma",
            "y_axis": "thermo",
        },
        {
            "name": "Elders Thermometer (THERMO) Long",
            "y_axis": "thermo_binary",
        },
        {
            "name": "Elders Thermometer (THERMO) Short",
            "y_axis": "thermo_binary",
        },
    ]

    def calc(self, data, length, mamode, drift, long, short):
        df = pd.DataFrame(data)
        df.columns = ["Date"] + self.columns
        df.set_index(pd.DatetimeIndex(df["Date"]), inplace=True)
        df[df.columns.difference(["Date"])] = (
            df[df.columns.difference(["Date"])]
            .apply(pd.to_numeric, errors="coerce")
            .astype(np.float64)
        )
        df.ta.thermo(
            length=int(length),
            mamode=THERMO.mamode[int(mamode)],
            drift=int(drift),
            long=float(long),
            short=float(short),
            cumulative=True,
            append=True,
        )
        thermo = df.columns[-4]
        thermo_ma = df.columns[-3]
        thermo_long = df.columns[-2]
        thermo_short = df.columns[-1]
        df.dropna()
        # help(df.ta)

        return [
            [[r["Date"], r[thermo]] for r in df.to_dict(orient="records")],
            [[r["Date"], r[thermo_ma]] for r in df.to_dict(orient="records")],
            [[r["Date"], r[thermo_long]] for r in df.to_dict(orient="records")],
            [[r["Date"], r[thermo_short]] for r in df.to_dict(orient="records")],
        ]
