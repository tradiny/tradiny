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

import copy


class Plottable:

    def plot_data(self, outputs):
        """
        outputs - return value of calc function
        """

        results = []
        outs = copy.copy(self.outputs)
        for idx, o in enumerate(outs):
            if "type" not in o:
                o["type"] = "line"  # default
            outs[idx]["data"] = outputs[idx]

        return outs
