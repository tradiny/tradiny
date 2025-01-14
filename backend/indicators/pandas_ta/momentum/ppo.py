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


class PPO(Indicator):
    name = "Percentage Price Oscillator (PPO)"
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
        {"name": "fast", "space": list(range(2, 20)), "default": [12]},
        {"name": "slow", "space": list(range(10, 40)), "default": [26]},
        {"name": "scalar", "space": list(range(50, 150)), "default": [100]},
        {"name": "mamode", "space": list(range(0, len(mamode))), "default": [9]},
    ]

    outputs = [
        {
            "name": "PPO",
            "y_axis": "ppo",
        },
        {
            "name": "PPO signal",
            "y_axis": "ppo",
        },
        {
            "name": "PPO histogram",
            "y_axis": "ppo",
        },
    ]

    def calc(self, data, fast, slow, scalar, mamode):

        df = pd.DataFrame(data)
        df.columns = ["Date"] + self.columns
        df.set_index(pd.DatetimeIndex(df["Date"]), inplace=True)
        df[df.columns.difference(["Date"])] = (
            df[df.columns.difference(["Date"])]
            .apply(pd.to_numeric, errors="coerce")
            .astype(np.float64)
        )
        df.ta.ppo(
            fast=int(fast),
            slow=int(slow),
            scalar=float(scalar),
            mamode=PPO.mamode[int(mamode)],
            cumulative=True,
            append=True,
        )
        ppo = df.columns[-3]
        ppo_s = df.columns[-2]
        ppo_h = df.columns[-1]
        df.dropna()
        # help(df.ta)

        return [
            [[r["Date"], r[ppo]] for r in df.to_dict(orient="records")],
            [[r["Date"], r[ppo_s]] for r in df.to_dict(orient="records")],
            [[r["Date"], r[ppo_h]] for r in df.to_dict(orient="records")],
        ]
