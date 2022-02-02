"""container-loading-problem - container.py
---- AUTHOR: Ivan STEPANIAN (iv-stpn <iv.stpn@gmail.com>)
---- ROLE: Defines Container-related classes (Container, ContainerFiller)
"""

import time
import os

from typing import Union, Callable

from export import to_timestamped_file_pickle
from logger import display_info, logger
from constants import DIMS, INIT_COORDS, PERMUTATIONS, CONSTRAINTS
from package import (
    STACKING_TOLERANCE,
    Package,
    product,
    PackageList,
    PlacedPackage,
    PlacedPackageList,
)
from render import render_3mf, save_and_render, view_step_by_step
from utils import intersects


def IDENTITY(X):
    return X


class Container:
    """Represents a Container to be filled with Package instances.
    A Container instance has given dimensions and keeps track of a linked PlacedPackageList.

    Attributes:
        dims (tuple[(float,) * DIMS]): The starting Container dimensions.
        volume (float): The volume calculated from the Container's dims.
        current_packages (PlacedPackageList): The list of Package instances
        currently placed in the Container.
    """

    def __init__(self, dims: "tuple[(float,) * DIMS]") -> None:
        """Container constructor method.

        Args:
            dims (tuple[(float,) * DIMS]): The starting Container dimensions.
        """
        self.dims = dims
        self.volume = product(dims)
        self.refresh()

    def refresh(self) -> None:
        """Resets the current_packages PlacePackageList attribute."""
        self.current_packages = PlacedPackageList(self.dims)

    def intersects_outside(
        self, min_coords: "tuple[(float,) * DIMS]", max_coords: "tuple[(float,) * DIMS]"
    ) -> bool:
        """Checks whether a given Package instance (through its start coordinates 'min_coords', and end
        coordinates 'max_coords') intersects with the outside of the Container.

        Args:
            min_coords (tuple[(float,) * DIMS]): start coordinates of a Package instance
            (i.e. corner with smallest coordinates).
            max_coords (tuple[(float,) * DIMS]): end coordinates of a Package instace
            (i.e. corner with largest coordinates).

        Returns:
            bool: Whether the Package instance intersects with the outside of the Container.
        """
        for i in range(DIMS):
            if max_coords[i] > self.dims[i] or min_coords[i] < 0:
                return True

        return False

    def can_be_placed(self, placing_package: PlacedPackage) -> bool:
        """Checks whether a package can be placed, by checking if it intersects with any
        PlacedPackage or the outside of the Container.

        Args:
            placing_package (PlacedPackage): Package instance to be potentially placed.

        Returns:
            bool: Whether placing_package can be placed with the Container.
        """

        if any(
            intersects(
                placing_package.min_coords, placing_package.max_coords, *constraint
            )
            for constraint in CONSTRAINTS
        ):
            return False

        if self.current_packages.any_intersect(
            placing_package.min_coords, placing_package.max_coords
        ):
            logger.debug(
                f"Placing {placing_package} would intersect with other placed packages!"
            )
            return False

        if self.intersects_outside(
            placing_package.min_coords, placing_package.max_coords
        ):
            logger.debug(
                f"Placing {placing_package} would make it exceed the container dimensions!"
            )
            return False

        return True

    def place_package(self, placing_package: PlacedPackage) -> bool:
        """If placing_package can be placed, places it and returns True;
        otherwise, does not place it and returns False.

        Args:
            placing_package (PlacedPackage): Package to be potentially placed.

        Returns:
            bool: Whether placing_package was placed.
        """
        if self.can_be_placed(placing_package):
            self.current_packages.add(placing_package)
            return True

        return False


