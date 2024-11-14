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


class PVI(Indicator):
    name = "Positive Volume Index (PVI)"
    categories = ["Volume"]

    columns = ["close", "volume"]

    inputs = [
        {"name": "length", "space": list(range(1, 300)), "default": [1]},
        {"name": "initial", "space": list(range(500, 3000, 5)), "default": [1000]},
    ]

    outputs = [
        {
            "name": "Positive Volume Index (PVI)",
            "y_axis": "pvi",
        }
    ]

    def calc(self, data, length, initial):
        df = pd.DataFrame(data)
        df.columns = ["Date"] + self.columns
        df.set_index(pd.DatetimeIndex(df["Date"]), inplace=True)
        df[df.columns.difference(["Date"])] = (
            df[df.columns.difference(["Date"])]
            .apply(pd.to_numeric, errors="coerce")
            .astype(np.float64)
        )
        df.ta.pvi(
            length=int(length), initial=int(initial), cumulative=True, append=True
        )
        out_name = df.columns[-1]
        df.dropna()
        # help(df.ta)

        return [[[r["Date"], r[out_name]] for r in df.to_dict(orient="records")]]
