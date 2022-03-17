"""container-loading-problem - main.py
---- AUTHOR: Ivan STEPANIAN (iv-stpn <iv.stpn@gmail.com>)
---- ROLE: Runs the 3CH algorithm on given examples
"""

from multiprocessing import Manager, Process
import json

from typing import Union
from container import IDENTITY, Container, ContainerFiller
from package import PackageList

import random
from datetime import datetime
import csv

from logger import display_info, logger

from constants import DIMS

from itertools import permutations

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


def package_type_permutations(types):
    return tuple(permutations(types))


@display_info
def save_results(
    results: "list[dict[str, Union[float, str]]]", debug: bool = False
) -> None:
    """Saves given results to a properly formatted CSV file.

    Args:
        results (list[dict[str, Union[float, str]]]): Results to be saved, as a list of
        singular results (as a dictionary mapping column names to column values).
    """
    file_path = f"results/results_{datetime.now().strftime('%d-%m-%Y_%H-%M-%S')}"
    with open(file_path, "w") as f:
        writer = csv.DictWriter(f, fieldnames=list(results[0].keys()))
        writer.writeheader()
        for result in results:
            writer.writerow(result)
    logger.info(f"Saved results to '{file_path}'")

    best = max(results, key=lambda result: result["Placed ratio"])
    logger.info(f"Best result: {best}")


def test_all_heuristics(
    container_dims: "tuple[(float,) * DIMS]",
    n_pkgs_by_type: "list[int, tuple[(float,) * DIMS]]",
    permutation_heuristics: bool = False,
    debug_each_heuristic: bool = False,
    debug: bool = False,
) -> None:
    """Tests all heuristic comibnation on a given example (with given container dimensions and
    packages), then saves the results using save_results.

    Args:
        container_dims (tuple[(float,) * DIMS]): given container dimensions.
        n_pkgs_by_type (list[int, tuple[(float,) * DIMS]]): list of packages, with the
        first number of each item being the number of packages of the dimensions in the following
        tuple (i.e. its default "type").
    """
    container = Container(container_dims)
    packages = PackageList()
    packages.init_n_pkg_of_each_dims(n_pkgs_by_type)
    container_filler = ContainerFiller(container, packages)

    results = []
    PRINT_STEP_EVERY = 1 if not permutation_heuristics else 1000
    start_time = datetime.now()

    @display_info
    def print_step(
        i: int, start: datetime, total: int, current_heuristic: str, debug: bool = False
    ) -> None:
        if i % PRINT_STEP_EVERY == 0:
            if i > 0:
                s = (datetime.now() - start).total_seconds()
                logger.info(
                    f"Time taken: {int(s // 3600):02}:{int(s % 3600 // 60):02}:{int(s % 60):02}"
                )

            percent_done = f"({((i+1)/total)*100:.4f}%)"
            logger.info(
                f"Iteration: {i+1:,} / {total:,} {percent_done} {current_heuristic}"
            )

    if permutation_heuristics:

        @display_info
        def init(debug: bool = False):
            logger.info("Generating permutations...")
            type_permutations = package_type_permutations(packages.package_types)
            total_iterations = len(type_permutations)
            logger.info(f"{len(type_permutations):,} permutations will be tested")
            logger.info(f"Total iterations: {total_iterations:,}")
            return type_permutations, total_iterations

        type_permutations, total_iterations = init(debug=debug)

        def run_heuristic(arr, i, type_permutation):
            start_time = datetime.now()

            best = None

            if debug:
                print_step(i, start_time, total_iterations, "", debug=debug)

            for corner_heuristic in CORNER_SORTING_HEURISITCS:

                result = container_filler.full_iteration_with_heuristics(
                    save=False,
                    render=False,
                    debug=debug_each_heuristic,
                    heuristics={
                        "type_permutation": type_permutation,
                        "corner_sorting": CORNER_SORTING_HEURISITCS[corner_heuristic],
                    },
                    run_name=f"{type_permutation}+{corner_heuristic}",
                )

                if best is None or result["Placed ratio"] > best["Placed ratio"]:
                    best = result

            if debug:
                print_step(i, start_time, total_iterations, "", debug=debug)

            arr[i] = json.dumps(best)

        arr = Manager().list(["" for _ in range(total_iterations)])

        p = []
        for i, type_permutation in enumerate(type_permutations):
            p.append(Process(target=run_heuristic, args=(arr, i, type_permutation)))
            p[i].start()

        for q in p:
            q.join()

        results = [json.loads(arr[i]) for i in range(total_iterations)]

    else:

        @display_info
        def init(debug: bool = False):
            logger.info("Calculatings steps...")
            total_iterations = len(INIT_SORTING_HEURISTICS) * len(
                CORNER_SORTING_HEURISITCS
            )
            logger.info(f"Total iterations: {total_iterations:,}")
            return total_iterations

        total_iterations = init(debug=debug)

        step = 0
        for init_heuristic in INIT_SORTING_HEURISTICS:
            for corner_heuristic in CORNER_SORTING_HEURISITCS:
                results.append(
                    container_filler.full_iteration_with_heuristics(
                        save=False,
                        render=False,
                        debug=debug_each_heuristic,
                        heuristics={
                            "init_sorting": INIT_SORTING_HEURISTICS[init_heuristic],
                            "corner_sorting": CORNER_SORTING_HEURISITCS[
                                corner_heuristic
                            ],
                        },
                        run_name=f"{init_heuristic}+{corner_heuristic}",
                    )
                )

                if debug:
                    print_step(
                        step,
                        start_time,
                        total_iterations,
                        f"{init_heuristic}+{corner_heuristic}",
                        debug=debug,
                    )

                if step % PRINT_STEP_EVERY == 0:
                    start_time = datetime.now()
                step += 1

    save_results(results, debug=debug)


