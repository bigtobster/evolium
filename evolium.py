#!/bin/env python3

import argparse
import logging
import csv
from collections import namedtuple
import random
import itertools

Formula = namedtuple("Formula", "m c fitness")
DataPoint = namedtuple("DataPoint", "x y")
MCRange = namedtuple("MCRange", "minM maxM minC maxC")
HyperParams = namedtuple("HyperParams", "cycles mcrange popSize mutProb mutVal dps tournamentSize goldenSize immigrationSize")

def __parseArgs():
    parser = argparse.ArgumentParser(description='Supply 2 Column CSV of Y, X data')
    parser.add_argument("path", type=str, help="Path to CSV Data", metavar="Path", nargs=1)
    parser.add_argument("--cycles", type=int, help="Number of evolutionary cycles to execute", metavar="Cycles", nargs="?", default=1000)
    parser.add_argument("--popSize", type=int, help="Size of base population", metavar="popSize", nargs="?", default=100)
    parser.add_argument("--minM", type=int, help="Smallest possible value of M", metavar="minM", nargs="?", default=0)
    parser.add_argument("--maxM", type=int, help="Largest possible value of M", metavar="maxM", nargs="?", default=100)
    parser.add_argument("--minC", type=int, help="Smallest possible value of C", metavar="minC", nargs="?", default=0)
    parser.add_argument("--maxC", type=int, help="Largest possible value of C", metavar="maxC", nargs="?", default=100)
    parser.add_argument("--mutProb", type=float, help="Probability of mutation (expressed as decimal between 0 and 1)", metavar="mutProb", nargs="?", default=0.01)
    parser.add_argument("--mutVal", type=float, help="Degree of mutation (expressed as decimal between 0 and 1)", metavar="mutVal", nargs="?", default=0.05)
    parser.add_argument("--dps", type=int, help="Number of decimal points of accuracy to go to", metavar="dps", nargs="?", default=1)
    parser.add_argument("--tournamentSize", type=float, help="Percentage of population involved in tournament (expressed as decimal between 0 and 1)", metavar="tournamentSize", nargs="?", default=0.08)
    parser.add_argument("--goldenSize", type=float, help="Percentage of base population that base population will be reduced to via selection (expressed as decimal between 0 and 1)", metavar="tournamentSize", nargs="?", default=0.4)
    parser.add_argument("--verbosity", type=int, help="Amount of verbiage to display (Debug)", metavar="Verbosity", default=2, choices=[1, 2, 3, 4, 5], nargs="?")
    parser.add_argument("--immigrationSize", type=float, help="Percentage of base population that is completely new each cycle (expressed as decimal between 0 and 1)", metavar="immigrationSize", nargs="?", default=0.2)
    args = parser.parse_args()
    mcrange = MCRange(args.minM, args.maxM, args.minC, args.maxC)
    hyperParams = HyperParams(args.cycles, mcrange, args.popSize, args.mutProb, args.mutVal, args.dps, args.tournamentSize, args.goldenSize, args.immigrationSize)
    return (args.path[0], hyperParams, args.verbosity)


def __getData(path):
    data = []
    with open(path, newline='') as csvfile:
        dataFile = csv.reader(csvfile, delimiter=',')
        for row in dataFile:
            data.append(DataPoint(float(row[0]), float(row[1])))
    logging.debug("Data acquired as " + str(data))
    return data

def __createPopulation(mcrange, dps, popSize):
    logging.debug("Creating new population with popSize " + str(popSize))
    return [Formula(round(random.uniform(mcrange.minM, mcrange.maxM), dps), round(random.uniform(mcrange.minC, mcrange.maxC), dps), None) for _ in range(popSize)]

def __best(population):
    logging.debug("Returning the best of " + str(population))
    return sorted(population, key=lambda ind: ind.fitness)[0]

def __scorePopulation(population, data, hyperParams):
    logging.debug("Scoring whole population of size " + str(len(population)))
    return [Formula(candidate.m, candidate.c, candidate.fitness or __score(candidate, data)) for candidate in population]

def __score(candidate, data):
    logging.debug("Scoring candidate " + str(candidate))
    return sum([abs(round(datapoint.y - ((candidate.m*datapoint.x)+candidate.c), hyperParams.dps)) for datapoint in data])

def __selectPopulation(population, hyperParams):
    logging.debug("Selecting the best " + str(int(round(hyperParams.goldenSize * len(population)))) + " from population of size " + str(len(population)))
    return [__best(random.sample(population, int(round(hyperParams.popSize*hyperParams.tournamentSize, 0)))) for _ in range(int(round(hyperParams.popSize*hyperParams.goldenSize, 0)))]

