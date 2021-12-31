"""container-loading-problem - package.py
---- AUTHOR: Ivan STEPANIAN (iv-stpn <iv.stpn@gmail.com>)
---- ROLE: Defines Package-related classes (Package, PackageList, PlacedPackage, PlacedPackageList)
"""

from math import prod as product
from constants import DIMS
from logger import logger

# TODO: Recheck "NOTE" notes

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
        dims (tuple[float, float, float]): The starting Container dimensions.
        volume (float): The volume calculated from the Container's dims.
    """

    N_PACKAGES = 0

    def __init__(self, dims: "tuple[(float,) * DIMS]") -> None:
        """Package constructor method.

        Args:
            dims (tuple[float, float, float]): The dimensions of the package; the order
            of the dimensions doens't matter.
        """
        self.id: int = Package.N_PACKAGES
        Package.N_PACKAGES += 1
        self.dims = dims
        self.volume = product(dims)

    # NOTE: Might not be completely accurate.
    def larger_than(self, dims: 'tuple[float, float, float]') -> bool:
        """Checks whether a Package instance is smaller than another Package in every dimensions.

        Args:
            dims (tuple[float, float, float]): The dimensions of the Package to compare to.

        Returns:
            bool: Whether this package instance is smaller in all dimensions to the passed dims.
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
        return f"Package{self.dims}"

    def __repr__(self) -> str:
        """Package __repr__ method.

        Returns:
            str: Returns the same as the __str__ method.
        """
        return f"Package{self.dims}"


# TODO: Inherit the dict class


class PackageList:
    """A PackageList keeps track of a list of Package instances, wrapping a dictionary
    with extra Package-specific methods.


    Attributes:
        packages (dict[int, Package]): A map of Package instances, with their id as key.
    """

    def __init__(self, packages: "dict[int, Package]" = None) -> None:
        """PackageList constructor method.

        Args:
            packages (dict[int, Package], optional): Initial packages, or None. $
            Defaults to {} (None -> {}).
        """
        if packages is None:
            packages = {}
        self.packages = packages

    def init_n_pkg_of_each_dims(
        self, n_items_dims: 'list[int, tuple[float, float, float]]'
    ) -> None:
        """Initializes a PackageList from n_items_dims.

        Args:
            n_items_dims (list[int, tuple[float, float, float]]): List of packages, with the first
            number of each item being the number of packages of the dimensions in the following.
            tuple.
        """
        for (n_items, dims) in n_items_dims:
            for _ in range(n_items):
                self.add(Package(dims))

    def add(self, package: Package) -> None:
        """Adds a Package instance to the packages attributes, mapping its id to the instance.

        Args:
            package (Package): A Package instance to add to this PackageList instance.
        """
        self.packages[package.id] = package

    def remove(self, _id: int) -> None:
        """Removes the Package with the corresponding id passed as _id.

        Args:
            _id (int): id of the Package instance to remove.
        """
        del self.packages[_id]

    def total_volume(self) -> float:
        """Returns the total volume of this PackageList.

        Returns:
            float: The sum of the volumes of the Package instances in this PackageList.
        """
        return sum(package.volume for package in self.packages.values())

    def keys(self):
        """Returns the dictionary keys of the packages attribute.

        Returns:
            dict_keys[int, Package]: packages.keys().
        """
        return self.packages.keys()

    def values(self):
        """Returns the dictionary values of the packages attribute.

        Returns:
            dict_values[int, Package]: packages.values().
        """
        return self.packages.values()

    def items(self):
        """Returns the dictionary items of the packages attribute.

        Returns:
            dict_items[int, Package]: packages.items().
        """
        return self.packages.items()

    def copy(self):
        """Returns a copy of the packages attribute.

        Returns:
            PackageList: Copy of packages.
        """
        return PackageList(dict(self.packages))

    # NOTE: Is the assumption that the packages with the smallest length in each dimension
    # are the "smallest packages" correct ? Small doubt: to test in edge cases.
    def find_smallest(self) -> 'dict[int, Package]':
        """Finds the Package instances with the smallest dimensions amongst packages.

        Returns:
            dict[int, Package]: Map of the smallest packages (with their id as key)
        """
        if len(self.packages) > 0:
            smallest = {}
            for i in range(DIMS):
                curr_smallest = min(
                    self.packages.values(), key=lambda package: package.dims[i]
                )

                if curr_smallest.id not in smallest:
                    smallest[curr_smallest.id] = curr_smallest

            logger.info(f"Smallest packages: {smallest}")
            return smallest

        return {}

    def __len__(self) -> int:
        """PackageList __len__ method.

        Returns:
            int: Returns the number of packages in this PackageList.
        """
        return len(self.packages)

    def __contains__(self, key) -> bool:
        """PackageList __contains__ method.

        Args:
            key: The id of a package in this PackageList.

        Returns:
            bool: Returns whether a Package id is part of this PackageList.
        """
        return key in self.packages

    def __getitem__(self, key) -> Package:
        """PackageList __getitem__ method.

        Args:
            key: The id of a package in this PackageList.

        Returns:
            Package: Returns the Package corresponding to the passed id (key).
        """
        return self.packages[key]


