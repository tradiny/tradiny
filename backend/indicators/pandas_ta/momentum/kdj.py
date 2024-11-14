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


class KDJ(Indicator):
    name = "KDJ"
    categories = ["Momentum"]

    columns = ["high", "low", "close"]

    inputs = [
        {"name": "length", "space": list(range(5, 15)), "default": [9]},
        {"name": "signal", "space": list(range(0, 10)), "default": [3]},
    ]

    outputs = [
        {
            "name": "KDJ K",
            "y_axis": "kdj",
        },
        {
            "name": "KDJ D",
            "y_axis": "kdj",
        },
        {
            "name": "KDJ J",
            "y_axis": "kdj",
        },
    ]

    def calc(self, data, length, signal):
        df = pd.DataFrame(data)
        df.columns = ["Date"] + self.columns
        df.set_index(pd.DatetimeIndex(df["Date"]), inplace=True)
        df[df.columns.difference(["Date"])] = (
            df[df.columns.difference(["Date"])]
            .apply(pd.to_numeric, errors="coerce")
            .astype(np.float64)
        )
        df.ta.kdj(length=int(length), signal=int(signal), cumulative=True, append=True)
        kdj_k = df.columns[-3]
        kdj_d = df.columns[-2]
        kdj_j = df.columns[-1]
        df.dropna()
        # help(df.ta)

        return [
            [[r["Date"], r[kdj_k]] for r in df.to_dict(orient="records")],
            [[r["Date"], r[kdj_d]] for r in df.to_dict(orient="records")],
            [[r["Date"], r[kdj_j]] for r in df.to_dict(orient="records")],
        ]
