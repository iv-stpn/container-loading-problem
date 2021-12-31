"""container-loading-problem - render.py
---- AUTHOR: Ivan STEPANIAN (iv-stpn <iv.stpn@gmail.com>)
---- ROLE: Defines rendering-related utils (save_and_render, render_3mf)
"""

import trimesh
import pyrender
import os.path
import numpy as np

from typing import Any

from generate_3mf import to_timestamped_file_3mf, to_file_3mf
from package import PlacedPackageList


def save_and_render(
    placed_packages: PlacedPackageList, id: Any = None, filename: str = None, folder: str = "scenes"
) -> str:
    """Saves a PlacedPackageList to a 3MF file and renders the model with pyrender.

    Args:
        placed_packages (PlacedPackageList): The PlacedPackageList to be saved to a model,
        then saved in a 3MF file.

        id (Any, optional): Run id to appear in the filename. Defaults to None.

        filename (str, optional): Name of the file where to save the model.
        Defaults to None. If None, saves to a timestamped file instead of a named file.

        folder (str, optional): The subfolder into which to save the model 3MF file.
        Defaults to "scenes".

    Returns:
        str: The final file path of the saved model.
    """
    if filename is None:
        file_path = to_timestamped_file_3mf(placed_packages, folder, id)
        render_3mf(file_path)
        return file_path

    file_path = os.path.join(folder, f"{id}_{filename}.3mf")
    to_file_3mf(file_path, placed_packages)
    render_3mf(file_path)
    return file_path


def render_3mf(file_3mf_path: str) -> None:
    """Renders a properly formatted 3MF file (an archive with the XML model stored at 3D/3dmodel)
    to a 3D scene using pyrender and trimesh.

    Args:
        file_3mf_path (str): The file path of the model to be rendered.
    """
    fuze_trimesh = trimesh.load(file_3mf_path)
    scene = pyrender.Scene.from_trimesh_scene(fuze_trimesh)
    rotate = trimesh.transformations.rotation_matrix(
        angle=np.radians(90.0), direction=[0, 0, 1], point=[0, 0, 0]
    )

    scene.set_pose(
        list(scene.nodes)[0], np.dot(
            scene.get_pose(list(scene.nodes)[0]), rotate)
    )
    pyrender.Viewer(scene, use_raymond_lighting=True)
