import pandas as pd
import pandas_ta as ta
import numpy as np

from indicators.data.indicator import Indicator


class OBVEMA(Indicator):
    name = "On Balance Volume with EMA (OBV EMA)"
    categories = ["Volume"]

    columns = ["close", "volume"]

    inputs = [{"name": "length", "space": list(range(2, 300)), "default": [10]}]

    outputs = [
        {"name": "On Balance Volume (OBV)", "y_axis": "obv"},
        {"name": "EMA(OBV)", "y_axis": "obv"},
    ]

    def calc(self, data, length):
        df = pd.DataFrame(data)
        df.columns = ["Date"] + self.columns
        df.set_index(pd.DatetimeIndex(df["Date"]), inplace=True)
        df[df.columns.difference(["Date"])] = (
            df[df.columns.difference(["Date"])]
            .apply(pd.to_numeric, errors="coerce")
            .astype(np.float64)
        )

        # Compute OBV
        df.ta.obv(cumulative=True, append=True)
        obv_col = df.columns[-1]

        # Compute EMA on OBV
        ema_len = int(length)
        ema_col = f"EMA_{ema_len}_{obv_col}"
        df[ema_col] = ta.ema(close=df[obv_col], length=ema_len)

        df.dropna()

        records = df.to_dict(orient="records")
        return [
            [[r["Date"], r[obv_col]] for r in records],
            [[r["Date"], r[ema_col]] for r in records],
        ]
