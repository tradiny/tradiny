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


class ICHIMOKU(Indicator):
    name = "Ichimoku Kinkō Hyō"
    categories = ["Overlap"]

    columns = ["high", "low", "close"]

    inputs = [
        {"name": "tenkan", "space": list(range(2, 20)), "default": [9]},
        {"name": "kijun", "space": list(range(2, 40)), "default": [26]},
        {"name": "senkou", "space": list(range(25, 76)), "default": [52]},
        {"name": "include_chikou", "space": [0, 1], "default": [1]},
    ]
    outputs = [
        {
            "name": "ICHIMOKU spanA",
            "y_axis": "price",
        },
        {
            "name": "ICHIMOKU spanB",
            "y_axis": "price",
        },
        {
            "name": "ICHIMOKU tenkan_sen",
            "y_axis": "price",
        },
        {
            "name": "ICHIMOKU kijun_sen",
            "y_axis": "price",
        },
        {
            "name": "ICHIMOKU chikou_span",
            "y_axis": "price",
        },
    ]

    def calc(self, data, tenkan, kijun, senkou, include_chikou):
        df = pd.DataFrame(data)
        df.columns = ["Date"] + self.columns
        df.set_index(pd.DatetimeIndex(df["Date"]), inplace=True)
        df[df.columns.difference(["Date"])] = (
            df[df.columns.difference(["Date"])]
            .apply(pd.to_numeric, errors="coerce")
            .astype(np.float64)
        )
        df.ta.ichimoku(
            tenkan=int(tenkan),
            kijun=int(kijun),
            senkou=int(senkou),
            include_chikou=bool(include_chikou),
            cumulative=True,
            append=True,
        )
        span_a = df.columns[-5]
        span_b = df.columns[-4]
        tenkan_sen = df.columns[-3]
        kijun_sen = df.columns[-2]
        chikou_span = df.columns[-1]
        # df.dropna()
        # help(df.ta)

        return [
            [[r["Date"], r[span_a]] for r in df.to_dict(orient="records")],
            [[r["Date"], r[span_b]] for r in df.to_dict(orient="records")],
            [[r["Date"], r[tenkan_sen]] for r in df.to_dict(orient="records")],
            [[r["Date"], r[kijun_sen]] for r in df.to_dict(orient="records")],
            [[r["Date"], r[chikou_span]] for r in df.to_dict(orient="records")],
        ]
