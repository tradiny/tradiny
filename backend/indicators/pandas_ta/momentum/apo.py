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

from typing import Union
import pandas as pd
import pandas_ta as ta
import numpy as np
import copy


from indicators.data.indicator import Indicator


class APO(Indicator):

    id = "indicators.pandas_ta.momentum.apo.APO"
    name = "Absolute Price Oscillator"
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
        {"name": "fast", "space": list(range(5, 20)), "default": [12]},
        {"name": "slow", "space": list(range(13, 40)), "default": [26]},
        {"name": "mamode", "space": list(range(0, len(mamode))), "default": [9]},
    ]

    outputs = [{"name": "APO", "y_axis": "apo", "type": "line", "color": "green"}]

    def calc(self, data, fast, slow, mamode):
        df = pd.DataFrame(data)
        df.columns = ["Date"] + self.columns
        df.set_index(pd.DatetimeIndex(df["Date"]), inplace=True)
        df[df.columns.difference(["Date"])] = (
            df[df.columns.difference(["Date"])]
            .apply(pd.to_numeric, errors="coerce")
            .astype(np.float64)
        )
        df.ta.apo(
            fast=int(fast),
            slow=int(slow),
            mamode=APO.mamode[int(mamode)],
            cumulative=True,
            append=True,
        )
        out_name = df.columns[-1]
        df.dropna()
        # help(df.ta)

        return [[[r["Date"], r[out_name]] for r in df.to_dict(orient="records")]]
