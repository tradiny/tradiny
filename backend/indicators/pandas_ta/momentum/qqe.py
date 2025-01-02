# This software is licensed under a dual-license model:
# 1. Under the Affero General Public License (AGPL) for open-source use.
# 2. With additional terms tailored to individual users (e.g., traders and investors):
#
#    - Individual users may use this software for personal profit (e.g., trading/investing)
#      without releasing proprietary strategies.
#
#    - Redistribution, public tools, or commercial use require compliance with AGPL
#      or a commercial license. Contact: license@tradiny.com
#
# For full details, see the LICENSE.md file in the root directory of this project.

import pandas as pd
import pandas_ta as ta
import numpy as np

from indicators.data.indicator import Indicator


class QQE(Indicator):
    name = "Quantitative Qualitative Estimation"
    categories = ["Momentum"]
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
        {"name": "length", "space": list(range(5, 25)), "default": [14]},
        {"name": "smooth", "space": list(range(1, 15)), "default": [5]},
        {
            "name": "factor",
            "space": [x * 0.001 for x in range(4200, 4300)],
            "default": [4.236],
        },
        {"name": "mamode", "space": list(range(0, len(mamode))), "default": [9]},
        {"name": "drift", "space": list(range(1, 10)), "default": [1]},
    ]

    outputs = [
        {
            "name": "QQE",
            "y_axis": "qqe",
        },
        {
            "name": "RSI_MA (basis)",
            "y_axis": "qqe",
        },
        {
            "name": "QQEl (long)",
            "y_axis": "qqe",
        },
        {
            "name": "QQEs (short)",
            "y_axis": "qqe",
        },
    ]

    def calc(self, data, length, smooth, factor, mamode, drift):

        df = pd.DataFrame(data)
        df.columns = ["Date"] + self.columns
        df.set_index(pd.DatetimeIndex(df["Date"]), inplace=True)
        df[df.columns.difference(["Date"])] = (
            df[df.columns.difference(["Date"])]
            .apply(pd.to_numeric, errors="coerce")
            .astype(np.float64)
        )
        df.ta.qqe(
            length=int(length),
            smooth=int(smooth),
            factor=float(factor),
            mamode=QQE.mamode[int(mamode)],
            drift=int(drift),
            cumulative=True,
            append=True,
        )
        qqe = df.columns[-4]
        qqe_rsi = df.columns[-3]
        qqe_l = df.columns[-2]
        qqe_s = df.columns[-1]
        # help(df.ta)

        return [
            [[r["Date"], r[qqe]] for r in df.to_dict(orient="records")],
            [[r["Date"], r[qqe_rsi]] for r in df.to_dict(orient="records")],
            [[r["Date"], r[qqe_l]] for r in df.to_dict(orient="records")],
            [[r["Date"], r[qqe_s]] for r in df.to_dict(orient="records")],
        ]
