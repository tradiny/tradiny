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


class TEMA(Indicator):
    name = "Triple Exponential Moving Average"
    categories = ["Overlap"]

    columns = ["close"]

    inputs = [{"name": "length", "space": list(range(2, 300)), "default": [10]}]

    outputs = [
        {
            "name": "TEMA",
            "y_axis": "price",
        }
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
        df.ta.tema(length=int(length), cumulative=True, append=True)
        out_name = df.columns[-1]
        df.dropna()
        # help(df.ta)

        return [[[r["Date"], r[out_name]] for r in df.to_dict(orient="records")]]
