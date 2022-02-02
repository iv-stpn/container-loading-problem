"""container-loading-problem - package.py
---- AUTHOR: Ivan STEPANIAN (iv-stpn <iv.stpn@gmail.com>)
---- ROLE: Defines Package-related classes (Package, PackageList, PlacedPackage, PlacedPackageList)
"""

from collections import UserDict
from random import random
from sklearn.cluster import KMeans
from math import prod as product
from constants import DIMS, TYPE_LIMIT
from logger import logger
from utils import intersects

# Two packages can "stack" even if they have up to 0.1 cm of empty space between them
# in the y coordinate
STACKING_TOLERANCE = 0.1


class Package:
    """A Package instance represents a package that hasn't yet been put inside a Container,
    and keeps track of the package's dimensions.

    Class Attributes:
        N_PACKAGES (int): The number of Package instaces created since the script was run.
        Used for the id of the Package instances, starts at 0.

    Attributes:
        dims (tuple[(float,) * DIMS]): The starting Container dimensions.
        volume (float): The volume calculated from the Container's dims.
    """

    N_PACKAGES = 0

    def __init__(self, dims: "tuple[(float,) * DIMS]", type=None) -> None:
        """Package constructor method.

        Args:
            dims (tuple[(float,) * DIMS]): The dimensions of the package; the order
            of the dimensions doens't matter.
        """
        self.id: int = Package.N_PACKAGES
        Package.N_PACKAGES += 1
        self.dims = dims
        self.volume = product(dims)
        self.type = type

    def larger_than(self, dims: "tuple[(float,) * DIMS]") -> bool:
        """Checks whether a Package instance is larger than another Package in every dimensions.

        Args:
            dims (tuple[(float,) * DIMS]): The dimensions of the Package to compare.

        Returns:
            bool: Whether this Package instance is larger than the passed dims in all dimensions.
        """
        self_dims_sorted = list(sorted(self.dims))
        dims_sorted = list(sorted(dims))

        for i in range(DIMS):
            if self_dims_sorted[i] < dims_sorted[i]:
                return False

        return True

    def __str__(self) -> str:
        """Package __str__ method.

        Returns:
            str: The package string representation.
        """
        return f"Package<Dims: {self.dims}, Type: {self.type}>"

    def __repr__(self) -> str:
        """Package __repr__ method.

        Returns:
            str: Returns the same as the __str__ method.
        """
        return f"Package<Dims: {self.dims}, Type: {self.type}>"


class PackageList(UserDict):
    """A PackageList keeps track of a list of Package instances, wrapping a dictionary
    with extra Package-specific methods.


    Attributes:
        packages (dict[int, Package]): A map of Package instances, with their id as key.
    """

    def __init__(self, packages=None, *args, **kwargs):
        """PackageList constructor method.

        Args:
            packages (dict[int, Package], optional): Initial packages, or None.
            Defaults to {} (None becomes {}).
        """
        if packages is None:
            packages = {}

        super(PackageList, self).__init__(packages, *args, **kwargs)

    def generate_package_types(
        self,
        n_items_dims: "list[int, tuple[(float,) * DIMS]]",
        strategy: str = "k_means",
    ) -> None:
        """Generates packages with types depending on the given strategy,
        in case the number of passed types exceeds TYPE_LIMIT.

        Args:
            strategy (str): The strategy to use to generate the package types.
        """
        if strategy == "random":
            for n_items, dims in n_items_dims:
                for _ in range(n_items):
                    self.add(Package(dims, type=random.randint(0, TYPE_LIMIT - 1)))

        elif strategy == "k_means":
            packages = []
            for n_items, dims in n_items_dims:
                packages += [list(dims)] * n_items

            kmeans = KMeans(n_clusters=TYPE_LIMIT).fit(packages)
            for type, dims in zip(kmeans.labels_, packages):
                self.add(Package(dims, type=type))

    def init_n_pkg_of_each_dims(
        self, n_items_dims: "list[int, tuple[(float,) * DIMS]]"
    ) -> None:
        """Initializes a PackageList from n_items_dims.

        Args:
            n_items_dims (list[int, tuple[(float,) * DIMS]]): List of packages, with the first
            number of each item being the number of packages of the dimensions in the following.
            tuple.
        """

        if len(n_items_dims) > TYPE_LIMIT:
            self.generate_package_types(n_items_dims)
            self.package_types = list(range(TYPE_LIMIT))

        else:
            for i, (n_items, dims) in enumerate(n_items_dims):
                for _ in range(n_items):
                    self.add(Package(dims, type=i))

            self.package_types = list(
                set(package.type for package in self.data.values())
            )

    def add(self, package: Package) -> None:
        """Adds a Package instance to the packages attributes, mapping its id to the instance.

        Args:
            package (Package): A Package instance to add to this PackageList instance.
        """
        self.data[package.id] = package

    def total_volume(self) -> float:
        """Returns the total volume of this PackageList.

        Returns:
            float: The sum of the volumes of the Package instances in this PackageList.
        """
        return sum(package.volume for package in self.data.values())

    def copy(self, deep=False):
        """Returns a copy of the packages attribute.

        Returns:
            PackageList: Copy of packages.
        """
        return PackageList(
            dict(map(lambda pkg: (pkg.id, pkg.copy()), self.data.values()))
            if deep
            else dict(self.data),
        )

    def find_smallest(self) -> "dict[int, Package]":
        """Finds the Package instances with the smallest dimensions and the smallest volumes
        amongst packages.

        Returns:
            dict[int, Package]: Map of the smallest packages (with their id as key)
        """
        if len(self.data) > 0:
            smallest = {}

            # Include smallest packages by each dimension
            for i in range(DIMS):
                curr_smallest = min(
                    self.data.values(), key=lambda package: package.dims[i]
                )

                if curr_smallest.id not in smallest:
                    smallest[curr_smallest.id] = curr_smallest

            # Include the smallest volume
            smallest_package = min(
                self.data.values(), key=lambda package: package.volume
            )

            if smallest_package.id not in smallest:
                smallest[smallest_package.id] = smallest_package

            logger.info(f"Smallest packages: {smallest}")
            return smallest

        return {}


