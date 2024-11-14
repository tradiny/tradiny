# This software is licensed under a dual license:
#
# 1. Creative Commons Attribution-NonCommercial (CC BY-NC)
#    for individuals and open source projects.
# 2. Commercial License for business use.
#
# For commercial inquiries, contact: license@tradiny.com
#
# For more details, refer to the LICENSE.md file in the root directory of this project.

from typing import Union
import pandas as pd
import pandas_ta as ta
import numpy as np

from indicators.data.indicator import Indicator


class AO(Indicator):

    id = "indicators.pandas_ta.momentum.ao.AO"
    name = "Awesome Oscillator"
    categories = ["Momentum"]

    columns = ["high", "low"]

    inputs = [
        {"name": "fast", "space": list(range(2, 20)), "default": [5]},
        {"name": "slow", "space": list(range(20, 68)), "default": [34]},
    ]

    outputs = [{"name": "AO", "y_axis": "ao", "type": "line", "color": "green"}]

    def calc(self, data, fast, slow):

        df = pd.DataFrame(data)
        df.columns = ["Date"] + self.columns
        df.set_index(pd.DatetimeIndex(df["Date"]), inplace=True)
        df[df.columns.difference(["Date"])] = (
            df[df.columns.difference(["Date"])]
            .apply(pd.to_numeric, errors="coerce")
            .astype(np.float64)
        )
        df.ta.ao(fast=int(fast), slow=int(slow), cumulative=True, append=True)
        out_name = df.columns[-1]
        df.dropna()
        # help(df.ta)

        return [[[r["Date"], r[out_name]] for r in df.to_dict(orient="records")]]