class ContainerFiller:
    """Represents the process of filling a Container with Package instances.
    A ContainerFiller instance has a linked Container and PackageList of Package instances
    to be placed.

    Class Attributes:
        RUN_ID: The ID of the current run. Gets incremented by loop_3CH, starts at 0.

    Attributes:
        container (Container): The Container instance to be linked with this ContainerFiller
        instance.

        _base_packages (PackageList): The initial list of packages to be placed in the
        Container.

        iter_start (float): The time at the start of the current iteration.

        iter_end (float): The time at the end of the current iteration.

        packages_to_put (PackageList): The current list of packages left to be placed in the
        Container, during the current iteration.

        packages_not_placed (PackageList): The current list of packages that could not have
        been placed on any corner during the current iteration.

        smallest_packages (dict[int, Package]): The list of the current smallest packages
        amongst the packages left to be placed (i.e. package with the smallest length
        in a given dimension).

        available_corners (list[tuple[(float,) * DIMS]]): The list of corners (represented
        by tuples of coordinates) that are currently available (for a package to be fitted into).
    """

    RUN_ID = 0

    def __init__(self, container: Container, packages_to_put: PackageList):
        """ContainerFille constructor method.

        Args:
            container (Container): The Container instance to be linked with this ContainerFiller
            instance.
            packages_to_put (PackageList): PackageList of Package instances, to be placed in the
            Container.
        """
        self.container = container
        self._base_packages = packages_to_put
        self.refresh()

    def refresh(self):
        """Refreshes the state of the ContainerFiller instance (and refreshes the state of
        its linked Container)."""
        self.iter_start = None
        self.iter_end = None

        self.debug = False

        self.packages_to_put = self._base_packages.copy()
        self.packages_not_placed = PackageList()

        self.smallest_packages = self.packages_to_put.find_smallest()

        self.available_corners: "list[tuple[(float,) * DIMS]]" = [INIT_COORDS]
        self.container.refresh()

    def place_package(
        self, placing_package: PlacedPackage
    ) -> Union[None, PlacedPackage]:
        """Tries to place a PlacedPackage that was instantiated with a given corner.
        If the PlacedPackage can be placed, remove the corner where it was placed from the list of
        available corners and add its 3 available corners to the available_corners list, then
        return the PlacedPackage; otherwise, return None.

        Args:
            placing_package (PlacedPackage): Package to be potentially placed.

        Returns:
            Union[None, PlacedPackage]: The PlacedPackage if it was placed, None otherwise.
        """
        logger.debug(f"Placing package: {placing_package}")
        if self.container.place_package(placing_package):
            self.available_corners.remove(placing_package.min_coords)
            self.add_corners(placing_package)

            # If debug is enabled, add a copy of the current corners list to the corner_history
            if self.debug:
                self.container.current_packages.corner_history.append(
                    list(self.available_corners)
                )

            return placing_package

        return None

    # NOTE: Experiment with "negative relative positioning" on corner (e.g. sliding a package back
    # on a corner as much as it can fit)?
    def can_package_fit(
        self, package: Package, corner: "tuple[(float,)* DIMS]"
    ) -> bool:
        """Checks whether a Package can fit on a given corner (with any possible rotation).

        Args:
            package (Package): The Package to try to fit on the given corner.
            corner (tuple[(float,) * DIMS]): The given corner where the package will be fitted.

        Returns:
            bool: Whether the Package fits on the corner with any rotation.
        """
        return any(
            self.container.can_be_placed(PlacedPackage(package, corner, rotation))
            for rotation in PERMUTATIONS
        )

    def is_valid_corner(
        self, corner: "tuple[(float,)* DIMS]", stacked_on_top=False
    ) -> bool:
        """Checks whether a corner is a valid corner (i.e. a corner where a package can be placed).

        Args:
            corner (tuple[(float,)* DIMS]): The corner to be checked.

        Returns:
            bool: Whether the corner is a valid corner.
        """

        # NOTE: gravity-breaking corners might be coherent if a package is added afterwards?

        # Ignore a corner put on the ground or on top of the current package
        if corner[2] > STACKING_TOLERANCE and not stacked_on_top:
            # Checks if the corner stacks on any other corner
            if not self.container.current_packages.stacks_on_any_package(corner):
                return False

        # Only add corner if one of the smallest packages can fit on it
        # (otherwise, the corner is pointless)
        if any(
            self.can_package_fit(package, corner)
            for package in self.smallest_packages.values()
        ):
            return True
        return False

    def add_corners(self, placed_package: PlacedPackage) -> None:
        """Adds the new corners of a PlacedPackage placed within the container.

        Args:
            placed_package (PlacedPackage): A PlacedPackage that was just placed in the Container.
        """

        def add_at_idx(tup, idx, val):
            return tuple(tup[i] + val if i == idx else tup[i] for i in range(len(tup)))

        for i in range(DIMS):
            corner = add_at_idx(placed_package.min_coords, i, placed_package.dims[i])
            if self.is_valid_corner(corner, i == 2):
                self.available_corners.append(corner)

    @display_info
    def _stats(
        self, run_name: str = "", debug: bool = False
    ) -> "dict[str, Union[float, str]]":
        """Shows the relevant statistics related to a run of the main loop of ContainerFiller.
        Returns the statistics as a dictionary.

        Shown statistics:
        - Run name ("Run")
        - Iteration duration ("Time")
        - Number of placed packages ("Placed N")
        - Amount of placed volume ("Placed Vol")
        - Number of remaining packages ("Remaining N")
        - Remaining volume to be placed ("Remaining Vol")
        - Ratio of packages placed relative to total volume to be placed ("Placed ratio")
        - Ratio of packages placed reltive to total capacity ("Filling ratio")

        Args:
            run_name (str, optional): The name of the current run. Defaults to "".

        Returns:
            dict[str, Union[float, str]]: Results of the current run
        """
        placed = self.container.current_packages
        not_placed = self.packages_not_placed

        volume_placed = placed.total_volume()
        volume_not_placed = not_placed.total_volume()

        results = {
            "Run": f'RUN_{self.RUN_ID}{"_" + str(run_name) if run_name else ""}',
            "Time": round(self.iter_end - self.iter_start, 2),
            "Placed N": len(placed),
            "Placed Vol": round(volume_placed, 1),
            "Remaining N": len(not_placed),
            "Remaining Vol": round(volume_not_placed, 1),
            "Placed ratio": round(
                volume_placed / (volume_placed + volume_not_placed), 2
            ),
            "Filling ratio": round(volume_placed / self.container.volume, 2),
        }

        logger.info(f"Run name: {results['Run']}")
        logger.info(f"Total iteration time: {results['Time']}s")
        logger.info(f"Placed: {results['Placed N']} ({results['Placed Vol']}) cm³")
        logger.info(
            f"Remains: {results['Remaining N']} ({results['Remaining Vol']} cm³)"
        )
        logger.info(f"Placed ratio: {results['Placed ratio']}")
        logger.info(f"Filling ratio: {results['Filling ratio']}")

        return results

    def loop_3CH(
        self,
        init_sorting_heuristic: Callable = IDENTITY,
        corner_sorting_heuristic: Callable = IDENTITY,
        type_permutation_heuristic: list = None,
        debug: bool = False,
    ) -> None:
        """The core loop of ContainerFiller, implementing the Three Corners Heuristic algorithm.
        Takes sorting heuristics as arguments, calculates the duration of an iteration, and
        increments the RUN_ID of ContainerFiller.

        Args:
            init_sorting_heuristic (Callable, optional): Heuritstic for sorting the order of the
            Package instances to be placed in the Container.
            Defaults to the identity function.

            corner_sorting_heuristic (Callable, optional): Heuristic for sorting the corners of
            the available_corners of the ContainerFiller instance during each iteration.
            Defaults to the identity function.
        """
        self.iter_start = time.perf_counter()

        # Initial package order sorting heuristic
        if type_permutation_heuristic is None:
            try:
                _list = list(
                    sorted(
                        list(self._base_packages.values()), key=init_sorting_heuristic
                    )
                )

            except Exception as err:
                logger.critical(
                    "init_sorting_heuristic is not a correct sorting function!"
                )
                logger.critical(err)
                return

        else:
            try:
                _list = list(
                    sorted(
                        list(self._base_packages.values()),
                        key=lambda pkg: (
                            type_permutation_heuristic.index(pkg.type),
                            -pkg.volume,
                        ),
                    )
                )

            except Exception as err:
                logger.critical(
                    "type_permutation_heuritstic is not a correct permutation!"
                )
                logger.critical(err)
                return

        for package in _list:
            _id = package.id
            if _id in self.packages_to_put:
                placed = False
                logger.warning(f"No. of corners: {len(self.available_corners)}")
                logger.debug(f"Available corners: {self.available_corners}")

                # Corner sorting heuristic
                for corner in list(
                    sorted(self.available_corners, key=corner_sorting_heuristic)
                ):
                    for rotation in PERMUTATIONS:
                        logger.debug(
                            f"Placing: {package}, Corner: {corner}, Rot: {rotation}"
                        )
                        if (
                            self.place_package(PlacedPackage(package, corner, rotation))
                            is not None
                        ):
                            placed = True
                            break

                    if placed:
                        logger.info(f"Placed {package} at {corner}!")
                        break

                self.packages_to_put.pop(package.id)

                # Recalculate smallest packages each time a smallest package is placed
                if package.id in self.smallest_packages:
                    self.smallest_packages = self.packages_to_put.find_smallest()

                    # Rechecking corners (even frequently) is more optimized than
                    # accumulating incoherent corners
                    for corner in self.available_corners:
                        if not any(
                            self.can_package_fit(package, corner)
                            for package in self.smallest_packages.values()
                        ):
                            self.available_corners.remove(corner)

                if not placed:
                    self.packages_not_placed.add(package)
                    logger.error(f"Could not place {package} at any corner!")

                    # Test if there is any package with dims >= to the current
                    # package's dims (and remove them)
                    n_removed = 0
                    for remaining_id in list(self.packages_to_put.keys()):
                        if package.larger_than(self._base_packages[remaining_id].dims):
                            n_removed += 1
                            self.packages_to_put.pop(remaining_id)
                            self.packages_not_placed.add(
                                self._base_packages[remaining_id]
                            )

                    if n_removed:
                        logger.warning(
                            f"Removed {n_removed} extra packages of dims equal or "
                            f"larger to {package}"
                        )

        self.iter_end = time.perf_counter()
        ContainerFiller.RUN_ID += 1

    def full_iteration_with_heuristics(
        self,
        stats=True,
        save=True,
        render=True,
        debug=False,
        heuristics: "dict[str, Callable]" = {},
        run_name="",
    ) -> "Union[None, dict[str, Union[float, str]]]":
        """Executes all methods related to an iteration, including the main loop with the passed
        heuristics, the 3MF converter and rendered, as well as the stats function.
        Returns the statistics of the run if save is set to True.

        Args:
            stats (bool, optional): Whether to show and return the statistics for this run.
            Defaults to True.

            save (bool, optional): Whether to save the 3MF model that results from this run.
            Defaults to True.

            render (bool, optional): Whether to render the 3MF model that results from this run.
            Defaults to True.

            heuristics (dict[str, Callable], optional): Dictionary of the heuristics for this run.
            Expected keys:
            - 'init_sorting' (see loop_3CH)
            - 'corner_sorting' (see loop_3CH)
            Defaults to {}.

            run_name (str, optional): The name of the current run.
            Defaults to "".

        Returns:
            Union[None, dict[str, Union[float, str]]]: Results of a given iteration (see _stats),
            if save is set to True; otherwise returns None.
        """
        self.debug = debug

        init_sorting = heuristics.get("init_sorting")
        corner_sorting = heuristics.get("corner_sorting")
        type_permutation = heuristics.get("type_permutation")

        self.loop_3CH(
            init_sorting if init_sorting is not None else IDENTITY,
            corner_sorting if corner_sorting is not None else IDENTITY,
            type_permutation,
            debug=debug,
        )

        if stats:
            results = self._stats(run_name)
        else:
            results = None

        if debug:
            view_step_by_step(self.container.current_packages)
            print()

        if save and render:
            save_and_render(
                self.container.current_packages, f"{run_name}_{ContainerFiller.RUN_ID}"
            )

        elif save or render:
            file_path = to_timestamped_file_pickle(
                self.container.current_packages,
                "scenes" if save else "temp",
                f"{run_name}_{ContainerFiller.RUN_ID}",
            )
            if render:
                render_3mf(file_path)

            if not save:
                os.remove(file_path)

        self.refresh()
        return results
