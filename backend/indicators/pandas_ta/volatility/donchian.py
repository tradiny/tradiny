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


class DONCHIAN(Indicator):
    name = "Donchian Channels (DC)"
    categories = ["Volatility"]

    columns = ["high", "low"]

    inputs = [
        {"name": "lower_length", "space": list(range(1, 300)), "default": [20]},
        {"name": "upper_length", "space": list(range(1, 300)), "default": [20]},
    ]

    outputs = [
        {
            "name": "Donchian Channels (DC) Lower",
            "y_axis": "price",
        },
        {
            "name": "Donchian Channels (DC) Mid",
            "y_axis": "price",
        },
        {
            "name": "Donchian Channels (DC) Upper",
            "y_axis": "price",
        },
    ]

    def calc(self, data, lower_length, upper_length):
        df = pd.DataFrame(data)
        df.columns = ["Date"] + self.columns
        df.set_index(pd.DatetimeIndex(df["Date"]), inplace=True)
        df[df.columns.difference(["Date"])] = (
            df[df.columns.difference(["Date"])]
            .apply(pd.to_numeric, errors="coerce")
            .astype(np.float64)
        )
        df.ta.donchian(
            lower_length=int(lower_length),
            upper_length=int(upper_length),
            cumulative=True,
            append=True,
        )
        donchian_lower = df.columns[-3]
        donchian_mid = df.columns[-2]
        donchian_upper = df.columns[-1]
        df.dropna()
        # help(df.ta)

        return [
            [[r["Date"], r[donchian_lower]] for r in df.to_dict(orient="records")],
            [[r["Date"], r[donchian_mid]] for r in df.to_dict(orient="records")],
            [[r["Date"], r[donchian_upper]] for r in df.to_dict(orient="records")],
        ]
