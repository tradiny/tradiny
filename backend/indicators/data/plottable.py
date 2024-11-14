# This software is licensed under a dual license:
#
# 1. Creative Commons Attribution-NonCommercial (CC BY-NC)
#    for individuals and open source projects.
# 2. Commercial License for business use.
#
# For commercial inquiries, contact: license@tradiny.com
#
# For more details, refer to the LICENSE.md file in the root directory of this project.

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
