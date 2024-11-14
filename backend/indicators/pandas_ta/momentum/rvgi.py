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


class RVGI(Indicator):
    name = "Relative Vigor Index"
    categories = ["Momentum"]

    columns = ["open", "high", "low", "close"]

    inputs = [
        {"name": "length", "space": list(range(5, 30)), "default": [14]},
        {"name": "swma_length", "space": list(range(1, 10)), "default": [4]},
    ]

    outputs = [
        {
            "name": "RVI",
            "y_axis": "rvgi",
        },
        {
            "name": "RVI signal",
            "y_axis": "rvgi",
        },
    ]

    def calc(self, data, length, swma_length):
        df = pd.DataFrame(data)
        df.columns = ["Date"] + self.columns
        df.set_index(pd.DatetimeIndex(df["Date"]), inplace=True)
        df[df.columns.difference(["Date"])] = (
            df[df.columns.difference(["Date"])]
            .apply(pd.to_numeric, errors="coerce")
            .astype(np.float64)
        )
        df.ta.rvgi(
            length=int(length),
            swma_length=int(swma_length),
            cumulative=True,
            append=True,
        )
        rvgi = df.columns[-2]
        rvgi_s = df.columns[-1]
        df.dropna()
        # help(df.ta)

        return [
            [[r["Date"], r[rvgi]] for r in df.to_dict(orient="records")],
            [[r["Date"], r[rvgi_s]] for r in df.to_dict(orient="records")],
        ]
