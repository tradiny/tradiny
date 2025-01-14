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


class TSIGNALS(Indicator):
    # TODO check

    name = "Trend Signals (TSIGNALS)"
    categories = ["Trend"]

    columns = ["trend"]

    inputs = [
        {"name": "as_bool", "space": [0, 1], "default": [0]},
        {"name": "trend_reset", "space": list(range(0, 20)), "default": [0]},
        {"name": "trend_offset", "space": list(range(0, 20)), "default": [0]},
        {"name": "drift", "space": list(range(1, 10)), "default": [1]},
    ]

    outputs = [
        {
            "name": "TS_Trends",
            "y_axis": "price",
        },
        # {
        #     'name': 'TS_Trades',
        #     'y_axis': 'price',
        # },
        # {
        #     'name': 'TS_Entries',
        #     'y_axis': 'price',
        # },
        # {
        #     'name': 'TS_Exits',
        #     'y_axis': 'price',
        # },
    ]

    def calc(self, data, as_bool, trend_reset, trend_offset, drift):
        df = pd.DataFrame(data)
        df.columns = ["Date"] + self.columns
        df.set_index(pd.DatetimeIndex(df["Date"]), inplace=True)
        df[df.columns.difference(["Date"])] = (
            df[df.columns.difference(["Date"])]
            .apply(pd.to_numeric, errors="coerce")
            .astype(np.float64)
        )
        df.ta.tsignals(
            as_bool=bool(as_bool),
            trend_reset=int(trend_reset),
            trend_offset=int(trend_offset),
            drift=int(drift),
            cumulative=True,
            append=True,
        )

        tstrends = df.columns[-1]
        # tstrades = df.columns[-3]
        # tsentries = df.columns[-2]
        # tsexits = df.columns[-1]
        df.dropna()
        # help(df.ta)

        return [
            [[r["Date"], r[tstrends]] for r in df.to_dict(orient="records")],
            # [[r['Date'], r[tstrades]] for r in df.to_dict(orient='records')],
            # [[r['Date'], r[tsentries]] for r in df.to_dict(orient='records')],
            # [[r['Date'], r[tsexits]] for r in df.to_dict(orient='records')]
        ]