class PlacedPackage:
    """A PlacedPackage is a package placed (or potentially placed) in a Container, at
    given coordinates with a given rotation.


    Attributes:
        package (Package): The Package instance on which this PlacedPackage instance is based.

        id (int): The id of the Package instance on which this PlacedPackage instance is based.

        dims (tuple[(float,) * DIMS]): The dimensions of the package in its current rotation.

        min_coords (tuple[(float,) * DIMS]): The vertex of the package with the smallest
        coordinates.

        max_coords (tuple[(float,) * DIMS]): The vertex of the package with the largest
        coordinates.
    """

    def __init__(
        self,
        package: Package,
        coords: "tuple[(float,) * DIMS]",
        rotation: "tuple[(int,) * DIMS]",
    ) -> None:
        """PlacedPackage constructor method.

        Args:
            package (Package): The given Package to take as basis.
            coords (tuple[(float,) * DIMS]): Coordinates for the package to be placed.
            rotation (tuple[int, int, int]): Given rotation in which to place the package.
        """
        self.package = package
        self.id = package.id

        # Maps package dims to new dims based on rotation permutation (i.e. rotates the dims)
        self.dims = tuple(self.package.dims[rotation[i]] for i in range(DIMS))

        self.min_coords = coords
        self.max_coords: "tuple[(float,) * DIMS]" = tuple(
            coords[i] + self.dims[i] for i in range(DIMS)
        )
        self.rotation = rotation

    def copy(self) -> "PlacedPackage":
        """Returns a copy of this PlacedPackage instance.

        Returns:
            PlacedPackage: Copy of this PlacedPackage instance.
        """
        return PlacedPackage(self.package, self.min_coords, self.rotation)

    def volume(self) -> float:
        """Returns the volume of the Package instance associated with this PlacedPackage instance.

        Returns:
            float: package volume.
        """
        return self.package.volume

    def can_stack_on_top_face(self, vertex: "tuple[(float,) * DIMS]") -> bool:
        """Checks if this PlacedPackage can be placed on top of a given vertex.

        Args:
            vertex (tuple[(float,) * DIMS]): Vertex on which to stack this PlacedPackage.

        Returns:
            bool: Whether this PlacedPackage instance can stack on the passed vertex.
        """
        if vertex[2] == 0:
            return True

        if (
            self.max_coords[2] - STACKING_TOLERANCE
            < vertex[2]
            < self.max_coords[2] + STACKING_TOLERANCE
        ):
            if (
                self.min_coords[0] < vertex[0] < self.max_coords[0]
                and self.min_coords[1] < vertex[1] < self.max_coords[2]
            ):
                return True

        return False

    def intersects_package(
        self, min_coords: "tuple[(float,) * DIMS]", max_coords: "tuple[(float,) * DIMS]"
    ) -> bool:
        """Checks whether a given Package instance (through its start coordinates 'min_coords', and
        end coordinates 'max_coords') intersects with this PlacedPackage.

        Args:
            min_coords (tuple[(float,) * DIMS]): start coordinates of a Package instance
            (i.e. corner with smallest coordinates).
            max_coords (tuple[(float,) * DIMS]): end coordinates of a Package instace
            (i.e. corner with largest coordinates).

        Returns:
            bool: Whether the package formed from the given coordinates intersects with
            this PlacedPackage.
        """
        return intersects(self.min_coords, self.max_coords, min_coords, max_coords)

    def __str__(self) -> str:
        """Package __str__ method.

        Returns:
            str: The PackageList string representation.
        """
        return f"XYZ: {self.min_coords}, Dims: {self.dims} (Rotation: {self.rotation})"

    def __repr__(self) -> str:
        """Package __repr__ method.

        Returns:
            str: Returns the same as the __str__ method.
        """
        return f"XYZ: {self.min_coords}, Dims: {self.dims} (Rotation: {self.rotation})"


