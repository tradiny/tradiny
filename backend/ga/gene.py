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


class Gene:
    def __init__(self, name=None, initial_population=None, gene_space=None):
        if name is None:
            raise NotImplementedError

        if initial_population is None:
            raise NotImplementedError

        if gene_space is None:
            raise NotImplementedError

        self.name = name
        self.initial_population = initial_population
        self.gene_space = gene_space
