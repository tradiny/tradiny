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


class KC(Indicator):
    name = "Keltner Channels (KC)"
    categories = ["Volatility"]
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
        {"name": "length", "space": list(range(1, 300)), "default": [20]},
        {"name": "mamode", "space": list(range(0, len(mamode))), "default": [1]},
        {"name": "scalar", "space": list(range(1, 50)), "default": [2]},
    ]

    outputs = [
        {
            "name": "Keltner Channels (KC) Lower",
            "y_axis": "price",
        },
        {
            "name": "Keltner Channels (KC) Basis",
            "y_axis": "price",
        },
        {
            "name": "Keltner Channels (KC) Upper",
            "y_axis": "price",
        },
    ]

    def calc(self, data, length, mamode, scalar):
        df = pd.DataFrame(data)
        df.columns = ["Date"] + self.columns
        df.set_index(pd.DatetimeIndex(df["Date"]), inplace=True)
        df[df.columns.difference(["Date"])] = (
            df[df.columns.difference(["Date"])]
            .apply(pd.to_numeric, errors="coerce")
            .astype(np.float64)
        )
        df.ta.kc(
            length=int(length),
            scalar=float(scalar),
            mamode=KC.mamode[int(mamode)],
            cumulative=True,
            append=True,
        )
        kc_lower = df.columns[-3]
        kc_basis = df.columns[-2]
        kc_upper = df.columns[-1]
        # df.dropna()
        # help(df.ta)

        return [
            [[r["Date"], r[kc_lower]] for r in df.to_dict(orient="records")],
            [[r["Date"], r[kc_basis]] for r in df.to_dict(orient="records")],
            [[r["Date"], r[kc_upper]] for r in df.to_dict(orient="records")],
        ]
