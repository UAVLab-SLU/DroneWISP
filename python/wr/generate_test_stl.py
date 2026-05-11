import argparse
from pathlib import Path

import trimesh


def build_test_mesh(
    size_x: float,
    size_y: float,
    cube_size: float,
    cube_height: float,
    ground_thickness: float,
) -> trimesh.Trimesh:
    ground = trimesh.creation.box(extents=(size_x, size_y, ground_thickness))
    ground.apply_translation((0.0, 0.0, -ground_thickness / 2.0))

    cube = trimesh.creation.box(extents=(cube_size, cube_size, cube_height))
    cube.apply_translation((0.0, 0.0, cube_height / 2.0))

    return trimesh.util.concatenate([ground, cube])


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate a small WR test STL.")
    parser.add_argument("--output", default="30x30x10.stl")
    parser.add_argument("--size-x", type=float, default=30.0)
    parser.add_argument("--size-y", type=float, default=30.0)
    parser.add_argument("--cube-size", type=float, default=6.0)
    parser.add_argument("--cube-height", type=float, default=10.0)
    parser.add_argument("--ground-thickness", type=float, default=0.2)
    args = parser.parse_args()

    mesh = build_test_mesh(
        size_x=args.size_x,
        size_y=args.size_y,
        cube_size=args.cube_size,
        cube_height=args.cube_height,
        ground_thickness=args.ground_thickness,
    )
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    mesh.export(output_path)
    print(output_path.resolve())


if __name__ == "__main__":
    main()
