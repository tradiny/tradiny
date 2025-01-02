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
