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


class DM(Indicator):
    name = "Directional Movement (DM)"
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

    columns = ["high", "low"]

    inputs = [
        {"name": "drift", "space": list(range(1, 10)), "default": [1]},
        {"name": "mamode", "space": list(range(0, len(mamode))), "default": [7]},
    ]

    outputs = [
        {
            "name": "DMP (+DM)",
            "y_axis": "dm",
        },
        {
            "name": "DMN (-DM)",
            "y_axis": "dm",
        },
    ]

    def calc(self, data, drift, mamode):
        df = pd.DataFrame(data)
        df.columns = ["Date"] + self.columns
        df.set_index(pd.DatetimeIndex(df["Date"]), inplace=True)
        df[df.columns.difference(["Date"])] = (
            df[df.columns.difference(["Date"])]
            .apply(pd.to_numeric, errors="coerce")
            .astype(np.float64)
        )
        df.ta.dm(
            drift=int(drift),
            mamode=DM.mamode[int(mamode)],
            cumulative=True,
            append=True,
        )
        plus_dm = df.columns[-2]
        minus_dm = df.columns[-1]
        df.dropna()
        # help(df.ta)

        return [
            [[r["Date"], r[plus_dm]] for r in df.to_dict(orient="records")],
            [[r["Date"], r[minus_dm]] for r in df.to_dict(orient="records")],
        ]
