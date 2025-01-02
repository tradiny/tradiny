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


class ACCBANDS(Indicator):
    name = "Acceleration Bands (ACCBANDS)"
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
        {"name": "c", "space": list(range(1, 30)), "default": [4]},
        {"name": "mamode", "space": list(range(0, len(mamode))), "default": [9]},
    ]
    outputs = [
        {
            "name": "Acceleration Bands (ACCBANDS) Lower",
            "y_axis": "price",
        },
        {
            "name": "Acceleration Bands (ACCBANDS) Mid",
            "y_axis": "price",
        },
        {
            "name": "Acceleration Bands (ACCBANDS) Upper",
            "y_axis": "price",
        },
    ]

    def calc(self, data, length, c, mamode):
        df = pd.DataFrame(data)
        df.columns = ["Date"] + self.columns
        df.set_index(pd.DatetimeIndex(df["Date"]), inplace=True)
        df[df.columns.difference(["Date"])] = (
            df[df.columns.difference(["Date"])]
            .apply(pd.to_numeric, errors="coerce")
            .astype(np.float64)
        )
        df.ta.accbands(
            length=int(length),
            c=float(c),
            mamode=ACCBANDS.mamode[int(mamode)],
            cumulative=True,
            append=True,
        )
        accbands_lower = df.columns[-3]
        accbands_mid = df.columns[-2]
        accbands_upper = df.columns[-1]
        df.dropna()
        # help(df.ta)

        return [
            [[r["Date"], r[accbands_lower]] for r in df.to_dict(orient="records")],
            [[r["Date"], r[accbands_mid]] for r in df.to_dict(orient="records")],
            [[r["Date"], r[accbands_upper]] for r in df.to_dict(orient="records")],
        ]
