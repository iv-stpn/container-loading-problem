"""container-loading-problem - render.py
---- AUTHOR: Ivan STEPANIAN (iv-stpn <iv.stpn@gmail.com>)
---- ROLE: Defines rendering-related utils (save_and_render, render_3mf)
"""

import pickle
import trimesh
from pyrender import Mesh, Scene, Viewer
import os.path
import numpy as np

from typing import Any
from constants import CONSTRAINTS

from export import (
    to_file_pickle,
    to_timestamped_file_3mf,
    to_file_3mf,
    to_timestamped_file_pickle,
)
from package import PlacedPackageList


def save_and_render(
    placed_packages: PlacedPackageList,
    id: Any = None,
    filename: str = None,
    folder: str = "scenes",
    mode: str = "pickle",
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

    if mode == "pickle":
        if filename is None:
            file_path = to_timestamped_file_pickle(placed_packages, folder, id)
            render_pickle(file_path)
        else:
            file_path = os.path.join(folder, f"{id}_{filename}.3mf")
            to_file_pickle(file_path, placed_packages)
            render_pickle(file_path)

    elif mode == "3mf":
        if filename is None:
            file_path = to_timestamped_file_3mf(placed_packages, folder, id)
            render_3mf(file_path)
        else:
            file_path = os.path.join(folder, f"{id}_{filename}.3mf")
            to_file_3mf(file_path, placed_packages)
            render_3mf(file_path)

    else:
        raise ValueError(f"Invalid mode: {mode}")

    return file_path


def view_step_by_step(placed_packages: PlacedPackageList) -> None:
    """Renders a PlacedPackageList to a pyrender scene, where package can be added
    step-by-step on the fly with the arrow keys.

    Args:
        placed_packages (PlacedPackageList): The PlacedPackageList to be rendered as a
        "step-by-step" scene.
    """

    KEYS = {"left": 65361, "right": 65363, "up": 65362, "down": 65364}

    class StepByStepViewer(Viewer):
        def __init__(self, placed_packages: PlacedPackageList, scene, *args, **kwargs):
            WALL_THICKNESS = 20
            for i in range(len(placed_packages.container_dims)):
                wall = trimesh.creation.box(
                    (
                        WALL_THICKNESS if i == 0 else placed_packages.container_dims[0],
                        WALL_THICKNESS if i == 1 else placed_packages.container_dims[1],
                        WALL_THICKNESS if i == 2 else placed_packages.container_dims[2],
                    )
                )
                wall.visual.face_colors = [0, 0, 0, 0.1]
                scene.add(
                    Mesh.from_trimesh(wall, smooth=False),
                    name=f"wall_{i}",
                    pose=np.array(
                        [
                            [
                                1,
                                0,
                                0,
                                -WALL_THICKNESS / 2
                                if i == 0
                                else placed_packages.container_dims[0]
                                / 2,  # Place at the center of the box
                            ],
                            [
                                0,
                                1,
                                0,
                                -WALL_THICKNESS / 2
                                if i == 1
                                else placed_packages.container_dims[1]
                                / 2,  # Place at the center of the box
                            ],
                            [
                                0,
                                0,
                                1,
                                -WALL_THICKNESS / 2
                                if i == 2
                                else placed_packages.container_dims[2]
                                / 2,  # Place at the center of the box
                            ],
                            [0, 0, 0, 1],
                        ],
                    ),
                )

            for (i, constraint) in enumerate(CONSTRAINTS):
                constraint_box = trimesh.creation.box(
                    (
                        constraint[1][0] - constraint[0][0],
                        constraint[1][1] - constraint[0][1],
                        constraint[1][2] - constraint[0][2],
                    )
                )
                constraint_box.visual.face_colors = [1, 0, 0, 0.999]  # RED
                scene.add(
                    Mesh.from_trimesh(constraint_box, smooth=False),
                    name=f"constraint_{i}",
                    pose=np.array(
                        [
                            [
                                1,
                                0,
                                0,
                                (constraint[1][0] + constraint[0][0])
                                / 2,  # Place at the center of the box
                            ],
                            [
                                0,
                                1,
                                0,
                                (constraint[1][1] + constraint[0][1])
                                / 2,  # Place at the center of the box
                            ],
                            [
                                0,
                                0,
                                1,
                                (constraint[1][2] + constraint[0][2])
                                / 2,  # Place at the center of the box
                            ],
                            [0, 0, 0, 1],
                        ],
                    ),
                )

            colors = [
                [0.5, 0.5, 1],
                [0.5, 1, 0.5],
                [1, 0.5, 0.5],
                [1, 1, 0],
                [0, 1, 1],
                [1, 0, 1],
                [0, 0, 1],
                [0, 1, 0],
                [0.5, 1, 1],
                [1, 0.5, 1],
                [1, 1, 0.5],
            ]
            # N_COLORS = 100
            # colors = [[random(), random(), random()] for _ in range(N_COLORS)]

            self.placed_packages = placed_packages
            self.package_nodes = []

            for package in placed_packages.values():
                box = trimesh.creation.box(extents=package.dims)
                box.visual.face_colors = colors[package.package.type % len(colors)] + [
                    0.999
                ]
                self.package_nodes.append(
                    scene.add(
                        Mesh.from_trimesh(box, smooth=False),
                        name=package.id,
                        pose=np.array(
                            [
                                [
                                    1,
                                    0,
                                    0,
                                    package.min_coords[0] + package.dims[0] / 2,
                                ],  # Place at the center of the box
                                [
                                    0,
                                    1,
                                    0,
                                    package.min_coords[1] + package.dims[1] / 2,
                                ],  # Place at the center of the box
                                [
                                    0,
                                    0,
                                    1,
                                    package.min_coords[2] + package.dims[2] / 2,
                                ],  # Place at the center of the box
                                [0, 0, 0, 1],
                            ],
                        ),
                    )
                )

            self.current_index = len(self.placed_packages) - 1

            rotate = trimesh.transformations.rotation_matrix(
                angle=np.radians(90.0), direction=[0, 0, 1], point=[0, 0, 0]
            )

            # Set the pose of the camera (the first node in the scene)
            scene.set_pose(
                list(scene.nodes)[0],
                np.dot(scene.get_pose(list(scene.nodes)[0]), rotate),
            )

            super().__init__(scene, *args, **kwargs)

        def on_key_press(self, symbol, modifiers):
            self._message_text = None
            changed = False
            if symbol == KEYS["left"]:
                if self.current_index >= 0:
                    self.scene.remove_node(self.package_nodes[self.current_index])
                    self.current_index = self.current_index - 1

                    self._message_text = (
                        f"Step {self.current_index + 1} / {len(self.placed_packages)}"
                    )

                    changed = True

            elif symbol == KEYS["right"]:
                if self.current_index < len(self.placed_packages) - 1:
                    self.current_index = self.current_index + 1
                    self.scene.add_node(self.package_nodes[self.current_index])

                    self._message_text = (
                        f"Step {self.current_index + 1} / {len(self.placed_packages)}"
                    )

                    changed = True

            elif symbol == KEYS["down"]:
                while self.current_index >= 0:
                    self.scene.remove_node(self.package_nodes[self.current_index])
                    self.current_index = self.current_index - 1

                self._message_text = f"Step 0 / {len(self.placed_packages)}"
                changed = True

            elif symbol == KEYS["up"]:
                while self.current_index < len(self.placed_packages) - 1:
                    self.current_index = self.current_index + 1
                    self.scene.add_node(self.package_nodes[self.current_index])

                self._message_text = (
                    f"Step {len(self.placed_packages)} / {len(self.placed_packages)}"
                )
                changed = True

            if changed:
                diff = (
                    "Start"
                    if self.current_index == -1
                    else list(
                        set(self.placed_packages.corner_history[self.current_index])
                        - set(
                            self.placed_packages.corner_history[self.current_index - 1]
                        )
                    )
                )
                placed_at = (
                    "Start"
                    if self.current_index == -1
                    else self.placed_packages[self.current_index].min_coords
                )

                print()
                print(
                    f'Step {"Start" if self.current_index == -1 else self.current_index}'
                )
                print(f"Placed at: {placed_at}")
                print(
                    f"Current corners: {self.placed_packages.corner_history[self.current_index]}"
                )
                print(f"Difference with previous step: {diff}")

            super().on_key_press(symbol, modifiers)

    StepByStepViewer(
        placed_packages,
        Scene(ambient_light=[0.3, 0.3, 0.3, 1.0]),
        use_raymond_lighting=True,
    )


def render_3mf(file_3mf_path: str) -> None:
    """Renders a properly formatted 3MF file (an archive with the XML model stored
    in the subfolder 3D/3dmodel) to a 3D scene using pyrender and trimesh.

    Args:
        file_3mf_path (str): The file path of the model to be rendered.
    """
    fuze_trimesh = trimesh.load(file_3mf_path)
    scene = Scene.from_trimesh_scene(fuze_trimesh, ambient_light=[0.3, 0.3, 0.3, 1.0])
    rotate = trimesh.transformations.rotation_matrix(
        angle=np.radians(90.0), direction=[0, 0, 1], point=[0, 0, 0]
    )
    scene.set_pose(
        list(scene.nodes)[0], np.dot(scene.get_pose(list(scene.nodes)[0]), rotate)
    )
    Viewer(scene, use_raymond_lighting=True)


def render_pickle(file_pickle_path: str) -> None:
    """Renders a properly formatted pickle file to a step-by-step 3D scene
    using pyrender and trimesh.

    Args:
        file_pickle_path (str): The file path of the model to be rendered.
    """
    with open(file_pickle_path, "rb") as f:
        placed_packages = pickle.load(f)

    view_step_by_step(placed_packages)
