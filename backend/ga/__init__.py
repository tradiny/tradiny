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

import warnings

warnings.filterwarnings("ignore", module="pygad\..*")
import random
import pygad

from app.fetcher import BlockingFetcher


class GA:

    def __init__(
        self,
        num_generations,
        sol_per_pop,
        mutation_num_genes,
        gene_space,
        initial_population,
        fitness,
        parallel_processing=["thread", 2],
        other_settings={},
        log=None,
        debug=True,
    ):
        self.num_generations = num_generations
        self.sol_per_pop = sol_per_pop
        self.mutation_num_genes = mutation_num_genes
        self.gene_space = gene_space
        self.initial_population = initial_population
        self.fitness = fitness
        self.parallel_processing = parallel_processing
        self.other_settings = other_settings
        self.fetcher = BlockingFetcher(parallel_processing[1])

        self.best_solution = None
        self.best_fitness = None
        self.log = log
        self.debug = debug

    def run(self):
        if self.log:
            self.log("Running GA")

        num_generations = self.num_generations
        gene_space = self.gene_space
        num_genes = len(gene_space)
        initial_population = self.initial_population

        num_parents_mating = int(self.sol_per_pop / 2)
        # if num_parents_mating < 2: num_parents_mating = 2
        # if self.sol_per_pop < num_parents_mating: num_parents_mating = self.sol_per_pop

        def on_generation(ga_instance):
            if self.debug and self.log:
                self.log(
                    "Generation : "
                    + str(ga_instance.generations_completed)
                    + "/"
                    + str(self.num_generations)
                )
                self.log(
                    "Fitness of the best solution :"
                    + str(ga_instance.best_solution()[1])
                )
                self.log("Best solution" + str(ga_instance.best_solution()[0]))

            best_solution = ga_instance.best_solution()[0]
            fitness = ga_instance.best_solution()[1]
            if self.best_fitness is None or fitness > self.best_fitness:
                self.best_fitness = fitness
                self.best_solution = best_solution

        kwargs = {
            "num_genes": num_genes,
            "num_generations": num_generations,
            "mutation_num_genes": self.mutation_num_genes,
            "sol_per_pop": self.sol_per_pop,
            "gene_space": gene_space,
            #'keep_elitism': 1,
            # num_genes=num_genes,
            "num_parents_mating": num_parents_mating,
            "fitness_func": self.fitness.get_func(),
            "on_generation": on_generation,
            "mutation_type": "random",
            "parallel_processing": self.parallel_processing,
            "save_solutions": True,
        }
        if initial_population is not None:
            kwargs["initial_population"] = initial_population
        kwargs.update(self.other_settings)
        self.ga_instance = pygad.GA(**kwargs)

        self.ga_instance.run()


from ga.gene import Gene
from ga.genetic_indicator import GeneticIndicatorFactory
from ga.fitness import OscilatorFitness


def calculate(source, name, interval, indicator, data_map, history, ws_url):
    num_generations = 50
    sol_per_pop = 4
    mutation_num_genes = 1

    factory = GeneticIndicatorFactory()
    GeneticIndicator = factory.create(log=print)

    genetic_indicator = GeneticIndicator(indicator["id"])()

    gene_space = []
    for _, gene in genetic_indicator.genes.items():
        gene_space.append(gene.gene_space)

    initial_population = []
    for i in range(0, sol_per_pop):
        ip = []
        for _, gene in genetic_indicator.genes.items():
            if i >= len(gene.initial_population):
                ip.append(random.choice(gene.gene_space))
            else:
                ip.append(gene.initial_population[i])
        initial_population.append(ip)

    fitness = OscilatorFitness(
        source, name, interval, genetic_indicator, indicator, data_map, history, ws_url
    )

    ga = GA(
        debug=True,
        num_generations=num_generations,
        sol_per_pop=sol_per_pop,
        mutation_num_genes=mutation_num_genes,
        gene_space=gene_space,
        initial_population=initial_population,
        fitness=fitness,
    )

    ga.run()

    inputs = {}
    for i, input in enumerate(genetic_indicator.inputs):
        inputs[input["name"]] = ga.best_solution[i]

    return ga.best_fitness, inputs