class PlacedPackageList(UserDict):
    """Wraps a list of PlacedPackage instances that have been placed inside a Container.
    Adds some PlacedPackage-related methods.

    Attributes:
        container_dims (tuple[(float,) * DIMS]): The dimensions of the associated Container
        packages (list[PlacedPackage]): A list of PlacePackage instances
        corner_history (list[tuple[(float,) * DIMS]]): A history of the corners at each step
        of the 3CH algorithm.
    """

    def __init__(
        self,
        container_dims,
        packages: "list[PlacedPackage]" = None,
        corner_history: "list[tuple[(float,) * DIMS]]" = None,
        *args,
        **kwargs,
    ) -> None:
        """PlacePackageList constructor method.

        Args:
            container_dims (tuple[(float,) * DIMS]): The dimensions of the associated Container
            packages (list[PlacedPackage], optional): The initial list of PlacedPackage instances.
            Defaults to [] (None becomes []).
            corner_history (list[tuple[(float,) * DIMS]]): A history of the corners at each step
            of the 3CH algorithm. Defaults to [] (None becomes []).
        """
        self.container_dims = container_dims

        if corner_history is None:
            corner_history = []

        self.corner_history = corner_history

        if packages is None:
            packages = {}

        super(PlacedPackageList, self).__init__(packages, *args, **kwargs)

    def add(self, package: PlacedPackage) -> None:
        """Adds a PlacedPackage to this PlacedPackageList.

        Args:
            package (PlacedPackage): A PlacedPackage instance to add to this PlacedPackageList.
        """
        self.data[package.id] = package

    def any_intersect(self, min_coords, max_coords) -> bool:
        """Checks whether a given Package instance (through its start coordinates 'min_coords', and
        end coordinates 'max_coords') intersects with any Package instance inside this PackageList.

        Args:
            min_coords (tuple[(float,) * DIMS]): start coordinates of a Package instance
            (i.e. corner with smallest coordinates).
            max_coords (tuple[(float,) * DIMS]): end coordinates of a Package instace
            (i.e. corner with largest coordinates).

        Returns:
            bool: Whether the package formed from the given coordinates intersects with any package
            from this PlacedPackageList.
        """
        return any(
            package.intersects_package(min_coords, max_coords)
            for package in self.data.values()
        )

    def stacks_on_any_package(self, vertex) -> bool:
        """Checks if any PlacedPackage in this PlacedPackageList can be placed on top of a given
        vertex.

        Args:
            vertex (tuple[(float,) * DIMS]): Vertex on which to stack any PlacedPackage.

        Returns:
            bool: Whether any PlacedPackage in this PlacedPackageList can stack on the passed
            vertex.
        """
        return any(
            package.can_stack_on_top_face(vertex) for package in self.data.values()
        )

    def total_volume(self) -> float:
        """Returns the total volume of this PlacedPackageList.

        Returns:
            float: The sum of the volumes of the Package instances in this PlacedPackageList.
        """
        return sum(package.volume() for package in self.data.values())

    def copy(self, deep=False) -> "PlacedPackageList":
        """Returns a deep copy of this PlacedPackageList.

        Returns:
            PlacedPackageList: A deep copy of this PlacedPackageList.
        """
        return PlacedPackageList(
            self.container_dims,
            dict(map(lambda pkg: (pkg.id, pkg.copy()), self.data.values()))
            if deep
            else dict(self.data),
        )
