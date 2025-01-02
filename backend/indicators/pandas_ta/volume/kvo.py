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


class KVO(Indicator):
    name = "Klinger Volume Oscillator (KVO)"
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

    columns = ["high", "low", "close", "volume"]

    inputs = [
        {"name": "fast", "space": list(range(5, 20)), "default": [34]},
        {"name": "slow", "space": list(range(13, 40)), "default": [55]},
        {"name": "signal", "space": list(range(1, 20)), "default": [13]},
        {"name": "mamode", "space": list(range(0, len(mamode))), "default": [1]},
    ]

    outputs = [
        {
            "name": "Klinger Volume Oscillator (KVO)",
            "y_axis": "kvo",
        },
        {
            "name": "Klinger Volume Oscillator (KVO) Signal",
            "y_axis": "kvo",
        },
    ]

    def calc(self, data, fast, slow, signal, mamode):
        df = pd.DataFrame(data)
        df.columns = ["Date"] + self.columns
        df.set_index(pd.DatetimeIndex(df["Date"]), inplace=True)
        df[df.columns.difference(["Date"])] = (
            df[df.columns.difference(["Date"])]
            .apply(pd.to_numeric, errors="coerce")
            .astype(np.float64)
        )
        df.ta.kvo(
            fast=int(fast),
            slow=int(slow),
            signal=int(signal),
            mamode=KVO.mamode[int(mamode)],
            cumulative=True,
            append=True,
        )
        kvo = df.columns[-2]
        kvo_signal = df.columns[-1]
        df.dropna()
        # help(df.ta)

        return [
            [[r["Date"], r[kvo]] for r in df.to_dict(orient="records")],
            [[r["Date"], r[kvo_signal]] for r in df.to_dict(orient="records")],
        ]
