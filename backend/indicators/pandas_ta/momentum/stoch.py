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


class STOCH(Indicator):
    name = "Stochastic Oscillator"
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

    columns = ["high", "low", "close"]

    inputs = [
        {"name": "fast_k", "space": list(range(1, 30)), "default": [14]},
        {"name": "slow_k", "space": list(range(0, 12)), "default": [3]},
        {"name": "slow_d", "space": list(range(0, 12)), "default": [3]},
        {"name": "mamode", "space": list(range(0, len(mamode))), "default": [9]},
    ]

    outputs = [
        {
            "name": "Stochastic Oscillator K",
            "y_axis": "stoch",
        },
        {
            "name": "Stochastic Oscillator D",
            "y_axis": "stoch",
        },
    ]

    def calc(self, data, fast_k, slow_k, slow_d, mamode):
        df = pd.DataFrame(data)
        df.columns = ["Date"] + self.columns
        df.set_index(pd.DatetimeIndex(df["Date"]), inplace=True)
        df[df.columns.difference(["Date"])] = (
            df[df.columns.difference(["Date"])]
            .apply(pd.to_numeric, errors="coerce")
            .astype(np.float64)
        )
        df.ta.stoch(
            fast_k=int(fast_k),
            slow_k=int(slow_k),
            slow_d=int(slow_d),
            mamode=STOCH.mamode[int(mamode)],
            cumulative=True,
            append=True,
        )
        stoch_k = df.columns[-3]
        stoch_d = df.columns[-2]
        stoch_h = df.columns[-1]
        df.dropna()
        # help(df.ta)

        return [
            [[r["Date"], r[stoch_k]] for r in df.to_dict(orient="records")],
            [[r["Date"], r[stoch_d]] for r in df.to_dict(orient="records")],
        ]
