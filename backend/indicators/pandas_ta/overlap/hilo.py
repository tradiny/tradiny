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


class HILO(Indicator):
    name = "Gann HiLo"
    categories = ["Overlap"]
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

    columns = ["high", "low", "close"]

    inputs = [
        {"name": "high_length", "space": list(range(1, 26)), "default": [13]},
        {"name": "low_length", "space": list(range(10, 34)), "default": [21]},
        {"name": "mamode", "space": list(range(0, len(mamode))), "default": [9]},
    ]

    outputs = [
        {
            "name": "HILO",
            "y_axis": "price",
        },
        {
            "name": "HILOl (long)",
            "y_axis": "price",
        },
        {
            "name": "HILOs (short)",
            "y_axis": "price",
        },
    ]

    def calc(self, data, high_length, low_length, mamode):
        df = pd.DataFrame(data)
        df.columns = ["Date"] + self.columns
        df.set_index(pd.DatetimeIndex(df["Date"]), inplace=True)
        df[df.columns.difference(["Date"])] = (
            df[df.columns.difference(["Date"])]
            .apply(pd.to_numeric, errors="coerce")
            .astype(np.float64)
        )
        df.ta.hilo(
            high_length=int(high_length),
            low_length=int(low_length),
            mamode=HILO.mamode[int(mamode)],
            cumulative=True,
            append=True,
        )
        hilo = df.columns[-3]
        hilol = df.columns[-2]
        hilos = df.columns[-1]
        df.dropna()
        # help(df.ta)

        return [
            [[r["Date"], r[hilo]] for r in df.to_dict(orient="records")],
            [[r["Date"], r[hilol]] for r in df.to_dict(orient="records")],
            [[r["Date"], r[hilos]] for r in df.to_dict(orient="records")],
        ]
