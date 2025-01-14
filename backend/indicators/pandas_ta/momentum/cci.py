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


class CCI(Indicator):

    id = "indicators.pandas_ta.momentum.cci.CCI"
    name = "Commodity Channel Index (CCI)"
    categories = ["Momentum"]

    columns = ["high", "low", "close"]

    inputs = [
        {"name": "length", "space": list(range(7, 22)), "default": [14]},
        {"name": "c", "space": [x * 0.005 for x in range(0, 21)], "default": [0.015]},
    ]

    outputs = [{"name": "CCI", "y_axis": "cci", "type": "line", "color": "green"}]

    def calc(self, data, length, c):
        df = pd.DataFrame(data)
        df.columns = ["Date"] + self.columns
        df.set_index(pd.DatetimeIndex(df["Date"]), inplace=True)
        df[df.columns.difference(["Date"])] = (
            df[df.columns.difference(["Date"])]
            .apply(pd.to_numeric, errors="coerce")
            .astype(np.float64)
        )
        df.ta.cci(length=int(length), c=float(c), cumulative=True, append=True)
        out_name = df.columns[-1]
        df.dropna()
        # help(df.ta)

        return [[[r["Date"], r[out_name]] for r in df.to_dict(orient="records")]]
