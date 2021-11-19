from itertools import permutations
from math import prod as product
import logging
import time
import random

# Sets up a custom logger
LOG_LEVEL = logging.getLevelName("INFO")
APP_NAME = "container-loading"


class CustomFormatter(logging.Formatter):
    from yachalk import chalk
    fmt = "[%(levelname)s] %(asctime)s — %(message)s (%(filename)s:%(lineno)d)"

    FORMATS = {
        logging.DEBUG: chalk.blue(fmt),
        logging.INFO: chalk.green(fmt),
        logging.WARNING: chalk.yellow(fmt),
        logging.ERROR: chalk.red(fmt),
        logging.CRITICAL: chalk.bold.red(fmt)
    }

    def format(self, record):
        return logging.Formatter(self.FORMATS[record.levelno]).format(record)


logger = logging.getLogger(APP_NAME)
logger.setLevel(LOG_LEVEL)
ch = logging.StreamHandler()
ch.setLevel(LOG_LEVEL)
ch.setFormatter(CustomFormatter())
logger.addHandler(ch)

################################################################################
################################################################################
################################################################################

DIMS = 3
PERMUTATIONS = tuple(permutations(range(DIMS)))
INIT_COORDS = tuple(0 for _ in range(DIMS))


class Package:
    n_packages = 0

    def __init__(self, dims: 'tuple[(float,) * DIMS]'):
        self.id = Package.n_packages
        Package.n_packages += 1
        self.dims = dims
        self.volume = product(dims)

    def larger_than(self, dims):
        for i in range(DIMS):
            if self.dims[i] < dims[i]:
                return False

        return True

    def __str__(self):
        return f"Package{self.dims}"

    def __repr__(self):
        return f"Package{self.dims}"


class PackageList:
    def __init__(self, packages: 'dict[int, Package]' = None):
        if packages is None:
            packages = {}
        self.packages = packages

    def init_n_items_dims(self, n_items_dims):
        for (n_items, dims) in n_items_dims:
            for _ in range(n_items):
                self.add(Package(dims))

    def add(self, package):
        self.packages[package.id] = package

    def remove(self, _id):
        del self.packages[_id]

    def total_volume(self):
        return sum(package.volume for package in self.packages.values())

    def keys(self):
        return self.packages.keys()

    def values(self):
        return self.packages.values()

    def items(self):
        return self.packages.items()

    def copy(self):
        return PackageList(dict(self.packages))

    def find_smallest(self):
        smallest = {}
        for i in range(DIMS):
            curr_smallest = min(self.packages.values(),
                                key=lambda package: package.dims[i])

            if curr_smallest.id not in smallest:
                smallest[curr_smallest.id] = curr_smallest

        # logger.info(f'Smallest packages: {smallest}')
        return smallest

    def __len__(self):
        return len(self.packages)

    def __contains__(self, key):
        return key in self.packages

    def __getitem__(self, key):
        return self.packages[key]


class PlacedPackage:
    def __init__(self, package: Package, coords: 'tuple[(float,) * DIMS]',
                 rotation: 'tuple[(int,) * DIMS]'):
        self.package = package

        # Maps package dims to new dims based on rotation permutation (i.e. rotates the dims)
        self.dims = tuple(self.package.dims[rotation[i]] for i in range(DIMS))

        self.min_coords = coords
        self.max_coords: 'tuple[(float,) * DIMS]' = tuple(
            coords[i] + self.dims[i] for i in range(DIMS)
        )
        self.rotation = rotation

    def volume(self):
        return self.package.volume

    def intersects(self, min_coords: 'tuple[(float,) * DIMS]',
                   max_coords: 'tuple[(float,) * DIMS]'):

        for i in range(DIMS):
            if (max_coords[i] <= self.min_coords[i]
                    or self.max_coords[i] <= min_coords[i]):
                return False

        return True

    def __str__(self):
        return f"XYZ: {self.min_coords}, Dims: {self.dims} (Rotation: {self.rotation})"

    def __repr__(self):
        return f"XYZ: {self.min_coords}, Dims: {self.dims} (Rotation: {self.rotation})"


class PlacedPackageList:
    def __init__(self, packages: 'list[PlacedPackage]' = None):
        if packages is None:
            packages = []

        self.packages = packages

    def add(self, package: PlacedPackage):
        self.packages.append(package)

    def remove(self, _id):
        self.packages.pop(_id)

    def any_intersect(self, min_coords, max_coords):
        for package in self.packages:
            if package.intersects(min_coords, max_coords):
                return True

        return False

    def total_volume(self):
        return sum(package.volume() for package in self.packages)

    def __len__(self):
        return len(self.packages)

    def __contains__(self, value):
        return value in self.packages

    def __getitem__(self, idx):
        return self.packages[idx]


