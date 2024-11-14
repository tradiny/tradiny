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


class VWAP(Indicator):
    name = "Volume Weighted Average Price"
    categories = ["Overlap"]
    anchor = [
        "B",
        "C",
        "D",
        "W",
        "M",
        "Q",
        "H",
        "S",
        "N",
        "A",
        "Y",
        "T",
        "L",
        "U",
        "us",
        "min",
    ]

    columns = ["high", "low", "close", "volume"]

    inputs = [
        {"name": "anchor", "space": list(range(0, len(anchor))), "default": [0]},
    ]

    outputs = [
        {
            "name": "VWAP",
            "y_axis": "price",
        }
    ]

    def calc(self, data, anchor):
        df = pd.DataFrame(data)
        df.columns = ["Date"] + self.columns
        df.set_index(pd.DatetimeIndex(df["Date"]), inplace=True)
        df[df.columns.difference(["Date"])] = (
            df[df.columns.difference(["Date"])]
            .apply(pd.to_numeric, errors="coerce")
            .astype(np.float64)
        )
        df.ta.vwap(anchor=VWAP.anchor[int(anchor)], cumulative=True, append=True)
        out_name = df.columns[-1]
        df.dropna()
        # help(df.ta)

        return [[[r["Date"], r[out_name]] for r in df.to_dict(orient="records")]]
