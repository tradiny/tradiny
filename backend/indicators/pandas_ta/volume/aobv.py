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


class AOBV(Indicator):
    name = "Archer On Balance Volume (AOBV)"
    categories = ["Volume"]

    columns = ["close", "volume"]

    inputs = [
        {"name": "fast", "space": list(range(1, 20)), "default": [4]},
        {"name": "slow", "space": list(range(1, 40)), "default": [12]},
        {"name": "max_lookback", "space": list(range(1, 20)), "default": [2]},
        {"name": "min_lookback", "space": list(range(1, 40)), "default": [2]},
    ]

    outputs = [
        {
            "name": "Archer On Balance Volume (AOBV) Min",
            "y_axis": "obv",
        },
        {
            "name": "Archer On Balance Volume (AOBV) Max",
            "y_axis": "obv",
        },
        {
            "name": "Archer On Balance Volume (AOBV) Fast",
            "y_axis": "obv",
        },
        {
            "name": "Archer On Balance Volume (AOBV) Slow",
            "y_axis": "obv",
        },
        {
            "name": "Archer On Balance Volume (AOBV) AOBV_LR",
            "y_axis": "aobv_binary",
        },
        {
            "name": "Archer On Balance Volume (AOBV) AOBV_SR",
            "y_axis": "aobv_binary",
        },
    ]

    def calc(self, data, fast, slow, max_lookback, min_lookback):
        df = pd.DataFrame(data)
        df.columns = ["Date"] + self.columns
        df.set_index(pd.DatetimeIndex(df["Date"]), inplace=True)
        df[df.columns.difference(["Date"])] = (
            df[df.columns.difference(["Date"])]
            .apply(pd.to_numeric, errors="coerce")
            .astype(np.float64)
        )
        df.ta.aobv(
            fast=int(fast),
            slow=int(slow),
            max_lookback=int(max_lookback),
            min_lookback=int(min_lookback),
            cumulative=True,
            append=True,
        )
        obv_min = df.columns[-6]
        obv_max = df.columns[-5]
        obv_fast = df.columns[-4]
        obv_slow = df.columns[-3]
        aobv_long = df.columns[-2]
        aobv_shot = df.columns[-1]
        df.dropna()
        # help(df.ta)

        return [
            [[r["Date"], r[obv_min]] for r in df.to_dict(orient="records")],
            [[r["Date"], r[obv_max]] for r in df.to_dict(orient="records")],
            [[r["Date"], r[obv_fast]] for r in df.to_dict(orient="records")],
            [[r["Date"], r[obv_slow]] for r in df.to_dict(orient="records")],
            [[r["Date"], r[aobv_long]] for r in df.to_dict(orient="records")],
            [[r["Date"], r[aobv_shot]] for r in df.to_dict(orient="records")],
        ]