class Container:
    def __init__(self, dims: 'tuple[(float,) * DIMS]'):
        self.dims = dims
        self.volume = product(dims)
        self.refresh()

    def refresh(self):
        self.current_packages = PlacedPackageList()

    def intersects_outside(self, min_coords, max_coords):
        for i in range(DIMS):
            if (max_coords[i] > self.dims[i] or min_coords[i] < 0):
                return True

        return False

    def can_be_placed(self, placing_package: PlacedPackage):
        if self.current_packages.any_intersect(placing_package.min_coords, placing_package.max_coords):
            logger.debug(
                f'Placing {placing_package} would intersect with other placed packages!')
            return False

        if self.intersects_outside(placing_package.min_coords, placing_package.max_coords):
            logger.debug(
                f'Placing {placing_package} would make it exceed the container dimensions!')
            return False

        return True

    def place_package(self, placing_package: PlacedPackage):
        if self.can_be_placed(placing_package):
            self.current_packages.add(placing_package)
            return True

        return False


class ContainerFiller:
    def __init__(self, container: Container, packages_to_put: PackageList):
        self.container = container
        self._base_packages = packages_to_put
        self.refresh()

    def refresh(self):
        self.iter_start = None
        self.iter_end = None
        self.packages_to_put = self._base_packages.copy()
        self.packages_not_placed = PackageList()
        self.smallest_packages = self.packages_to_put.find_smallest()
        self.available_corners: 'list[tuple[(float,) * DIMS]]' = [INIT_COORDS]
        self.container.refresh()

    def place_package(self, placing_package: PlacedPackage):
        logger.debug(f"Placing package: {placing_package}")
        if self.container.place_package(placing_package):
            self.available_corners.remove(placing_package.min_coords)
            self.add_corners(placing_package)
            return placing_package

        return None

    def can_package_fit(self, package, corner):
        return any(self.container.can_be_placed(PlacedPackage(package, corner, rotation)) for rotation in PERMUTATIONS)

    def add_corners(self, placed_package: PlacedPackage):
        # Only add corner if smallest packages can fit

        def add_at_idx(tup, idx, val):
            return tuple(tup[i] + val if i == idx else tup[i] for i in range(len(tup)))

        for i in range(DIMS):
            corner = add_at_idx(placed_package.min_coords,
                                i, placed_package.dims[i])

            # Only add corner if one of the smallest packages can fit (otherwise, the corner is pointless)
            # Note: corners should be rechecked after the smallest packages were all placed
            # TODO: compare optimization with and without smallest package check
            if any(self.can_package_fit(package, corner) for package in self.smallest_packages.values()):
                self.available_corners.append(corner)

    def _stats(self):
        placed = self.container.current_packages
        not_placed = self.packages_not_placed

        volume_placed = placed.total_volume()
        volume_not_placed = not_placed.total_volume()

        logger.info(
            f"Total iteration time: {(self.iter_end - self.iter_start):.2f}s")
        logger.info(f"Placed: {len(placed)} ({volume_placed:.1f}) cm³")
        logger.info(
            f"Remains: {len(not_placed)} ({volume_not_placed:.1f} cm³)")
        logger.info(
            f"Volume ratio: {(volume_placed / (volume_placed + volume_not_placed)):.2f}")
        logger.info(
            f"Filling ratio: {(volume_placed / self.container.volume):.2f}")

    def core_loop_3CH(self, sorting_heuristic=lambda _item: _item):
        self.iter_start = time.perf_counter()
        _list = list(
            sorted(list(self._base_packages.values()), key=sorting_heuristic))
        # Initial package order sorting heuristic
        for package in _list:
            _id = package.id
            if _id in self.packages_to_put:
                placed = False
                logger.warning(
                    f"No. of corners: {len(self.available_corners)}")
                # logger.debug(f"Available corners: {self.available_corners}")
                for corner in self.available_corners:
                    for rotation in PERMUTATIONS:
                        # logger.debug(f"Placing: {package}, Corner: {corner}, Rot: {rotation}")
                        if self.place_package(PlacedPackage(package, corner, rotation)) is not None:
                            placed = True
                            break

                    if placed:
                        logger.info(f"Placed {package} at {corner}!")
                        break

                self.packages_to_put.remove(package.id)

                # TODO: Optimize to reduce number of times smallest packages are recalculated
                if package.id in self.smallest_packages:
                    self.smallest_packages = self.packages_to_put.find_smallest()

                    # Rechecking corner (even frequently) is more optimized than accumulating incoherent corners
                    for corner in self.available_corners:
                        if not any(self.can_package_fit(package, corner) for package in self.smallest_packages.values()):
                            self.available_corners.remove(corner)

                if not placed:
                    self.packages_not_placed.add(package)
                    logger.error(f"Could not place {package} at any corner!")
                    # Test if there is any package with dims >= to the current package's dims (and remove them)
                    n_removed = 0
                    for remaining_id in list(self.packages_to_put.keys()):
                        if package.larger_than(self._base_packages[remaining_id].dims):
                            n_removed += 1
                            self.packages_to_put.remove(remaining_id)
                            self.packages_not_placed.add(
                                self._base_packages[remaining_id])

                    if n_removed:
                        logger.warning(
                            f"Removed {n_removed} extra packages of dims equal or larger to {package}")

        self.iter_end = time.perf_counter()


