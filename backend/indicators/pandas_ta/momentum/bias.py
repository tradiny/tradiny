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


class BIAS(Indicator):

    id = "indicators.pandas_ta.momentum.bias.BIAS"
    name = "Bias"
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
        {"name": "length", "space": list(range(13, 40)), "default": [26]},
        {"name": "mamode", "space": list(range(0, len(mamode))), "default": [9]},
    ]

    outputs = [{"name": "BIAS", "y_axis": "bias", "type": "line", "color": "green"}]

    def calc(self, data, length, mamode):
        df = pd.DataFrame(data)
        df.columns = ["Date"] + self.columns
        df.set_index(pd.DatetimeIndex(df["Date"]), inplace=True)
        df[df.columns.difference(["Date"])] = (
            df[df.columns.difference(["Date"])]
            .apply(pd.to_numeric, errors="coerce")
            .astype(np.float64)
        )
        df.ta.bias(
            length=int(length),
            mamode=BIAS.mamode[int(mamode)],
            cumulative=True,
            append=True,
        )
        out_name = df.columns[-1]
        df.dropna()
        # help(df.ta)

        return [[[r["Date"], r[out_name]] for r in df.to_dict(orient="records")]]
