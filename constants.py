"""container-loading-problem - constants.py
---- AUTHOR: Ivan STEPANIAN (iv-stpn <iv.stpn@gmail.com>)
---- ROLE: Defines the global constants of the folder
"""

from itertools import permutations

# Number of dimensions for the coordinate system used throughout the code base.
DIMS = 3

# Possible permutations of the coordinates of a rectangular prism.
# Maps coordinates (0, 1, 2) = (x, y z) to the corresponding permutation.
# (e.g PERUMATIONS[2] = (1, 0, 2) <=> (0, 1, 2) => (1, 0, 2) <=> (x, y, z) => (y, x, z) rotation)
PERMUTATIONS = tuple(permutations(range(DIMS)))

# Where to place the first package during the Three Corners Heuristic algorithm
# Initially set to (0, 0, 0)
INIT_COORDS = tuple(0 for _ in range(DIMS))
