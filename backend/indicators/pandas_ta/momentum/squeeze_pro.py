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


class SQUEEZEPRO(Indicator):
    disabled = False  # TODO: disabled because it does not work with default settings

    name = "Squeeze Momentum PRO"
    categories = ["Momentum"]
    mamode = ["ema", "sma"]

    columns = ["high", "low", "close"]

    inputs = [
        {"name": "bb_length", "space": list(range(5, 40)), "default": [20]},
        {"name": "bb_std", "space": [x * 0.5 for x in range(0, 21)], "default": [2.0]},
        {"name": "kc_length", "space": list(range(5, 40)), "default": [20]},
        {
            "name": "kc_scalar_wide",
            "space": [x * 0.5 for x in range(0, 21)],
            "default": [1.5],
        },
        {
            "name": "kc_scalar_normal",
            "space": [x * 0.5 for x in range(0, 21)],
            "default": [2],
        },
        {
            "name": "kc_scalar_narrow",
            "space": [x * 0.5 for x in range(0, 21)],
            "default": [1],
        },
        {"name": "mom_length", "space": list(range(5, 20)), "default": [12]},
        {"name": "mom_smooth", "space": list(range(2, 15)), "default": [6]},
        {"name": "use_tr", "space": [0, 1], "default": [1]},
        {"name": "mamode", "space": list(range(0, len(mamode))), "default": [1]},
    ]

    outputs = [
        {
            "name": "SQZPRO",
            "y_axis": "sqz_pro",
        },
        {
            "name": "SQZPRO_ON_WIDE",
            "y_axis": "sqz_pro_on_wide",
        },
        {
            "name": "SQZPRO_ON_NORMAL",
            "y_axis": "sqz_pro_on_normal",
        },
        {
            "name": "SQZPRO_ON_NARROW",
            "y_axis": "sqz_pro_on_narrow",
        },
        {
            "name": "SQZPRO_OFF_WIDE",
            "y_axis": "sqz_pro_off_wide",
        },
        {
            "name": "SQZPRO_NO",
            "y_axis": "sqz_pro_no",
        },
    ]

    def calc(
        self,
        data,
        bb_length,
        bb_std,
        kc_length,
        kc_scalar_wide,
        kc_scalar_normal,
        kc_scalar_narrow,
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
        df.ta.squeeze_pro(
            bb_length=int(bb_length),
            bb_std=float(bb_std),
            kc_length=int(kc_length),
            kc_scalar_normal=float(kc_scalar_normal),
            kc_scalar_wide=float(kc_scalar_wide),
            kc_scalar_narrow=float(kc_scalar_narrow),
            mom_length=int(mom_length),
            mom_smooth=int(mom_smooth),
            use_tr=bool(use_tr),
            mamode=SQUEEZEPRO.mamode[int(mamode)],
            cumulative=True,
            append=True,
        )

        nodata = (
            df.columns[-1] == "Volume"
        )  # this esentially means that NO data was added into DF because of bad input values
        if nodata:
            self.log("bad input values of %s" % self.name)
            return self.calc_nan(data)

        sqz_pro = df.columns[-6]
        sqz_pro_on_wide = df.columns[-5]
        sqz_pro_on_normal = df.columns[-4]
        sqz_pro_on_narrow = df.columns[-3]
        sqz_pro_off_wide = df.columns[-2]
        sqz_pro_no = df.columns[-1]
        df.dropna()
        # help(df.ta)

        out = [
            [[r["Date"], r[sqz_pro]] for r in df.to_dict(orient="records")],
            [[r["Date"], r[sqz_pro_on_wide]] for r in df.to_dict(orient="records")],
            [[r["Date"], r[sqz_pro_on_normal]] for r in df.to_dict(orient="records")],
            [[r["Date"], r[sqz_pro_on_narrow]] for r in df.to_dict(orient="records")],
            [[r["Date"], r[sqz_pro_off_wide]] for r in df.to_dict(orient="records")],
            [[r["Date"], r[sqz_pro_no]] for r in df.to_dict(orient="records")],
        ]

        return out
