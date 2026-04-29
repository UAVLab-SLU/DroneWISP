from pathlib import Path

import trimesh


GROUND_SIZE_X = 30.0
GROUND_SIZE_Y = 30.0
CUBE_SIZE = 10.0
GROUND_THICKNESS = 0.2


def build_scene() -> trimesh.Trimesh:
    ground = trimesh.creation.box(
        extents=(GROUND_SIZE_X, GROUND_SIZE_Y, GROUND_THICKNESS)
    )
    ground.apply_translation((0.0, 0.0, -GROUND_THICKNESS / 2.0))

    cube = trimesh.creation.box(extents=(CUBE_SIZE, CUBE_SIZE, CUBE_SIZE))
    cube.apply_translation((0.0, 0.0, CUBE_SIZE / 2.0))

    return trimesh.util.concatenate([ground, cube])


def main() -> None:
    output_path = Path(__file__).resolve().parents[2] / "30x30x10.stl"
    mesh = build_scene()
    mesh.export(output_path)
    print(output_path)


if __name__ == "__main__":
    main()