def example_1():
    container = Container((1203.0, 233.5, 268.5))
    packages = PackageList()
    n_items_dims = [(40, (53.5, 29.5, 24.5)),
                    (10, (38.5, 35.5, 32.5)),
                    (13, (53.5, 29.5, 24.5)),
                    (15, (53.5, 39.5, 39.5)),
                    (20, (60.5, 50.5, 41.5)),
                    (22, (53.5, 30.5, 24.5)),
                    (12, (58.5, 53.5, 33.5)),
                    (132, (59.5, 41.5, 35.5)),
                    (375, (72.5, 43.5, 43.5))]

    # n_items_dims = [(2, (53.5, 29.5, 24.5))]

    packages.init_n_items_dims(n_items_dims)
    packages.find_smallest()

    container_filler = ContainerFiller(container, packages)
    container_filler.core_loop_3CH(lambda x: -x.volume)
    container_filler._stats()


example_1()

# static double rand_filling_3CH(Container container)
#         (
#             nb_ticks_rand_filling_3CH -= DateTime.Now.Ticks;
#             float nb_accessible = 0;
#             float nb_inaccessible = 0;
#             List<Package> packages_to_remove = new List<Package>();
#             Random random = new Random();
#             List<Coords3D> available_corners = new List<Coords3D>();
#             available_corners.Add(new Coords3D(0, 0, 0));
#             float nb_of_available_corners = 1;
#             foreach (Package package in container.packages_to_put)
#             (
#                 float curr_corner = random.Next(0, nb_of_available_corners);
#                 float available_corners_tested = 0;

#                 package.coords = available_corners[curr_corner];
#                 do
#                 (
#                     package.coords = available_corners[curr_corner];
#                     float rot = 0;
#                     do
#                     (
#                         flip_state(package, rot);
#                         rot++;
#                     ) while (!get_in(container.packages_placed, package, container) && rot < 6);
#                     curr_corner = (curr_corner + 1) % nb_of_available_corners;
#                     available_corners_tested++;
#                 ) while (!get_in(container.packages_placed, package, container) && available_corners_tested <= nb_of_available_corners);
#                 if (available_corners_tested <= nb_of_available_corners)
#                 (
#                     curr_corner = (curr_corner + nb_of_available_corners - 1) % nb_of_available_corners;
#                     /*if (container.accessible(package))
#                     (
#                         nb_accessible++;
#                     )
#                     else
#                     (
#                         nb_inaccessible++;
#                     )
#                     if (container.update_standable_space(package))
#                     (
#                         container.update_walkable_space();
#                     )
#                     container.update_gradient(package);*/
#                     Coords3D place = available_corners[curr_corner];
#                     available_corners.RemoveAt(curr_corner);
#                     packages_to_remove.Add(package);
#                     container.packages_placed.Add(package);
#                     available_corners.Add(new Coords3D(place.x + package.dim1, place.y, place.z));
#                     available_corners.Add(new Coords3D(place.x, place.y + package.dim2, place.z));
#                     available_corners.Add(new Coords3D(place.x, place.y, place.z + package.dim3));
#                     nb_of_available_corners += 2;
#                 )
#             )
#             foreach(Package package in packages_to_remove)
#             (
#                 container.packages_to_put.Remove(package);
#             )
#             Console.WriteLine("---------------------------------------------------");
#             Console.WriteLine("Rand_filling_3CH\npackages placed :");
#             Console.WriteLine(container.packages_placed.Count());
#             Console.WriteLine("accessible packages :");
#             Console.WriteLine(nb_accessible);
#             Console.WriteLine("inaccessible packages :");
#             Console.WriteLine(nb_inaccessible);
#             Console.WriteLine("cost :");
#             Console.WriteLine(container.costfunction());
#             Console.WriteLine("---------------------------------------------------");
#             float sum_volumes = 0;
#             foreach (Package p in container.packages_placed)
#             (
#                 sum_volumes += p.vol;
#             )
#             Console.WriteLine((double)sum_volumes / container.vol);
#             nb_ticks_rand_filling_3CH += DateTime.Now.Ticks;
#             Utils.write_file("D:\\RL_3mf\\3D\\3dmodel.model", Utils.to_3mf(container.packages_placed));
#             return (double)sum_volumes / container.vol;
#         )
