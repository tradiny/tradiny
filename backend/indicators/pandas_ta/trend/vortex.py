# This software is licensed under a dual license:
#
# 1. Creative Commons Attribution-NonCommercial (CC BY-NC)
#    for individuals and open source projects.
# 2. Commercial License for business use.
#
# For commercial inquiries, contact: license@tradiny.com
#
# For more details, refer to the LICENSE.md file in the root directory of this project.

import pandas as pd
import pandas_ta as ta
import numpy as np
from indicators.data.indicator import Indicator


class VORTEX(Indicator):
    name = "Vortex"
    categories = ["Trend"]

    columns = ["high", "low", "close"]

    inputs = [{"name": "drift", "space": list(range(1, 10)), "default": [1]}]

    outputs = [
        {
            "name": "Vortex VTXP",
            "y_axis": "vortex",
        },
        {
            "name": "Vortex VTXM",
            "y_axis": "vortex",
        },
    ]

    def calc(self, data, drift):
        df = pd.DataFrame(data)
        df.columns = ["Date"] + self.columns
        df.set_index(pd.DatetimeIndex(df["Date"]), inplace=True)
        df[df.columns.difference(["Date"])] = (
            df[df.columns.difference(["Date"])]
            .apply(pd.to_numeric, errors="coerce")
            .astype(np.float64)
        )
        df.ta.vortex(drift=int(drift), cumulative=True, append=True)
        vortex_vtxp = df.columns[-2]
        vortex_vtxm = df.columns[-1]
        df.dropna()
        # help(df.ta)

        return [
            [[r["Date"], r[vortex_vtxp]] for r in df.to_dict(orient="records")],
            [[r["Date"], r[vortex_vtxm]] for r in df.to_dict(orient="records")],
        ]
