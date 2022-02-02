"""container-loading-problem - constants.py
---- AUTHOR: Ivan STEPANIAN (iv-stpn <iv.stpn@gmail.com>)
---- ROLE: Defines the global constants the program uses
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

# Limit of the number of types of packages that can be placed in the container
# Limits the number of permutations of the package types (10 types => 10! = 3628800 possibilities)
TYPE_LIMIT = 10

# Regions of the container where packages cannot be placed, list of (min_coords, max_coords) pairs
CONSTRAINTS = [
    ((0, 0, 254), (16.5, 9, 268.5)),
    ((0, 224.5, 254), (16.5, 233.5, 268.5)),
]
