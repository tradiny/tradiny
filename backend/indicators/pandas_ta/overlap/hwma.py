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


class HWMA(Indicator):
    name = "HWMA (Holt-Winter Moving Average)"
    categories = ["Overlap"]

    columns = ["close"]

    inputs = [
        {"name": "na", "space": [x * 0.05 for x in range(0, 21)], "default": [0.2]},
        {"name": "nb", "space": [x * 0.05 for x in range(0, 21)], "default": [0.1]},
        {"name": "nc", "space": [x * 0.05 for x in range(0, 21)], "default": [0.1]},
    ]

    outputs = [
        {
            "name": "HWMA",
            "y_axis": "price",
        }
    ]

    def calc(self, data, na, nb, nc):
        df = pd.DataFrame(data)
        df.columns = ["Date"] + self.columns
        df.set_index(pd.DatetimeIndex(df["Date"]), inplace=True)
        df[df.columns.difference(["Date"])] = (
            df[df.columns.difference(["Date"])]
            .apply(pd.to_numeric, errors="coerce")
            .astype(np.float64)
        )
        df.ta.hwma(
            na=float(na), nb=float(nb), nc=float(nc), cumulative=True, append=True
        )
        out_name = df.columns[-1]
        df.dropna()
        # help(df.ta)

        return [[[r["Date"], r[out_name]] for r in df.to_dict(orient="records")]]
