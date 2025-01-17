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


class XSIGNALS(Indicator):
    disabled = True  # TODO: missing default values and probably wrong output

    name = "Cross Signals (XSIGNALS)"
    categories = ["Trend"]

    columns = ["signal"]

    inputs = [
        {"name": "xa", "space": [0, 1], "default": [0]},
        {"name": "xb", "space": [0, 1], "default": [0]},
        {"name": "above", "space": [0, 1], "default": [0]},
        {"name": "long", "space": [0, 1], "default": [0]},
        {"name": "asbool", "space": [0, 1], "default": [0]},
        {"name": "trend_reset", "space": [0, 1], "default": [0]},
        {"name": "trend_offset", "space": [0, 1], "default": [0]},
    ]

    outputs = [
        {
            "name": "Cross Signals CS_Trends",
            "y_axis": "price",
        },
        {
            "name": "Cross Signals CS_Trades",
            "y_axis": "price",
        },
        {
            "name": "Cross Signals CS_Entries",
            "y_axis": "price",
        },
        {
            "name": "Cross Signals CS_Exits",
            "y_axis": "price",
        },
    ]

    def calc(self, data, above, long, asbool, trend_reset, trend_offset):
        df = pd.DataFrame(data)
        df.columns = ["Date"] + self.columns
        df.set_index(pd.DatetimeIndex(df["Date"]), inplace=True)
        df[df.columns.difference(["Date"])] = (
            df[df.columns.difference(["Date"])]
            .apply(pd.to_numeric, errors="coerce")
            .astype(np.float64)
        )
        df.ta.xsignals(
            above=bool(above),
            long=bool(long),
            asbool=bool(asbool),
            trend_reset=bool(trend_reset),
            trend_offset=bool(trend_offset),
            cumulative=True,
            append=True,
        )
        cstrends = df.columns[-4]
        cstrades = df.columns[-3]
        csentries = df.columns[-2]
        csexits = df.columns[-1]
        df.dropna()
        # help(df.ta)

        return [
            [[r["Date"], r[cstrends]] for r in df.to_dict(orient="records")],
            [[r["Date"], r[cstrades]] for r in df.to_dict(orient="records")],
            [[r["Date"], r[csentries]] for r in df.to_dict(orient="records")],
            [[r["Date"], r[csexits]] for r in df.to_dict(orient="records")],
        ]
