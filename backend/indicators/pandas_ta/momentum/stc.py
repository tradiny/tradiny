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


class STC(Indicator):
    name = "Schaff Trend Cycle"
    categories = ["Momentum"]

    columns = ["close"]

    inputs = [
        {"name": "tclength", "space": list(range(5, 15)), "default": [10]},
        {"name": "fast", "space": list(range(5, 15)), "default": [12]},
        {"name": "slow", "space": list(range(5, 15)), "default": [26]},
        {"name": "factor", "space": [x * 0.5 for x in range(0, 21)], "default": [0.5]},
    ]

    outputs = [
        {
            "name": "STC",
            "y_axis": "stc",
        },
        {
            "name": "STC mac",
            "y_axis": "stc2",
        },
        {
            "name": "STC stoch",
            "y_axis": "stc2",
        },
    ]

    def calc(self, data, tclength, fast, slow, factor):
        df = pd.DataFrame(data)
        df.columns = ["Date"] + self.columns
        df.set_index(pd.DatetimeIndex(df["Date"]), inplace=True)
        df[df.columns.difference(["Date"])] = (
            df[df.columns.difference(["Date"])]
            .apply(pd.to_numeric, errors="coerce")
            .astype(np.float64)
        )
        df.ta.stc(
            tclength=int(tclength),
            fast=int(fast),
            slow=int(slow),
            factor=float(factor),
            cumulative=True,
            append=True,
        )
        stc = df.columns[-3]
        stc_mac = df.columns[-2]
        stc_stoch = df.columns[-1]
        df.dropna()
        # help(df.ta)

        return [
            [[r["Date"], r[stc]] for r in df.to_dict(orient="records")],
            [[r["Date"], r[stc_mac]] for r in df.to_dict(orient="records")],
            [[r["Date"], r[stc_stoch]] for r in df.to_dict(orient="records")],
        ]
