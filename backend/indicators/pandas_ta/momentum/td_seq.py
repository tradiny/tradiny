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


class TDSEQ(Indicator):
    disabled = False  # TODO: disabled because "'AnalysisIndicators' object has no attribute 'td_seq'"

    name = "Tom Demark Sequential"
    categories = ["Momentum"]

    columns = ["close"]

    inputs = [
        {"name": "as_int", "space": [0, 1], "default": [1]},
    ]

    outputs = [
        {
            "name": "TD SEQ Up",
            "y_axis": "price",
        },
        {
            "name": "TD SEQ Down",
            "y_axis": "price",
        },
    ]

    def calc(self, data, as_int):
        df = pd.DataFrame(data)
        df.columns = ["Date"] + self.columns
        df.set_index(pd.DatetimeIndex(df["Date"]), inplace=True)
        df[df.columns.difference(["Date"])] = (
            df[df.columns.difference(["Date"])]
            .apply(pd.to_numeric, errors="coerce")
            .astype(np.float64)
        )
        df.ta.td_seq(as_int=bool(as_int), cumulative=True, append=True)
        td_seq_up = df.columns[-2]
        td_seq_down = df.columns[-1]
        df.dropna()
        # help(df.ta)

        return [
            [[r["Date"], r[td_seq_up]] for r in df.to_dict(orient="records")],
            [[r["Date"], r[td_seq_down]] for r in df.to_dict(orient="records")],
        ]
