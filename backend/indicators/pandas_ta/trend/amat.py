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


class AMAT(Indicator):
    # TODO check
    name = "Archer Moving Averages Trends (AMAT)"
    categories = ["Trend"]
    mamode = [
        "dema",
        "ema",
        "fwma",
        "hma",
        "linreg",
        "midpoint",
        "pwma",
        "rma",
        "sinwma",
        "sma",
        "swma",
        "t3," "tema",
        "trima",
        "vidya",
        "wma",
        "zlma",
    ]

    columns = ["close"]

    inputs = [
        {"name": "fast", "space": list(range(5, 20)), "default": [8]},
        {"name": "slow", "space": list(range(13, 40)), "default": [21]},
        {"name": "mamode", "space": list(range(0, len(mamode))), "default": [2]},
        {"name": "lookback", "space": list(range(1, 10)), "default": [2]},
    ]

    outputs = [
        {
            "name": "AMAT_LR",
            "y_axis": "price",
        },
        {
            "name": "AMAT_SR",
            "y_axis": "price",
        },
    ]

    def calc(self, data, fast, slow, mamode, lookback):
        df = pd.DataFrame(data)
        df.columns = ["Date"] + self.columns
        df.set_index(pd.DatetimeIndex(df["Date"]), inplace=True)
        df[df.columns.difference(["Date"])] = (
            df[df.columns.difference(["Date"])]
            .apply(pd.to_numeric, errors="coerce")
            .astype(np.float64)
        )
        df.ta.amat(
            fast=int(fast),
            slow=int(slow),
            mamode=AMAT.mamode[int(mamode)],
            lookback=int(lookback),
            cumulative=True,
            append=True,
        )
        AMAT_LR = df.columns[-2]
        AMAT_SR = df.columns[-1]
        df.dropna()
        # help(df.ta)

        return [
            [[r["Date"], r[AMAT_LR]] for r in df.to_dict(orient="records")],
            [[r["Date"], r[AMAT_SR]] for r in df.to_dict(orient="records")],
        ]
