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


class SMI(Indicator):
    name = "SMI Ergodic Indicator"
    categories = ["Momentum"]

    columns = ["close"]

    inputs = [
        {"name": "fast", "space": list(range(1, 15)), "default": [5]},
        {"name": "slow", "space": list(range(13, 40)), "default": [20]},
        {"name": "signal", "space": list(range(1, 20)), "default": [5]},
        {"name": "scalar", "space": list(range(0, 15)), "default": [1]},
    ]

    outputs = [
        {
            "name": "SMI",
            "y_axis": "smi",
        },
        {
            "name": "SMI signal",
            "y_axis": "smi",
        },
        {
            "name": "SMI oscilator",
            "y_axis": "smi",
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
        df.ta.smi(
            fast=int(fast),
            slow=int(slow),
            signal=int(signal),
            scalar=float(scalar),
            cumulative=True,
            append=True,
        )
        smi = df.columns[-3]
        smi_s = df.columns[-2]
        smi_o = df.columns[-1]
        df.dropna()
        # help(df.ta)

        return [
            [[r["Date"], r[smi]] for r in df.to_dict(orient="records")],
            [[r["Date"], r[smi_s]] for r in df.to_dict(orient="records")],
            [[r["Date"], r[smi_o]] for r in df.to_dict(orient="records")],
        ]
