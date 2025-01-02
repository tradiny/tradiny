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


class HWC(Indicator):
    name = "Holt-Winter Channel"
    categories = ["Volatility"]

    columns = ["close"]

    inputs = [
        {"name": "na", "space": [x * 0.1 for x in range(1, 25)], "default": [0.2]},
        {"name": "nb", "space": [x * 0.1 for x in range(1, 25)], "default": [0.2]},
        {"name": "nc", "space": [x * 0.1 for x in range(1, 25)], "default": [0.2]},
        {"name": "nd", "space": [x * 0.1 for x in range(1, 25)], "default": [0.2]},
        {"name": "scalar", "space": list(range(1, 20)), "default": [1]},
    ]

    outputs = [
        {
            "name": "Holt-Winter Channel Mid",
            "y_axis": "price",
        },
        {
            "name": "Holt-Winter Channel Upper",
            "y_axis": "price",
        },
        {
            "name": "Holt-Winter Channel Lower",
            "y_axis": "price",
        },
    ]

    def calc(self, data, na, nb, nc, nd, scalar):
        df = pd.DataFrame(data)
        df.columns = ["Date"] + self.columns
        df.set_index(pd.DatetimeIndex(df["Date"]), inplace=True)
        df[df.columns.difference(["Date"])] = (
            df[df.columns.difference(["Date"])]
            .apply(pd.to_numeric, errors="coerce")
            .astype(np.float64)
        )
        df.ta.hwc(
            na=float(na),
            nb=float(nb),
            nc=float(nc),
            nd=float(nd),
            scalar=float(scalar),
            cumulative=True,
            append=True,
        )
        hwc_mid = df.columns[-3]
        hwc_upper = df.columns[-2]
        hwc_lower = df.columns[-1]
        df.dropna()
        # help(df.ta)

        return [
            [[r["Date"], r[hwc_mid]] for r in df.to_dict(orient="records")],
            [[r["Date"], r[hwc_upper]] for r in df.to_dict(orient="records")],
            [[r["Date"], r[hwc_lower]] for r in df.to_dict(orient="records")],
        ]
