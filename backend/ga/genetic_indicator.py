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

import importlib
import copy

from ga.gene import Gene


class GeneticIndicatorFactory:

    def create(self, log=None):

        def GeneticIndicator(name):

            bn = name.split(".")
            base_name = bn[-1]
            bn.pop()
            package = ".".join(bn)
            base = getattr(importlib.import_module(package), base_name)

            class Indicator(base):
                def __init__(self, *args, **kwargs):

                    self.inputs = copy.deepcopy(base.inputs)
                    self.outputs = copy.deepcopy(base.outputs)
                    self.klass_path = name

                    self.gene_pos = 0
                    self.genes = {}

                    if len(args) > 0:
                        for gene in list(args):
                            self.add_gene(gene)
                    else:
                        for inp in self.inputs:
                            self.add_gene(
                                Gene(
                                    name=inp.get("name"),
                                    initial_population=(
                                        inp.get("default") if inp.get("default") else []
                                    ),
                                    gene_space=inp.get("space"),
                                )
                            )

                    if hasattr(super(), "__init__"):
                        super().__init__(*args, **kwargs)

                    self.set_log(log)

                def get_gene_by_name(self, name):
                    return self.genes[name]

                def add_gene(self, gene):
                    gene.pos = self.gene_pos
                    self.genes[gene.name] = gene

                    self.gene_pos += 1

                def num_genes(self):
                    return len(self.genes.values())

            return Indicator

        return GeneticIndicator