def run_with_heuristics(
    example: "tuple[tuple[(float,) * DIMS], list[tuple[(float,) * DIMS]]]",
    init_sorting: str = "volume_desc",
    corner_sorting: str = "axis_xyz",
    type_permutation: list = None,
    debug: bool = False,
    run_name: str = None,
):
    """Runs the 3CH algorithm with given heuristics.

    Args:
        example (tuple[tuple[(float,) * DIMS], list[tuple[(float,) * DIMS]]]): Example to be run,
        as a tuple of the container dimensions followed by the list of the packages.
        init_sorting (str): Initial sorting heuristic.
        corner_sorting (str): Corner sorting heuristic.
        type_permutation (tuple[str]): Package type permutation.
        run_name (str): Name of the run.
    """
    container = Container(example[0])
    packages = PackageList()
    packages.init_n_pkg_of_each_dims(example[1])
    container_filler = ContainerFiller(container, packages)

    if run_name is None:
        run_name = f"{init_sorting or type_permutation}+{corner_sorting}"

    container_filler.full_iteration_with_heuristics(
        save=True,
        render=False,
        stats=True,
        debug=debug,
        heuristics={
            "init_sorting": INIT_SORTING_HEURISTICS.get(init_sorting, IDENTITY),
            "corner_sorting": CORNER_SORTING_HEURISITCS.get(corner_sorting, IDENTITY),
            "type_permutation": type_permutation,
        },
        run_name=run_name,
    )


example_1 = (
    (1203.0, 233.5, 268.5),
    [
        (53, (24.5, 29.5, 53.5)),  # Type: 0
        (22, (24.5, 30.5, 53.5)),  # Type: 1
        (10, (32.5, 38.5, 35.5)),  # Type: 2
        (15, (39.5, 39.5, 53.5)),  # Type: 3
        (132, (35.5, 41.5, 59.5)),  # Type: 4
        (12, (33.5, 53.5, 58.5)),  # Type: 5
        (20, (41.5, 50.5, 60.5)),  # Type: 3
        (375, (43.5, 43.5, 72.5)),  # Type: 7
    ],
)

example_2 = (
    (1203.0, 233.5, 268.5),
    [
        (4, (21, 21, 33)),  # Type: 0
        (21, (23, 40, 47)),  # Type: 1
        (58, (34, 50, 51)),  # Type: 2
        (8, (32, 48, 58)),  # Type: 3
        (97, (38, 43, 56)),  # Type: 4
        (21, (34, 50, 56)),  # Type: 5
        (67, (44, 46, 47)),  # Type: 6
        (159, (36, 46, 58)),  # Type: 7
        (55, (35, 52, 56)),  # Type: 8
        (34, (42, 49, 50)),  # Type: 9
        (17, (45, 47, 55)),  # Type: 10
        (29, (36, 55, 60)),  # Type: 11
        (77, (43, 52, 60)),  # Type: 12
        (60, (40, 58, 59)),  # Type: 13
        (7, (43, 57, 57)),  # Type: 14
        (2, (50, 57, 57)),  # Type: 15
    ],
)

for example in [example_1, example_2]:
    # Tests all INIT_SORTING and CORNER_SORTING heuristic combinations
    # test_all_heuristics(*example, debug=True)

    # Tests all permutations heuristics
    test_all_heuristics(*example, permutation_heuristics=True, debug=True)

# Test a specific heuristic combination for example one.
# run_with_heuristics(
#     example=example_1,
#     init_sorting="volume_desc",
#     corner_sorting="axis_xzy",
#     debug=True,
#     run_name="test_example_1",
# )

# Test a specific type_permutation heuristic for example two.
# run_with_heuristics(
#     example=example_2,
#     corner_sorting="axis_xyz",
#     type_permutation=[0, 1, 2, 5, 9, 4, 6, 7, 8, 3],
#     debug=True,
#     run_name="test_example_2",
# )
