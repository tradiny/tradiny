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


class ZSCORE(Indicator):
    name = "Z Score"
    categories = ["Statistics"]

    columns = ["close"]

    inputs = [
        {"name": "length", "space": list(range(1, 300)), "default": [30]},
        {"name": "std", "space": [x * 0.5 for x in range(2, 25)], "default": [1.0]},
    ]

    outputs = [
        {
            "name": "Z Score",
            "y_axis": "zscore",
        }
    ]

    def calc(self, data, length, std):
        df = pd.DataFrame(data)
        df.columns = ["Date"] + self.columns
        df.set_index(pd.DatetimeIndex(df["Date"]), inplace=True)
        df[df.columns.difference(["Date"])] = (
            df[df.columns.difference(["Date"])]
            .apply(pd.to_numeric, errors="coerce")
            .astype(np.float64)
        )
        df.ta.zscore(length=int(length), std=float(std), cumulative=True, append=True)
        out_name = df.columns[-1]
        df.dropna()
        # help(df.ta)

        return [[[r["Date"], r[out_name]] for r in df.to_dict(orient="records")]]
