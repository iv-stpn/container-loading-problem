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

## Example 1 (no constraint)

Container: 1203.0cm X 233.5cm X 268.5cm.

Packages:

| Number of packages | Length | Width  | Height |
| ------------------ | ------ | ------ | ------ |
| 40                 | 53.5cm | 29.5cm | 24.5cm |
| 10                 | 38.5cm | 35.5cm | 32.5cm |
| 13                 | 53.5cm | 29.5cm | 24.5cm |
| 15                 | 53.5cm | 39.5cm | 39.5cm |
| 20                 | 60.5cm | 50.5cm | 41.5cm |
| 22                 | 53.5cm | 30.5cm | 24.5cm |
| 12                 | 58.5cm | 53.5cm | 33.5cm |
| 132                | 59.5cm | 41.5cm | 35.5cm |
| 375                | 72.5cm | 43.5cm | 43.5cm |

Best result: 91% placed ratio (heuristics: volume_desc+axis_xyz)

## Example 2 (no constraint)

Container: 1203.0cm X 233.5cm X 268.5cm.

Packages:

| Number of packages | Length | Width | Height |
| ------------------ | ------ | ----- | ------ |
| 77                 | 52cm   | 43cm  | 60cm   |
| 67                 | 47cm   | 46cm  | 44cm   |
| 4                  | 21cm   | 21cm  | 33cm   |
| 97                 | 56cm   | 43cm  | 38cm   |
| 34                 | 42cm   | 49cm  | 50cm   |
| 159                | 36cm   | 46cm  | 58cm   |
| 60                 | 58cm   | 59cm  | 40cm   |
| 21                 | 47cm   | 40cm  | 23cm   |
| 55                 | 56cm   | 35cm  | 52cm   |
| 17                 | 45cm   | 47cm  | 55cm   |
| 58                 | 50cm   | 51cm  | 34cm   |
| 21                 | 56cm   | 50cm  | 34cm   |
| 29                 | 60cm   | 55cm  | 36cm   |
| 2                  | 57cm   | 57cm  | 50cm   |
| 7                  | 57cm   | 57cm  | 43cm   |
| 8                  | 58cm   | 48cm  | 32cm   |

Best result: 84% placed ratio (heuristics: none+axis_xyz)


## TODO:

- Special constraints
- On-the-fly reordering heuristics
- Formalise 3CH algorithm
- Recheck model & codebase - ensure smallest_package logic is correct and all assumptions make mathematical and logical sense
- Implement tree search to create a theoritical complete algorithm
- Implement optimized Monte Carlo tree serach and reinforcement learning algorithms to explore all possible 3CH placements
