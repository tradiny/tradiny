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


class AROON(Indicator):
    name = "Aroon & Aroon Oscillator"
    categories = ["Trend"]

    columns = ["high", "low"]

    inputs = [
        {"name": "length", "space": list(range(1, 300)), "default": [14]},
        {"name": "scalar", "space": list(range(50, 150)), "default": [100]},
    ]

    outputs = [
        {
            "name": "Aroon & Aroon Oscillator Up",
            "y_axis": "aroon",
        },
        {
            "name": "Aroon & Aroon Oscillator Down",
            "y_axis": "aroon",
        },
        {
            "name": "Aroon & Aroon Oscillator Osc",
            "y_axis": "aroon",
        },
    ]

    def calc(self, data, length, scalar):
        df = pd.DataFrame(data)
        df.columns = ["Date"] + self.columns
        df.set_index(pd.DatetimeIndex(df["Date"]), inplace=True)
        df[df.columns.difference(["Date"])] = (
            df[df.columns.difference(["Date"])]
            .apply(pd.to_numeric, errors="coerce")
            .astype(np.float64)
        )
        df.ta.aroon(
            length=int(length), scalar=float(scalar), cumulative=True, append=True
        )
        aroon_up = df.columns[-3]
        aroon_down = df.columns[-2]
        aroon_osc = df.columns[-1]
        df.dropna()
        # help(df.ta)

        return [
            [[r["Date"], r[aroon_up]] for r in df.to_dict(orient="records")],
            [[r["Date"], r[aroon_down]] for r in df.to_dict(orient="records")],
            [[r["Date"], r[aroon_osc]] for r in df.to_dict(orient="records")],
        ]
