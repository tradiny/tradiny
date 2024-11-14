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


class QUANTILE(Indicator):
    name = "Quantile"
    categories = ["Statistics"]

    columns = ["close"]

    inputs = [
        {"name": "length", "space": list(range(1, 300)), "default": [30]},
        {
            "name": "quantile",
            "space": [x * 0.05 for x in range(1, 20)],
            "default": [0.5],
        },
    ]

    outputs = [
        {
            "name": "Quantile",
            "y_axis": "price",
        }
    ]

    def calc(self, data, length, quantile):
        df = pd.DataFrame(data)
        df.columns = ["Date"] + self.columns
        df.set_index(pd.DatetimeIndex(df["Date"]), inplace=True)
        df[df.columns.difference(["Date"])] = (
            df[df.columns.difference(["Date"])]
            .apply(pd.to_numeric, errors="coerce")
            .astype(np.float64)
        )
        df.ta.quantile(
            length=int(length), quantile=float(quantile), cumulative=True, append=True
        )
        out_name = df.columns[-1]
        df.dropna()
        # help(df.ta)

        return [[[r["Date"], r[out_name]] for r in df.to_dict(orient="records")]]