class PlacedPackage:
    """A PlacedPackage is a package placed (or potentially placed) in a Container, at
    given coordinates with a given rotation.


    Attributes:
        package (Package): The Package instance on which this PlacedPackage instance is based.

        dims (tuple[float, float, float]): The dimensions of the package in its current rotation.

        min_coords (tuple[float, float, float]): The vertex of the package with the smallest
        coordinates.

        max_coords (tuple[float, float, float]): The vertex of the package with the largest
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
            coords (tuple[float, float, float]): Coordinates for the package to be placed.
            rotation (tuple[int, int, int]): Given rotation in which to place the package.
        """
        self.package = package

        # Maps package dims to new dims based on rotation permutation (i.e. rotates the dims)
        self.dims = tuple(self.package.dims[rotation[i]] for i in range(DIMS))

        self.min_coords = coords
        self.max_coords: "tuple[(float,) * DIMS]" = tuple(
            coords[i] + self.dims[i] for i in range(DIMS)
        )
        self.rotation = rotation

    def volume(self) -> float:
        """Returns the volume of the Package instance associated with this PlacedPackage instance.

        Returns:
            float: package volume.
        """
        return self.package.volume

    def can_stack_on_top_face(self, vertex: 'tuple[float, float, float]') -> bool:
        """Checks if this PlacedPackage can be placed on top of a given vertex.

        Args:
            vertex (tuple[float, float, float]): Vertex on which to stack this PlacedPackage.

        Returns:
            bool: Whether this PlacedPackage instance can stack on the passed vertex.
        """
        if vertex[1] == 0:
            return True

        if (
            self.max_coords[1] - STACKING_TOLERANCE
            < vertex[1]
            < self.max_coords[1] + STACKING_TOLERANCE
        ):
            if (
                self.min_coords[0] < vertex[0] < self.max_coords[0]
                and self.min_coords[2] < vertex[2] < self.max_coords[2]
            ):
                return True

        return False

    def intersects_package(
        self, min_coords: "tuple[(float,) * DIMS]", max_coords: "tuple[(float,) * DIMS]"
    ) -> bool:
        """Checks whether a given Package instance (through its start coordinates 'min_coords', and
        end coordinates 'max_coords') intersects with this PlacedPackage.

        Args:
            min_coords (tuple[float, float, float]): start coordinates of a Package instance
            (i.e. corner with smallest coordinates).
            max_coords (tuple[float, float, float]): end coordinates of a Package instace
            (i.e. corner with largest coordinates).

        Returns:
            bool: Whether the package formed from the given coordinates intersects with
            this PlacedPackage.
        """
        for i in range(DIMS):
            if (
                max_coords[i] <= self.min_coords[i]
                or self.max_coords[i] <= min_coords[i]
            ):
                return False

        return True

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


# TODO: Inherit the list class


class PlacedPackageList:
    """Wraps a list of PlacedPackage instances that have been placed inside a Container.
    Adds some PlacedPackage-related methods.

    Attributes:
        packages (list[PlacedPackage]): A list of PlacePackage instances
    """

    def __init__(self, packages: "list[PlacedPackage]" = None) -> None:
        """PlacePackageList constructor method.

        Args:
            packages (list[PlacedPackage], optional): The initial list of PlacedPackage instances.
            Defaults to [] (None -> []).
        """
        if packages is None:
            packages = []

        self.packages = packages

    def add(self, package: PlacedPackage) -> None:
        """Appends a PlacedPackage to this PlacedPackageList.

        Args:
            package (PlacedPackage): A PlacedPackage instance to add to this PlacedPackageList.
        """
        self.packages.append(package)

    def remove(self, idx: int) -> None:
        """Removes the PlacedPackage at the index idx from this PlacedPackageList.

        Args:
            idx (int): Index of the PlacedPackage to remove in this PlacedPackageList.
        """
        self.packages.pop(idx)

    def any_intersect(self, min_coords, max_coords) -> bool:
        """Checks whether a given Package instance (through its start coordinates 'min_coords', and
        end coordinates 'max_coords') intersects with any Package instance inside this PackageList.

        Args:
            min_coords (tuple[float, float, float]): start coordinates of a Package instance
            (i.e. corner with smallest coordinates).
            max_coords (tuple[float, float, float]): end coordinates of a Package instace
            (i.e. corner with largest coordinates).

        Returns:
            bool: Whether the package formed from the given coordinates intersects with any package
            from this PlacedPackageList.
        """
        return any(
            package.intersects_package(min_coords, max_coords)
            for package in self.packages
        )

    def any_can_stack(self, vertex) -> bool:
        """Checks if any PlacedPackage in this PlacedPackageList can be placed on top of a given
        vertex.

        Args:
            vertex (tuple[float, float, float]): Vertex on which to stack any PlacedPackage.

        Returns:
            bool: Whether any PlacedPackage in this PlacedPackageList can stack on the passed
            vertex.
        """
        return any(
            package.can_stack_on_top_face(vertex) for package in self.packages
        )

    def total_volume(self) -> float:
        """Returns the total volume of this PlacedPackageList.

        Returns:
            float: The sum of the volumes of the Package instances in this PlacedPackageList.
        """
        return sum(package.volume() for package in self.packages)

    def __len__(self) -> int:
        """PlacedPackageList __len__ method.

        Returns:
            int: Returns the number of packages in this PlacedPackageList.
        """
        return len(self.packages)

    def __contains__(self, package: PlacedPackage) -> bool:
        """PlacedPackageList __contains__ method.

        Args:
            package (PlacedPackage): A PlacedPackage instace.

        Returns:
            bool: Returns whether a given PlacedPackage instance is part of this PlacedPackageList.
        """
        return package in self.packages

    def __getitem__(self, idx) -> PlacedPackage:
        """PlacedPackageList __getitem__ method.

        Args:
            idx: The index of the PlacedPackage in the list.

        Returns:
            PlacedPackage: Returns the PlacedPackage stored at the passed index in the
            PlacedPackageList.
        """
        return self.packages[idx]
