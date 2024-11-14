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


class ERI(Indicator):
    name = "Elder Ray Index"
    categories = ["Momentum"]

    columns = ["high", "low", "close"]

    inputs = [{"name": "length", "space": list(range(5, 20)), "default": [13]}]

    outputs = [
        {
            "name": "ER bull power",
            "y_axis": "er",
        },
        {
            "name": "ER bear power",
            "y_axis": "er",
        },
    ]

    def calc(self, data, length):
        df = pd.DataFrame(data)
        df.columns = ["Date"] + self.columns
        df.set_index(pd.DatetimeIndex(df["Date"]), inplace=True)
        df[df.columns.difference(["Date"])] = (
            df[df.columns.difference(["Date"])]
            .apply(pd.to_numeric, errors="coerce")
            .astype(np.float64)
        )
        df.ta.eri(length=int(length), cumulative=True, append=True)
        er_bull = df.columns[-2]
        er_bear = df.columns[-1]
        df.dropna()
        # help(df.ta)

        return [
            [[r["Date"], r[er_bull]] for r in df.to_dict(orient="records")],
            [[r["Date"], r[er_bear]] for r in df.to_dict(orient="records")],
        ]
