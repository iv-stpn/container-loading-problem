# Three Corners Heuristics Approach To The Container Loading Problem

Requires Python 3.5+.

To launch the project, run

```bash
pip install -r requirements.txt

# or, following the path under which pip is installed

# pip3 install -r requirements.txt
```

to install the required dependencies.

Then run

```bash
python main.py

# or, following the path under which pip is installed

# python3 main.py
```

to run the `main` script, which contains two hard-coded examples of containers with predefined packages that should be used to fill them as much as possible.

The examples are run on all possible combinations of heuristics to find the best one.

See `previous_results` to check previously generated results.


# Container: 1203.0cm (L) × 233.5cm (W) × 268.5cm (H)

## Example 1

Packages:

| Number of packages | Length | Width  | Height | Volume  |
| ------------------ | ------ | ------ | ------ | ------- |
| 53                 | 24.5cm | 29.5cm | 53.5cm | 0.039m³ |
| 22                 | 24.5cm | 30.5cm | 53.5cm | 0.040m³ |
| 10                 | 38.5cm | 35.5cm | 32.5cm | 0.044m³ |
| 15                 | 39.5cm | 39.5cm | 53.5cm | 0.083m³ |
| 132                | 35.5cm | 41.5cm | 59.5cm | 0.088m³ |
| 12                 | 33.5cm | 53.5cm | 58.5cm | 0.105m³ |
| 20                 | 41.5cm | 50.5cm | 60.5cm | 0.127m³ |
| 375                | 43.5cm | 43.5cm | 72.5cm | 0.137m³ |

### Best result (with INIT_SORTING and CORNER_SORTING heuristics)
91% placed ratio (heuristics: volume_desc+axis_xyz, with constraints)

## Example 2

Packages:

| Number of packages | Length | Width | Height | Volume  |
| ------------------ | ------ | ----- | ------ | ------- |
| 4                  | 21cm   | 21cm  | 33cm   | 0.014m³ |
| 21                 | 23cm   | 40cm  | 47cm   | 0.043m³ |
| 58                 | 34cm   | 50cm  | 51cm   | 0.087m³ |
| 8                  | 32cm   | 48cm  | 58cm   | 0.089m³ |
| 97                 | 38cm   | 43cm  | 56cm   | 0.091m³ |
| 21                 | 34cm   | 50cm  | 56cm   | 0.095m³ |
| 67                 | 44cm   | 46cm  | 47cm   | 0.095m³ |
| 159                | 58cm   | 46cm  | 36cm   | 0.096m³ |
| 55                 | 35cm   | 52cm  | 56cm   | 0.102m³ |
| 34                 | 42cm   | 49cm  | 50cm   | 0.103m³ |
| 17                 | 45cm   | 47cm  | 55cm   | 0.116m³ |
| 29                 | 36cm   | 55cm  | 60cm   | 0.119m³ |
| 77                 | 60cm   | 43cm  | 52cm   | 0.134m³ |
| 60                 | 40cm   | 59cm  | 58cm   | 0.137m³ |
| 7                  | 43cm   | 57cm  | 57cm   | 0.139m³ |
| 2                  | 50cm   | 57cm  | 57cm   | 0.162m³ |


### Best result (with INIT_SORTING and CORNER_SORTING heuristics)
81% placed ratio (heuristics: volume_desc+axis_xzy, with constraints)


## TODO List:

### Interface
- [ ] Complete "debug mode" option
- [ ] Base CLI using argparse
- [ ] Add flags and arguments to CLI
- [ ] Support parralel computing
- [ ] Convert CLI to GUI using Gooey

### 3D Visualizer
- [X] Minimum render
- [X] Show container
- [X] Step-by-step view (with corner history), using keyboard events
- [X] Show constraints
- [X] Use colors to distinguish types of packages
- [ ] Move and rotate the scene freely
- [ ] Extra interactions (zoom, view package info...)

### Heuristics
- [X] INIT_SORTING heuristics
- [X] CORNER_SORTING heuristics
- [X] "Type"-based permutation heuristics
- [X] "Type" generation heuristics
- [ ] "On-the-fly" reording / changing of heuristics mid-algorithm (and meta-heuristics)
- [ ] "Shape"-based heuristics (type variant)
- [ ] Rotation heuristics
- [ ] Inner "type" sorting
- [ ] Inter-type heuristics (change heuristics depending on type)


### Code quality
- [X] Add type hinting
- [X] Add docstrings
- [X] Add comments
- [ ] Clean-up docstings, type hinting, comments
- [ ] Reorder main (no functions in main!)
- [ ] Export pickled Container instead of pickled PlacedPackageList
- [ ] Container-based constraints instead of constant constraints


### 3CH

- [X] Core implementation
- [X] Get statistics at the end of a series of iterations
- [X] "Test all heuristics" implementation
- [ ] "True" bruteforce 3CH
- [ ] Formalise 3CH (can it be proved that a perfect solution is necessarily a 3CH solution?)
- [ ] Recheck / clean-up model and codebase
- [ ] 6CH support
- [ ] "Approximate" 3CH (place packages not only on exact corners)


### Machine learning

- [ ] Generate datasets from "cutting" a container into a perfect filling (risk: very biased datasets)
- [ ] Find an "input" approach
  - N-likeliest package candidates, encoded as types (how to create universal types) or 3D dimensions / M-likeliest corner candidates for a sequential decision-making process
  - OR all packages/corners at once (with a maximal space for the corners and zero-padding)
- [ ] Explore neural/pointer networks (find a working approach):
    - Inputs (?) + Neural Network => Output
    - Output = Ordering => 3CH => Fitness => Training (possible approach?)
    - A gradient descent approach is still very abstract
    - Search for datasets (for now searches have yielded no results)
- [ ] Explore neuroevolution (less likely to get stuck in local minima?):
    - Inputs (?) + Neural Network => Output
    - Define phenotypes and a genetic approach
