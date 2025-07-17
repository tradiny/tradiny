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

from datetime import datetime, timedelta

from indicators.data.serializable import Serializable
from indicators.data.plottable import Plottable


class Indicator(Serializable, Plottable):

    def __init__(self):
        self.initialized = False

    def set_log(self, log):
        self.log = log

    def safe_calc(self, *args, **kwargs):
        try:
            return self.calc(*args, **kwargs)
        except Exception as e:
            self.log(
                "Error exception in indicator %s: %s, returning NaNs..."
                % (self.name, str(e))
            )

            ohlc_data = args[0] if len(args) >= 1 else None
            if ohlc_data is None and "ohlc_data" in kwargs:
                ohlc_data = kwargs["ohlc_data"]
            return self.calc_nan(ohlc_data)

    def calc_nan(self, ohlc_data):
        ret = []
        for o in range(len(self.outputs)):
            ret.append([[d[0], float("nan")] for d in ohlc_data])
        return ret

    def get_interval_from_ohlc_data(self, ohlc_data):
        detected_intervals = []
        trials = 5

        trials += 1
        iterate_by = int(len(ohlc_data) / trials)
        for i in range(0, len(ohlc_data) - iterate_by, iterate_by):
            t1 = ohlc_data[i][0]
            t2 = ohlc_data[i + 1][0]
            detected_intervals.append(
                self._get_interval_from_last_two_datapoints(t1, t2)
            )
        most_common_string = lambda lst: max(set(lst), key=lst.count)
        return most_common_string(detected_intervals)

    def _get_interval_from_last_two_datapoints(self, p1, p2):
        if type(p1) is str:
            p1 = datetime.strptime(p1, "%Y-%m-%d %H:%M:%S")
        if type(p2) is str:
            p2 = datetime.strptime(p2, "%Y-%m-%d %H:%M:%S")
        diff = p2 - p1
        if timedelta(seconds=45) < diff and diff < timedelta(seconds=75):
            return "1m"
        elif timedelta(minutes=4) < diff and diff < timedelta(minutes=6):
            return "5m"
        elif timedelta(minutes=10) < diff and diff < timedelta(minutes=20):
            return "15m"
        elif timedelta(minutes=20) < diff and diff < timedelta(minutes=40):
            return "30m"
        elif timedelta(minutes=45) < diff and diff < timedelta(minutes=75):
            return "1h"
        elif timedelta(minutes=100) < diff and diff < timedelta(minutes=140):
            return "2h"
        elif timedelta(hours=3) < diff and diff < timedelta(hours=5):
            return "4h"
        elif timedelta(hours=5) < diff and diff < timedelta(hours=7):
            return "6h"
        elif timedelta(hours=11) < diff and diff < timedelta(hours=13):
            return "12h"
        elif timedelta(hours=20) < diff and diff < timedelta(hours=28):
            return "1d"
        elif timedelta(days=2) < diff and diff < timedelta(days=4):
            return "3d"
        elif timedelta(days=6) < diff and diff < timedelta(days=8):
            return "1w"
        elif timedelta(days=20) < diff and diff < timedelta(days=40):
            return "1M"
        else:
            return "1h"
