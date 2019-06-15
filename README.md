# evolium
Genetic Algorithm that attempts to find a y = mx+c line for a given dataset.
Uses Tournament selection and mutation at configurable rates
Great for finding patterns in 2D data

## Installation
Simply download. Ensure the following are available in your Python Environment.

- argparse
- logging
- csv
- collections
- random
- itertools 

All of the above should be in stdlib

## Usage
From Python 
    import evolium
    data = getData()
    params = getHyperParams()
    evolium.evolve(data, params)

Alternatively, use directly from the CLI

    python3 evolium.py -h
    
Example CLI

    python evolium.py --cycles 10000 --popSize 10000 --minM -1000 --maxM 1000 --minC -1000 --maxC 1000 --dps 4 --verbosity 1 res/medium.csv
