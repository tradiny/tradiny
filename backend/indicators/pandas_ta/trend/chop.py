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


class CHOP(Indicator):
    name = "Choppiness Index (CHOP)"
    categories = ["Trend"]

    columns = ["high", "low", "close"]

    inputs = [
        {"name": "length", "space": list(range(1, 300)), "default": [14]},
        {"name": "atr_length", "space": list(range(1, 300)), "default": [1]},
        {"name": "scalar", "space": list(range(50, 150)), "default": [100]},
        {"name": "drift", "space": list(range(1, 10)), "default": [1]},
    ]

    outputs = [
        {
            "name": "Choppiness Index (CHOP)",
            "y_axis": "chop",
        }
    ]

    def calc(self, data, length, atr_length, scalar, drift):
        df = pd.DataFrame(data)
        df.columns = ["Date"] + self.columns
        df.set_index(pd.DatetimeIndex(df["Date"]), inplace=True)
        df[df.columns.difference(["Date"])] = (
            df[df.columns.difference(["Date"])]
            .apply(pd.to_numeric, errors="coerce")
            .astype(np.float64)
        )
        df.ta.chop(
            length=int(length),
            atr_length=int(atr_length),
            scalar=float(scalar),
            drift=int(drift),
            cumulative=True,
            append=True,
        )
        out_name = df.columns[-1]
        df.dropna()
        # help(df.ta)

        return [[[r["Date"], r[out_name]] for r in df.to_dict(orient="records")]]
