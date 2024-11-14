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


class BOP(Indicator):

    id = "indicators.pandas_ta.momentum.bop.BOP"
    name = "Balance of Power"
    categories = ["Momentum"]

    columns = ["open", "high", "low", "close"]

    inputs = [
        {
            "name": "percentage",
            "space": [x * 0.05 for x in range(0, 21)],
            "default": [1],
        },
    ]

    outputs = [{"name": "BOP", "y_axis": "bop", "type": "line", "color": "green"}]

    def calc(self, data, percentage):
        df = pd.DataFrame(data)
        df.columns = ["Date"] + self.columns
        df.set_index(pd.DatetimeIndex(df["Date"]), inplace=True)
        df[df.columns.difference(["Date"])] = (
            df[df.columns.difference(["Date"])]
            .apply(pd.to_numeric, errors="coerce")
            .astype(np.float64)
        )
        df.ta.bop(
            percentage=float(percentage), cumulative=True, append=True
        )  # TODO: percentage agrument missing in bop.py

        out_name = df.columns[-1]
        df.dropna()
        # help(df.ta)

        return [[[r["Date"], r[out_name]] for r in df.to_dict(orient="records")]]
