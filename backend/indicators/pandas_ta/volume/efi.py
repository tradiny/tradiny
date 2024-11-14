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


class EFI(Indicator):
    name = "Elder" "s Force Index (EFI)"
    categories = ["Volume"]
    mamode = [
        "dema",
        "ema",
        "fwma",
        "hma",
        "linreg",
        "midpoint",
        "pwma",
        "rma",
        "sinwma",
        "sma",
        "swma",
        "t3," "tema",
        "trima",
        "vidya",
        "wma",
        "zlma",
    ]

    columns = ["close", "volume"]

    inputs = [
        {"name": "length", "space": list(range(1, 300)), "default": [13]},
        {"name": "mamode", "space": list(range(0, len(mamode))), "default": [1]},
        {"name": "drift", "space": list(range(1, 10)), "default": [1]},
    ]

    outputs = [
        {
            "name": "Elder" "s Force Index (EFI)",
            "y_axis": "efi",
        }
    ]

    def calc(self, data, length, mamode, drift):
        df = pd.DataFrame(data)
        df.columns = ["Date"] + self.columns
        df.set_index(pd.DatetimeIndex(df["Date"]), inplace=True)
        df[df.columns.difference(["Date"])] = (
            df[df.columns.difference(["Date"])]
            .apply(pd.to_numeric, errors="coerce")
            .astype(np.float64)
        )
        df.ta.efi(
            length=int(length),
            drift=int(drift),
            mamode=EFI.mamode[int(mamode)],
            cumulative=True,
            append=True,
        )
        out_name = df.columns[-1]
        df.dropna()
        # help(df.ta)

        return [[[r["Date"], r[out_name]] for r in df.to_dict(orient="records")]]
