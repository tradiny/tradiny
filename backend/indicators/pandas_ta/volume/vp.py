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


class VP(Indicator):
    disabled = True  # TODO: 'AnalysisIndicators' object has no attribute 'vp'

    name = "Volume Profile (VP)"
    categories = ["Volume"]

    columns = ["close", "volume"]

    inputs = [
        {"name": "", "space": list(range(1, 300)), "default": [10]},
        {"name": "percent", "space": list(range(1, 300)), "default": [1]},
    ]

    outputs = [
        {
            "name": "Volume Profile (VP)",
            "y_axis": "vp",
        }
    ]

    def calc(self, data, width, percent):
        df = pd.DataFrame(data)
        df.columns = ["Date"] + self.columns
        df.set_index(pd.DatetimeIndex(df["Date"]), inplace=True)
        df[df.columns.difference(["Date"])] = (
            df[df.columns.difference(["Date"])]
            .apply(pd.to_numeric, errors="coerce")
            .astype(np.float64)
        )
        df.ta.vp(width=int(width), percent=float(percent), cumulative=True, append=True)
        out_name = df.columns[-1]
        df.dropna()
        # help(df.ta)

        return [[[r["Date"], r[out_name]] for r in df.to_dict(orient="records")]]
