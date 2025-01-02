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


class STOCHRSI(Indicator):
    name = "Stochastic RSI Oscillator"
    categories = ["Momentum"]
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

    columns = ["close"]

    inputs = [
        {"name": "length", "space": list(range(5, 30)), "default": [14]},
        {"name": "rsi_length", "space": list(range(5, 30)), "default": [14]},
        {"name": "k", "space": list(range(0, 10)), "default": [3]},
        {"name": "d", "space": list(range(0, 10)), "default": [3]},
        {"name": "mamode", "space": list(range(0, len(mamode))), "default": [1]},
    ]

    outputs = [
        {
            "name": "Stochastic RSI Oscillator K",
            "y_axis": "stoch_rsi",
        },
        {
            "name": "Stochastic RSI Oscillator D",
            "y_axis": "stoch_rsi",
        },
    ]

    def calc(self, data, length, rsi_length, k, d, mamode):
        df = pd.DataFrame(data)
        df.columns = ["Date"] + self.columns
        df.set_index(pd.DatetimeIndex(df["Date"]), inplace=True)
        df[df.columns.difference(["Date"])] = (
            df[df.columns.difference(["Date"])]
            .apply(pd.to_numeric, errors="coerce")
            .astype(np.float64)
        )
        df.ta.stochrsi(
            length=int(length),
            rsi_length=int(rsi_length),
            k=int(k),
            d=int(d),
            mamode=STOCHRSI.mamode[int(mamode)],
            cumulative=True,
            append=True,
        )

        stoch_rsi_k = df.columns[-2]
        stoch_rsi_d = df.columns[-1]
        df.dropna()
        # help(df.ta)

        return [
            [[r["Date"], r[stoch_rsi_k]] for r in df.to_dict(orient="records")],
            [[r["Date"], r[stoch_rsi_d]] for r in df.to_dict(orient="records")],
        ]
