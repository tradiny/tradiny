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


class PVO(Indicator):
    name = "Percentage Volume Oscillator"
    categories = ["Momentum"]

    columns = ["volume"]

    inputs = [
        {"name": "fast", "space": list(range(5, 20)), "default": [12]},
        {"name": "slow", "space": list(range(13, 40)), "default": [26]},
        {"name": "signal", "space": list(range(1, 20)), "default": [9]},
        {"name": "scalar", "space": list(range(50, 150)), "default": [100]},
    ]

    outputs = [
        {
            "name": "PVO",
            "y_axis": "pvo",
        },
        {
            "name": "PVO signal",
            "y_axis": "pvo",
        },
        {
            "name": "PVO histogram",
            "y_axis": "pvo",
        },
    ]

    def calc(self, data, fast, slow, signal, scalar):
        df = pd.DataFrame(data)
        df.columns = ["Date"] + self.columns
        df.set_index(pd.DatetimeIndex(df["Date"]), inplace=True)
        df[df.columns.difference(["Date"])] = (
            df[df.columns.difference(["Date"])]
            .apply(pd.to_numeric, errors="coerce")
            .astype(np.float64)
        )
        df.ta.pvo(
            fast=int(fast),
            slow=int(slow),
            signal=int(signal),
            scalar=float(scalar),
            cumulative=True,
            append=True,
        )
        pvo = df.columns[-3]
        pvo_h = df.columns[-2]
        pvo_s = df.columns[-1]
        df.dropna()
        # help(df.ta)

        return [
            [[r["Date"], r[pvo]] for r in df.to_dict(orient="records")],
            [[r["Date"], r[pvo_s]] for r in df.to_dict(orient="records")],
            [[r["Date"], r[pvo_h]] for r in df.to_dict(orient="records")],
        ]