def __potentialChildren(population):
    ms, cs = [], []
    for cand in population:
        ms.append(cand.m)
        cs.append(cand.c)
    potentials = set([(cand[1], cand[0]) for cand in list(itertools.product(ms, cs))] + list(itertools.product(ms, cs)))
    logging.debug("This population has the potential to have the following children: " + str(potentials))
    return [Formula(pot[0], pot[1], None)for pot in potentials]

def __breedPopulation(population, hyperParams):
    pool = __potentialChildren(population)
    logging.debug("Breeding population of size " + str(len(pool)))
    children = random.sample(pool, int(min(len(pool), (hyperParams.popSize*(1-hyperParams.immigrationSize))-len(population))))
    ################
   # children = set()
   # permutations = __numberOfPerms(population)
   # logging.debug(str(permutations) + " are possible with this breeding population")
   # while len(children) < min(permutations, (hyperParams.popSize*(1-hyperParams.immigrationSize))-len(population)):
   #     mum = random.choice(population)
   #     dad = random.choice(population)
   #     son = __crossover(mum, dad)
   #     children.add(son)
   #     logging.debug("Mum of " + str(mum) + " and Dad of " + str(dad) + " created a child " + str(son))

        # It's possible to have too few permutations on the data set to make a unique children set of the required size
        # This happens when dps is low and the target m and x are in the lower or upper bounds of their respective ranges
        # Solution is to test to see how many candidates could ever be in the children set and use that
    logging.debug(str(len(children)) + " children generated")
    mutatedChildren = __mutate(children, hyperParams)
    immigrants = hyperParams.popSize - (len(children) + len(population))
    logging.debug("Immigrants to be inserted " + str(immigrants))
    population += list(children) + __createPopulation(hyperParams.mcrange, hyperParams.dps, immigrants)
    if len(population) != hyperParams.popSize:
        raise ValueError("Population is length {} and required to be {}".format(len(population), hyperParams.popSize))
    return population

def __crossover(a, b):
    return Formula(a.m, b.c, None)

def __mutate(children, hyperParams):
    mutatedChildren = set()
    counter = 0
    for child in children:
        m = child.m
        c = child.c
        if random.random() < hyperParams.mutProb:
            direction = round(random.random()-0.5, 0)
            counter += 1
            if random.random() < 0.5:
                m += (hyperParams.mutVal * direction)
                logging.debug("Mutating child " + str(child) + "by adding " + str(hyperParams.mutVal * direction) + "to m")
            else:
                c += (hyperParams.mutVal * direction)
                logging.debug("Mutating child " + str(child) + "by adding " + str(hyperParams.mutVal * direction) + "to c")
        else:
            logging.debug("Child with properties m, c " + str((m, c),) + " avoided mutation")
        mutatedChildren.add(Formula(m, c, None))
    logging.debug("A total of " + str(counter) + " children were mutated. " + str(round(len(children) * hyperParams.mutProb, 1)) + " predicted.")
    return mutatedChildren

def setup():
    (path, hyperParams, verbosity) = __parseArgs()
    random.seed()
    logging.basicConfig(filename='debug.log', level=verbosity*10)
    logging.info("Path = " + path)
    logging.info("Verbosity = " + str(verbosity))
    logging.info("HyperParams = " + str(hyperParams))
    data = __getData(path)
    return (data, hyperParams)

def evolve(data, hyperParams):
    basePopulation = __createPopulation(hyperParams.mcrange, hyperParams.dps, hyperParams.popSize)
    for i in range(hyperParams.cycles):
        logging.info("Starting iteration " + str(i+1) + " of " + str(hyperParams.cycles))
        logging.info("Base population size: " + str(len(basePopulation)))
        logging.debug("Base population: " + str(basePopulation))
        fitPopulation = __scorePopulation(basePopulation, data, hyperParams)
        logging.info("Fit population size: " + str(len(fitPopulation)))
        logging.debug("Fit population: " + str(fitPopulation))
        best = __best(fitPopulation)
        logging.info("Best candidate: " + str(best))
        if best.fitness == 0:
            logging.info("Best possible case identified. Returning with " + str(best))
            return (best, i+1)
        bestPopulation = __selectPopulation(fitPopulation, hyperParams)
        logging.info("Best Population size " + str(len(bestPopulation)))
        logging.debug("Best Population: " + str(bestPopulation))
        if i+1 < hyperParams.cycles:
            basePopulation = __breedPopulation(bestPopulation, hyperParams)
        else:
            basePopulation = bestPopulation
    return (__best(basePopulation), hyperParams.cycles)

if __name__ == "__main__":
    (data, hyperParams) = setup()
    (best, completed) = evolve(data, hyperParams)
    print("Best Candidate found with fitness of {fitness} and formula of {m}x+{c} after {cycles}".format(fitness=best.fitness, m=best.m, c=best.c, cycles=hyperParams.cycles))


