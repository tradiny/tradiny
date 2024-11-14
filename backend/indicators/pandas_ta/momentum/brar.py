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


class BRAR(Indicator):

    id = "indicators.pandas_ta.momentum.brar.BRAR"
    name = "BRAR"
    categories = ["Momentum"]

    columns = ["open", "high", "low", "close"]

    inputs = [
        {"name": "length", "space": list(range(13, 39)), "default": [26]},
        {"name": "scalar", "space": list(range(50, 150)), "default": [100]},
        {"name": "drift", "space": list(range(1, 10)), "default": [1]},
    ]

    outputs = [
        {"name": "BRAR AR", "y_axis": "brar", "type": "line", "color": "green"},
        {"name": "BRAR BR", "y_axis": "brar", "type": "line", "color": "red"},
    ]

    def calc(self, data, length, scalar, drift):
        df = pd.DataFrame(data)
        df.columns = ["Date"] + self.columns
        df.set_index(pd.DatetimeIndex(df["Date"]), inplace=True)
        df[df.columns.difference(["Date"])] = (
            df[df.columns.difference(["Date"])]
            .apply(pd.to_numeric, errors="coerce")
            .astype(np.float64)
        )
        df.ta.brar(
            length=int(length),
            scalar=float(scalar),
            drift=int(drift),
            cumulative=True,
            append=True,
        )
        brar_ar = df.columns[-2]
        brar_br = df.columns[-1]
        df.dropna()
        # help(df.ta)

        return [
            [[r["Date"], r[brar_ar]] for r in df.to_dict(orient="records")],
            [[r["Date"], r[brar_br]] for r in df.to_dict(orient="records")],
        ]
