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


class SQUEEZE(Indicator):
    name = "Squeeze Momentum"
    categories = ["Momentum"]
    mamode = ["ema", "sma"]

    columns = ["high", "low", "close"]

    inputs = [
        {"name": "bb_length", "space": list(range(5, 40)), "default": [20]},
        {"name": "bb_std", "space": [x * 0.5 for x in range(0, 21)], "default": [2]},
        {"name": "kc_length", "space": list(range(5, 40)), "default": [20]},
        {
            "name": "kc_scalar",
            "space": [x * 0.5 for x in range(0, 21)],
            "default": [1.5],
        },
        {"name": "mom_length", "space": list(range(5, 20)), "default": [12]},
        {"name": "mom_smooth", "space": list(range(2, 15)), "default": [6]},
        {"name": "use_tr", "space": [0, 1], "default": [1]},
        {"name": "mamode", "space": list(range(0, len(mamode))), "default": [1]},
    ]

    outputs = [
        {
            "name": "SQZ",
            "y_axis": "sqz",
        },
        {
            "name": "SQZ_ON",
            "y_axis": "sqz_binary",
        },
        {
            "name": "SQZ_OFF",
            "y_axis": "sqz_binary",
        },
        {
            "name": "NO_SQZ",
            "y_axis": "sqz_binary",
        },
    ]

    def calc(
        self,
        data,
        bb_length,
        bb_std,
        kc_length,
        kc_scalar,
        mom_length,
        mom_smooth,
        use_tr,
        mamode,
    ):

        df = pd.DataFrame(data)
        df.columns = ["Date"] + self.columns
        df.set_index(pd.DatetimeIndex(df["Date"]), inplace=True)
        df[df.columns.difference(["Date"])] = (
            df[df.columns.difference(["Date"])]
            .apply(pd.to_numeric, errors="coerce")
            .astype(np.float64)
        )
        df.ta.squeeze(
            bb_length=int(bb_length),
            bb_std=float(bb_std),
            kc_scalar=float(kc_scalar),
            kc_length=int(kc_length),
            mom_length=int(mom_length),
            mom_smooth=int(mom_smooth),
            use_tr=bool(use_tr),
            mamode=SQUEEZE.mamode[int(mamode)],
            cumulative=True,
            append=True,
        )
        sqz = df.columns[-4]
        sqz_on = df.columns[-3]
        sqz_off = df.columns[-2]
        no_sqz = df.columns[-1]
        df.dropna()
        # help(df.ta)

        return [
            [[r["Date"], r[sqz]] for r in df.to_dict(orient="records")],
            [[r["Date"], r[sqz_on]] for r in df.to_dict(orient="records")],
            [[r["Date"], r[sqz_off]] for r in df.to_dict(orient="records")],
            [[r["Date"], r[no_sqz]] for r in df.to_dict(orient="records")],
        ]
