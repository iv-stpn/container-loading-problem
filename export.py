"""container-loading-problem - generate_3mf.py
---- AUTHOR: Ivan STEPANIAN (iv-stpn <iv.stpn@gmail.com>)
---- ROLE: Defines 3MF-related utils (to_file_3mf, to_timestamped_file_3mf, write_3mf_to_zip)
"""

import pickle
import random
from itertools import product
from typing import Any
from package import PlacedPackageList

from constants import DIMS
from datetime import datetime
from zipfile import ZipFile

from logger import display_info, logger
import os.path

# XMLNS standard used for the 3MF models generated
STANDARD_XMLNS_3MF = "http://schemas.microsoft.com/3dmanufacturing/core/2015/02"

# All possible 3-bit numbers. Maps to whether a vertex includes
# the length of the dimension of the rectangular prism with the same index.

# (e.g. VERTICES[2] = (False, True, False) => (_, y, _); the vertex corresponds to
# the one where the x and z coordinates are the same as the starting coordinates
# of the rectangular prism, but the y coordinate corresponds to its end coordinate)
VERTICES = list(product([False, True], repeat=DIMS))

# Triangles are represented by sets the of three vertices; the order of those vertices
# matters for the rendering of the triangles (smoother surfaces will be rendered if
# two triangles of the same surface start with the same vertex)

# Here the numbers representing a triangle correspond to the indices of vertices
# in the VERTICES
TRIANGLES = (
    (1, 5, 7),
    (1, 7, 3),
    (5, 4, 6),
    (5, 6, 7),
    (4, 0, 2),
    (4, 2, 6),
    (0, 1, 3),
    (0, 3, 2),
    (3, 7, 6),
    (3, 6, 2),
    (5, 0, 4),
    (5, 1, 0),
)


def rand_hex_color() -> str:
    """Generates and returns a random RBG color (with full opacity) in hex RGBA format.

    Returns:
        str: Random hex RGBA color (with full opacity).
    """
    return f"#{''.join(random.sample('0123456789ABCDEF', 6))}FF"


def _file_chunk(formatted_string: str) -> str:
    """Strips leading newline and trailing whitespace, then add newline at the end of the string.

    Args:
        formatted_string (str): A string with an extra newline at the start,
        and no newline at the end, to be reformatted.

    Returns:
        str: A string with no newline at the start, no whitespace at the end,
        with an appended newline.
    """
    return formatted_string.lstrip("\n").rstrip() + "\n"


def to_timestamped_file_3mf(
    placed_package_list: PlacedPackageList, folder="", id: Any = None
) -> str:
    """Generates a 3MF file with a timestamp as its name.

    Args:
        placed_package_list (PlacedPackageList): The PlacedPackageList instance to save
        to a 3MF file.
        folder (str, optional): Subfolder path in which to save the file. Defaults to "".
        id (Any, optional): A stringifiable identifier; if none, isn't included in
        new file path. Defaults to None.

    Returns:
        str: Generated timestamped file path.
    """
    if id is None:
        file_path = os.path.join(
            folder, f"{datetime.now().strftime('%d%m%Y_%H-%M-%S')}.3mf"
        )
    else:
        # Don't include seconds in file path if no ID is passed.
        # (it is assumed that no two runs with the same ID will finish within the same minute)
        file_path = os.path.join(
            folder, f"{id}_{datetime.now().strftime('%d%m%Y_%H-%M')}.3mf"
        )

    to_file_3mf(file_path, placed_package_list)
    return file_path


@display_info
def write_3mf_to_zip(file_path: str, model: str, debug: bool = False) -> None:
    """Writes a 3MF model, passed as its XML string (the string of the model itself, not of a
    file containing it), and saves it to a ZIP file, as the file 3dmodel.model in the folder
    3D, as per convention. Force-logs the result of the writing of the file.

    Args:
        file_path (str): Path of the 3MF file to be written.
        model (str): XML string (of the model itself, not a file path) of the 3MF model.
    """
    try:
        with ZipFile(file_path, "w") as file_3mf:
            file_3mf.writestr("3D/3dmodel.model", model)
        logger.info(f"Successfully saved 3mf model to '{file_path}'")
    except IOError as err:
        logger.critical(f"Could not save 3mf model to '{file_path}'. Error: {err}")


