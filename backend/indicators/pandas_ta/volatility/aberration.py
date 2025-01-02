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


class ABERRATION(Indicator):
    name = "Aberration (ABER)"
    categories = ["Volatility"]

    columns = ["high", "low", "close"]

    inputs = [
        {"name": "length", "space": list(range(1, 300)), "default": [14]},
        {"name": "atr_length", "space": list(range(1, 300)), "default": [1]},
    ]
    outputs = [
        {
            "name": "Aberration (ABER) ABER_ZG",
            "y_axis": "price",
        },
        {
            "name": "Aberration (ABER) ABER_SG",
            "y_axis": "price",
        },
        {
            "name": "Aberration (ABER) ABER_XG",
            "y_axis": "price",
        },
        {
            "name": "Aberration (ABER) ABER_ATR",
            "y_axis": "aberration_atr",
        },
    ]

    def calc(self, data, length, atr_length):
        df = pd.DataFrame(data)
        df.columns = ["Date"] + self.columns
        df.set_index(pd.DatetimeIndex(df["Date"]), inplace=True)
        df[df.columns.difference(["Date"])] = (
            df[df.columns.difference(["Date"])]
            .apply(pd.to_numeric, errors="coerce")
            .astype(np.float64)
        )
        df.ta.aberration(
            length=int(length), atr_length=int(atr_length), cumulative=True, append=True
        )
        aberration_zg = df.columns[-4]
        aberration_sg = df.columns[-3]
        aberration_xg = df.columns[-2]
        aberration_atr = df.columns[-1]
        df.dropna()
        # help(df.ta)

        return [
            [[r["Date"], r[aberration_zg]] for r in df.to_dict(orient="records")],
            [[r["Date"], r[aberration_sg]] for r in df.to_dict(orient="records")],
            [[r["Date"], r[aberration_xg]] for r in df.to_dict(orient="records")],
            [[r["Date"], r[aberration_atr]] for r in df.to_dict(orient="records")],
        ]
