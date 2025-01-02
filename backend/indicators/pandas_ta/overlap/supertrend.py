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


class SUPERTREND(Indicator):
    name = "Supertrend"
    categories = ["Overlap"]

    columns = ["high", "low", "close"]

    inputs = [
        {"name": "length", "space": list(range(2, 300)), "default": [7]},
        {
            "name": "multiplier",
            "space": [x * 0.5 for x in range(0, 21)],
            "default": [3.0],
        },
    ]

    outputs = [
        {
            "name": "SUPERT(trend)",
            "y_axis": "price",
        },
        {
            "name": "SUPERTd(direction)",
            "y_axis": "SUPERTd",
        },
        {
            "name": "SUPERTl(long)",
            "y_axis": "price",
        },
        {
            "name": "SUPERTs(short)",
            "y_axis": "price",
        },
    ]

    def calc(self, data, length, multiplier):
        df = pd.DataFrame(data)
        df.columns = ["Date"] + self.columns
        df.set_index(pd.DatetimeIndex(df["Date"]), inplace=True)
        df[df.columns.difference(["Date"])] = (
            df[df.columns.difference(["Date"])]
            .apply(pd.to_numeric, errors="coerce")
            .astype(np.float64)
        )
        df.ta.supertrend(
            length=int(length),
            multiplier=float(multiplier),
            cumulative=True,
            append=True,
        )
        SUPERT = df.columns[-4]
        SUPERTd = df.columns[-3]
        SUPERTl = df.columns[-2]
        SUPERTs = df.columns[-1]
        df.dropna()
        # help(df.ta)

        return [
            [[r["Date"], r[SUPERT]] for r in df.to_dict(orient="records")],
            [[r["Date"], r[SUPERTd]] for r in df.to_dict(orient="records")],
            [[r["Date"], r[SUPERTl]] for r in df.to_dict(orient="records")],
            [[r["Date"], r[SUPERTs]] for r in df.to_dict(orient="records")],
        ]
