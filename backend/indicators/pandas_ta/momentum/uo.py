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


class UO(Indicator):
    name = "Ultimate Oscillator (UO)"
    categories = ["Momentum"]

    columns = ["high", "low", "close"]

    inputs = [
        {"name": "fast", "space": list(range(1, 30)), "default": [7]},
        {"name": "medium", "space": list(range(1, 30)), "default": [14]},
        {"name": "slow", "space": list(range(1, 50)), "default": [28]},
        {"name": "fast_k", "space": [x * 0.5 for x in range(0, 21)], "default": [4.0]},
        {
            "name": "medium_k",
            "space": [x * 0.5 for x in range(0, 21)],
            "default": [2.0],
        },
        {"name": "slow_k", "space": [x * 0.5 for x in range(0, 21)], "default": [1.0]},
        {"name": "drift", "space": list(range(1, 10)), "default": [1]},
    ]

    outputs = [
        {
            "name": "Ultimate Oscillator",
            "y_axis": "uo",
        }
    ]

    def calc(self, data, fast, medium, slow, fast_k, medium_k, slow_k, drift):
        df = pd.DataFrame(data)
        df.columns = ["Date"] + self.columns
        df.set_index(pd.DatetimeIndex(df["Date"]), inplace=True)
        df[df.columns.difference(["Date"])] = (
            df[df.columns.difference(["Date"])]
            .apply(pd.to_numeric, errors="coerce")
            .astype(np.float64)
        )
        df.ta.uo(
            fast=int(fast),
            medium=int(medium),
            slow=int(slow),
            fast_k=float(fast_k),
            medium_k=float(medium_k),
            slow_k=float(slow_k),
            drift=int(drift),
            cumulative=True,
            append=True,
        )
        out_name = df.columns[-1]
        df.dropna()
        # help(df.ta)

        return [[[r["Date"], r[out_name]] for r in df.to_dict(orient="records")]]
