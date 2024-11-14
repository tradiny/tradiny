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


class ALMA(Indicator):

    name = "Arnaud Legoux Moving Average"
    categories = ["Overlap"]

    columns = ["close"]

    inputs = [
        {"name": "length", "space": list(range(2, 300)), "default": [10]},
        {"name": "sigma", "space": [x * 0.5 for x in range(0, 21)], "default": [6.0]},
        {
            "name": "distribution_offset",
            "space": [x * 0.05 for x in range(0, 21)],
            "default": [0.85],
        },
    ]

    outputs = [
        {
            "name": "ALMA",
            "y_axis": "price",
        }
    ]

    def calc(self, data, length, sigma, distribution_offset):

        df = pd.DataFrame(data)
        df.columns = ["Date"] + self.columns
        df.set_index(pd.DatetimeIndex(df["Date"]), inplace=True)
        df[df.columns.difference(["Date"])] = (
            df[df.columns.difference(["Date"])]
            .apply(pd.to_numeric, errors="coerce")
            .astype(np.float64)
        )
        df.ta.alma(
            length=int(length),
            sigma=float(sigma),
            distribution_offset=float(distribution_offset),
            cumulative=True,
            append=True,
        )
        out_name = df.columns[-1]
        df.dropna()
        # help(df.ta)

        return [[[r["Date"], r[out_name]] for r in df.to_dict(orient="records")]]
