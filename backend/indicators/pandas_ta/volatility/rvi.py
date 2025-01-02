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


class RVI(Indicator):
    # TODO check

    name = "Relative Volatility Index (RVI)"
    categories = ["Volatility"]
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

    columns = ["close", "high", "low"]

    inputs = [
        {"name": "length", "space": list(range(1, 300)), "default": [14]},
        {"name": "mamode", "space": list(range(0, len(mamode))), "default": [1]},
        {"name": "scalar", "space": list(range(50, 150)), "default": [100]},
        {"name": "refined", "space": [0, 1], "default": [0]},
        {"name": "thirds", "space": [0, 1], "default": [0]},
        {"name": "drift", "space": list(range(1, 10)), "default": [1]},
    ]

    outputs = [
        {
            "name": "Relative Volatility Index (RVI)",
            "y_axis": "rvi",
        },
        # {
        #     'name': 'Relative Volatility Index (RVI) Basis',
        #     'y_axis': 'rvi',
        # },
        # {
        #     'name': 'Relative Volatility Index (RVI) Upper',
        #     'y_axis': 'rvi',
        # },
    ]

    def calc(self, data, length, mamode, scalar, refined, thirds, drift):
        df = pd.DataFrame(data)
        df.columns = ["Date"] + self.columns
        df.set_index(pd.DatetimeIndex(df["Date"]), inplace=True)
        df[df.columns.difference(["Date"])] = (
            df[df.columns.difference(["Date"])]
            .apply(pd.to_numeric, errors="coerce")
            .astype(np.float64)
        )
        df.ta.rvi(
            length=int(length),
            scalar=float(scalar),
            mamode=RVI.mamode[int(mamode)],
            refined=bool(refined),
            thirds=bool(thirds),
            drift=int(drift),
            cumulative=True,
            append=True,
        )

        rvi = df.columns[-1]
        df.dropna()
        # help(df.ta)

        return [[[r["Date"], r[rvi]] for r in df.to_dict(orient="records")]]