def to_file_3mf(file_path, placed_package_list: PlacedPackageList) -> None:
    """Creates a 3MF model from a PlacedPackageList instance, and saves it as a 3MF archive
    using write_3mf_to_zip.

    Args:
        file_path (str): Path of the 3MF file to be written.
        placed_package_list (PlacedPackageList): PlacedPackageList instance to be converted
        into an XML-formatted string of its corresponding 3MF model.
    """
    packages = placed_package_list.packages

    # All strings of the XML model are prepended with a newline and do not end with a newline
    # so the strings multiline strings are readable with the same amount of whitespace as they will
    # appear in the XML string generated.

    # The _file_chunk method takes care of dealing with the whitespace of the strings so the XML
    # string is generated properly.

    model = _file_chunk(
        f"""
<?xml version="1.0" encoding="UTF-8"?>
<model unit="meter" xml:lang="en-US" xmlns="{STANDARD_XMLNS_3MF}">
    <resources>"""
    )

    base_materials_str = ""
    vertices_str = ""
    triangles_str = ""

    # Count of vertices
    i = 0

    # Count of packages
    for j, package in enumerate(packages, 1):
        base_materials_str += _file_chunk(
            f"""
        <basematerials id="{j}">
            <base name="Color{j}" displaycolor="{rand_hex_color()}"/>
        </basematerials>"""
        )

        # Generate the vertices coordinates by taking the base
        # dimensions
        vertices = [
            tuple(
                package.min_coords[dim] + package.dims[dim]
                if (x_dim, y_dim, z_dim)[dim]
                else package.min_coords[dim]
                for dim in range(DIMS)
            )
            for x_dim, y_dim, z_dim in VERTICES
        ]

        for v in vertices:
            vertices_str += _file_chunk(
                f"""
                        <vertex x="{v[0]}" y="{v[1]}" z="{v[2]}"/>"""
            )

        for t in TRIANGLES:
            triangles_str += _file_chunk(
                f"""
                        <triangle v1="{i+t[0]}" v2="{i+t[1]}" v3="{i+t[2]}" pid="{j}"/>"""
            )

        # After each iteration, add the number of new vertices to the vertices count
        # (i.e. 8 vertices, as 8 vertices form a rectangular prism)
        i += len(VERTICES)

    model += base_materials_str
    model += _file_chunk(
        f"""
        <object id="{len(packages)+1}" type="model">
            <mesh>
                <vertices>"""
    )

    model += vertices_str
    model += _file_chunk(
        """
                </vertices>
                <triangles>"""
    )

    model += triangles_str
    model += _file_chunk(
        f"""
                </triangles>
            </mesh>
        </object>
    </resources>
    <build>
        <item objectid="{len(packages)+1}"/>
    </build>
</model>"""
    )

    write_3mf_to_zip(file_path, model)


def to_timestamped_file_pickle(
    placed_package_list: PlacedPackageList, folder="", id: Any = None
) -> str:
    """Generates a pickle file with a timestamp as its name.

    Args:
        placed_package_list (PlacedPackageList): The PlacedPackageList instance to save
        to a pickle file.
        folder (str, optional): Subfolder path in which to save the file. Defaults to "".
        id (Any, optional): A stringifiable identifier; if none, isn't included in
        new file path. Defaults to None.

    Returns:
        str: Generated timestamped file path.
    """
    if id is None:
        file_path = os.path.join(
            folder, f"{datetime.now().strftime('%d%m%Y_%H-%M-%S')}.pickle"
        )
    else:
        # Don't include seconds in file path if no ID is passed.
        # (it is assumed that no two runs with the same ID will finish within the same minute)
        file_path = os.path.join(
            folder, f"{id}_{datetime.now().strftime('%d%m%Y_%H-%M')}.pickle"
        )

    to_file_pickle(file_path, placed_package_list)
    return file_path


def to_file_pickle(file_path: str, placed_package_list: PlacedPackageList) -> None:
    """Saves a PlacedPackageList instance to a pickle file.

    Args:
        file_path (str): Path of the pickle file to be written.
        placed_package_list (PlacedPackageList): PlacedPackageList instance to be saved.
    """
    with open(file_path, "wb") as file_pickle:
        pickle.dump(placed_package_list, file_pickle)
