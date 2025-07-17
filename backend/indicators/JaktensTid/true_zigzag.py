"""
Apache License
Version 2.0, January 2004
http://www.apache.org/licenses/

Author: https://github.com/JaktensTid/true-zigzag
"""

from math import floor
import pandas as pd
import pandas_ta as ta
import numpy as np

from indicators.data.indicator import Indicator


def _calc_dev(base_price, price):
    return 100 * (price - base_price) / base_price


def zigzag(highs, lows, depth=10, dev_threshold=5):
    def pivots(src_raw, length, isHigh):
        src = list(reversed(src_raw))
        bar_index = list(range(len(src)))
        for start in range(0, len(src)):
            if start + 2 * length + 1 > len(src) - 1:
                return
            p = 0
            if length < len(src) - start:
                p = src[start + length]
            if length == 0:
                yield 0, p
            else:
                isFound = True
                for i in range(start, start + length):
                    if isHigh and src[i] > p:
                        isFound = False
                    if not isHigh and src[i] < p:
                        isFound = False
                for i in range(start + length + 1, start + 2 * length + 1):
                    if isHigh and src[i] >= p:
                        isFound = False
                    c = not isHigh and src[i] <= p
                    if c:
                        isFound = False
                if isFound:
                    yield (bar_index[start + length], p)
                else:
                    yield None, None

    data_highs = [x for x in pivots(highs, floor(depth / 2), True) if x[0]]
    data_lows = [x for x in pivots(lows, floor(depth / 2), False) if x[0]]

    raw_pairs = []

    for i, (ind, p) in enumerate(data_highs):
        lows_d = sorted(
            [(ind_l, p_l) for ind_l, p_l in data_lows if ind > ind_l],
            key=lambda x: x[0],
        )
        if lows_d:
            lows = lows_d[-1]

            if abs(_calc_dev(lows[1], p)) >= dev_threshold:
                raw_pairs.append(((ind, p), (lows[0], lows[1])))

    result = []

    for (i_h, p_h), (i_l, p_l) in raw_pairs:
        if not result:
            result.append(((i_h, p_h), (i_l, p_l)))
            continue

        if i_l == result[-1][1][0]:
            if p_h > result[-1][0][1]:
                result = result[:-1]
            else:
                continue

        result.append(((i_h, p_h), (i_l, p_l)))

    return result


class ZIGZAG(Indicator):

    id = "indicators.jaktenstid.zigzag.ZIGZAG"
    name = "Zig Zag"
    categories = ["trend"]

    columns = ["high", "low"]

    inputs = [
        {"name": "depth", "space": list(range(1, 50)), "default": [10]},
        {
            "name": "dev_threshold",
            "space": list(np.arange(0.1, 10, 0.1)),
            "default": [0.5],
        },
    ]

    outputs = [{"name": "ZigZag", "y_axis": "price"}]

    def calc(self, data, depth, dev_threshold):
        df = pd.DataFrame(data)
        df.columns = ["Date"] + self.columns
        df.set_index(pd.DatetimeIndex(df["Date"]), inplace=True)
        df[df.columns.difference(["Date"])] = (
            df[df.columns.difference(["Date"])]
            .apply(pd.to_numeric, errors="coerce")
            .astype(np.float64)
        )
        out_name = "zig_zag"

        # 1. Prepare an empty column.
        df[out_name] = np.nan

        # 2. Calculate pivot pairs.
        zz_pairs = zigzag(
            df["high"].tolist(),
            df["low"].tolist(),
            depth=int(depth),
            dev_threshold=float(dev_threshold),
        )

        # --- pivot assignment only --------------------------------------------------
        for i, price in sorted(
            (
                (len(df) - 1 - idx, p)  # convert reverse index
                for pair in zz_pairs
                for (idx, p) in pair
            ),
            key=lambda x: x[0],
        ):
            df.at[df.index[i], out_name] = price

        # --- let pandas do the linear work -----------------------------------------
        df[out_name] = df[out_name].interpolate(
            method="linear", limit_area="inside"  # do NOT extrapolate ends
        )

        df.dropna(subset=[out_name], inplace=True)
        result = [[[r["Date"], r[out_name]] for r in df.to_dict(orient="records")]]
        return result
