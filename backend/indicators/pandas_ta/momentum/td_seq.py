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


class TDSEQ(Indicator):
    disabled = False  # TODO: disabled because "'AnalysisIndicators' object has no attribute 'td_seq'"

    name = "Tom Demark Sequential (TDSEQ)"
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
