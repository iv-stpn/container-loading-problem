"""container-loading-problem - main.py
---- AUTHOR: Ivan STEPANIAN (iv-stpn <iv.stpn@gmail.com>)
---- ROLE: Runs the 3CH algorithm on given examples
"""

from typing import Union
from container import Container, ContainerFiller
from package import PackageList

import random
from datetime import datetime
import csv

from logger import display_info, logger

from constants import DIMS

# Sorts packages (ordering decision at the start of the 3CH algorithm) based on the position of
# corners
INIT_SORTING_HEURISTICS = {
    "none": lambda _: 0,
    "random": lambda _: random.random(),
    "volume_desc": lambda pkg: -pkg.volume,
    "volume_asc": lambda pkg: pkg.volume,
    "max_dims": lambda pkg: max(pkg.dims),
    "min_dims": lambda pkg: min(pkg.dims),
}

# Sorts corner (ordering decision during every iteration) based on the position of corners
CORNER_SORTING_HEURISITCS = {
    "none": lambda _: 0,
    "random": lambda _: random.random(),
    "axis_x": lambda pos: pos[0],
    "axis_y": lambda pos: pos[1],
    "axis_z": lambda pos: pos[2],
    "axis_xy": lambda pos: (pos[0], pos[1]),
    "axis_xz": lambda pos: (pos[0], pos[2]),
    "axis_yx": lambda pos: (pos[1], pos[0]),
    "axis_yz": lambda pos: (pos[1], pos[2]),
    "axis_zx": lambda pos: (pos[2], pos[0]),
    "axis_zy": lambda pos: (pos[2], pos[0]),
    "axis_xyz": lambda pos: (pos[0], pos[1], pos[2]),
    "axis_xzy": lambda pos: (pos[0], pos[2], pos[1]),
    "axis_yxz": lambda pos: (pos[1], pos[0], pos[2]),
    "axis_yzx": lambda pos: (pos[1], pos[2], pos[0]),
    "axis_zxy": lambda pos: (pos[2], pos[0], pos[1]),
    "axis_zyx": lambda pos: (pos[2], pos[1], pos[0]),
    "min_axis": lambda pos: min(pos),
    "max_axis": lambda pos: max(pos),
}


@display_info
def save_results(results: "list[dict[str, Union[float, str]]]") -> None:
    """Saves given results to a properly formatted CSV file.

    Args:
        results (list[dict[str, Union[float, str]]]): Results to be saved, as a list of
        singular results (as a dictionary mapping column names to column values).
    """
    file_path = f"results/results_{datetime.now().strftime('%d%m%Y_%H-%M-%S')}"
    with open(file_path, "w") as f:
        writer = csv.DictWriter(f, fieldnames=list(results[0].keys()))
        writer.writeheader()
        for result in results:
            writer.writerow(result)
    logger.info(f"Saved results to '{file_path}'")

    best = max(results, key=lambda result: result["Placed ratio"])
    logger.info(f"Best result: {best}")
    print()


def test_all_heuristics(
    container_dims: "tuple[(float,) * DIMS]",
    n_pkgs_of_each_dims: "list[int, tuple[(float,) * DIMS]]",
) -> None:
    """Tests all heuristic comibnation on a given example (with given container dimensions and
    packages), then saves the results using save_results.

    Args:
        container_dims (tuple[float, float, float]): given container dimensions.
        n_pkgs_of_each_dims (list[int, tuple[float, float, float]]): list of packages, with the
        first number of each item being the number of packages of the dimensions in the following
        tuple.
    """
    container = Container(container_dims)
    packages = PackageList()
    packages.init_n_pkg_of_each_dims(n_pkgs_of_each_dims)
    container_filler = ContainerFiller(container, packages)

    results = []
    for init_heuristic in INIT_SORTING_HEURISTICS:
        for corner_heuristic in CORNER_SORTING_HEURISITCS:
            results.append(
                container_filler.full_iteration_with_heuristics(
                    save=False,
                    render=False,
                    heuristics={
                        "init_sorting": INIT_SORTING_HEURISTICS[init_heuristic],
                        "corner_sorting": CORNER_SORTING_HEURISITCS[corner_heuristic],
                    },
                    run_name=f"{init_heuristic}+{corner_heuristic}",
                )
            )

    save_results(results)


def example_1() -> None:
    """Tests all heuristic combinations for example one.
    """
    container_dims = (1203.0, 233.5, 268.5)
    n_pkgs_of_each_dims = [
        (40, (53.5, 29.5, 24.5)),
        (10, (38.5, 35.5, 32.5)),
        (13, (53.5, 29.5, 24.5)),
        (15, (53.5, 39.5, 39.5)),
        (20, (60.5, 50.5, 41.5)),
        (22, (53.5, 30.5, 24.5)),
        (12, (58.5, 53.5, 33.5)),
        (132, (59.5, 41.5, 35.5)),
        (375, (72.5, 43.5, 43.5)),
    ]

    test_all_heuristics(container_dims, n_pkgs_of_each_dims)


def example_2() -> None:
    """Tests all heuristic combinations for example two.
    """
    container_dims = (1203.0, 233.5, 268.5)
    n_pkgs_of_each_dims = [
        (77, (52, 43, 60)),
        (67, (47, 46, 44)),
        (4, (21, 21, 33)),
        (97, (56, 43, 38)),
        (34, (42, 49, 50)),
        (159, (36, 46, 58)),
        (60, (58, 59, 40)),
        (21, (47, 40, 23)),
        (55, (56, 35, 52)),
        (17, (45, 47, 55)),
        (58, (50, 51, 34)),
        (21, (56, 50, 34)),
        (29, (60, 55, 36)),
        (2, (57, 57, 50)),
        (7, (57, 57, 43)),
        (8, (58, 48, 32)),
    ]

    test_all_heuristics(container_dims, n_pkgs_of_each_dims)


example_1()
example_2()
