import argparse
import json
import math
import os
import tempfile
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
import trimesh
from my_stl.mesh_utils import StlMeshUtils
from open_foam_controller import OpenFoamController


DEFAULT_DIRECTION_CONVENTION = "to"
DEFAULT_HEIGHT_CELLS = 10
DEFAULT_ENVIRONMENT_SCALE = 1.0
INTERNAL_BOUND_PADDING = {"xy": 1, "z_min": 1, "z_max": 1}
COMPASS_UNIT_VECTORS = {
    "N": (0.0, 1.0),
    "NNE": (math.sin(math.radians(22.5)), math.cos(math.radians(22.5))),
    "NE": (math.sin(math.radians(45.0)), math.cos(math.radians(45.0))),
    "ENE": (math.sin(math.radians(67.5)), math.cos(math.radians(67.5))),
    "E": (1.0, 0.0),
    "ESE": (math.sin(math.radians(112.5)), math.cos(math.radians(112.5))),
    "SE": (math.sin(math.radians(135.0)), math.cos(math.radians(135.0))),
    "SSE": (math.sin(math.radians(157.5)), math.cos(math.radians(157.5))),
    "S": (0.0, -1.0),
    "SSW": (math.sin(math.radians(202.5)), math.cos(math.radians(202.5))),
    "SW": (math.sin(math.radians(225.0)), math.cos(math.radians(225.0))),
    "WSW": (math.sin(math.radians(247.5)), math.cos(math.radians(247.5))),
    "W": (-1.0, 0.0),
    "WNW": (math.sin(math.radians(292.5)), math.cos(math.radians(292.5))),
    "NW": (math.sin(math.radians(315.0)), math.cos(math.radians(315.0))),
    "NNW": (math.sin(math.radians(337.5)), math.cos(math.radians(337.5))),
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run a single WR CFD job and export one merged CSV.")
    parser.add_argument("--stl-path", default=os.getenv("WR_INPUT_STL_PATH"))
    parser.add_argument("--output-csv", default=os.getenv("WR_OUTPUT_CSV_PATH"))
    parser.add_argument("--config-path", default=os.getenv("WR_INPUT_CONFIG_PATH"))
    parser.add_argument("--case-root", default=os.getenv("WR_CASE_ROOT", "openFoamCase"))
    return parser.parse_args()


def load_config_payload(config_path: Path) -> dict[str, Any]:
    try:
        payload = json.loads(config_path.read_text())
    except json.JSONDecodeError as exc:
        raise ValueError(f"Invalid simulation config JSON: {exc}") from exc
    if not isinstance(payload, dict):
        raise ValueError("Simulation config JSON must be an object.")
    return payload


def parse_wind_config_from_payload(payload: dict[str, Any]) -> dict[str, Any]:
    environment = payload.get("environment") if isinstance(payload.get("environment"), dict) else {}
    origin = environment.get("origin") if isinstance(environment.get("origin"), dict) else {}
    if "wind" in environment:
        wind_payload = environment["wind"]
    elif "wind" in payload:
        wind_payload = payload["wind"]
    else:
        raise ValueError("Simulation config must contain wind or environment.wind.")

    height_cells = DEFAULT_HEIGHT_CELLS
    environment_scale = DEFAULT_ENVIRONMENT_SCALE
    if isinstance(wind_payload, dict):
        if "sources" in wind_payload:
            sources_payload = wind_payload["sources"]
        elif "wind_velocity" in wind_payload and "wind_direction" in wind_payload:
            sources_payload = [wind_payload]
        else:
            raise ValueError("Wind object must contain sources or a single wind definition.")
        if "height_cells" in wind_payload and wind_payload["height_cells"] is not None:
            height_cells = parse_height_cells(wind_payload["height_cells"])
        if "scale" in wind_payload and wind_payload["scale"] is not None:
            environment_scale = parse_environment_scale(wind_payload["scale"])
    else:
        sources_payload = wind_payload

    if not isinstance(sources_payload, list) or not sources_payload:
        raise ValueError("Wind sources must be a non-empty array.")
    normalized: list[dict[str, Any]] = []
    for item in sources_payload:
        if not isinstance(item, dict):
            raise ValueError("Each wind source must be an object.")
        normalized.append(item)
    return {
        "sources": normalized,
        "height_cells": height_cells,
        "scale": environment_scale,
        "radius": origin.get("radius"),
    }


def parse_height_cells(value: Any) -> int:
    if isinstance(value, bool):
        raise ValueError("wind.height_cells must be an integer.")
    if isinstance(value, float) and not value.is_integer():
        raise ValueError("wind.height_cells must be an integer.")
    height_cells = int(value)
    if height_cells < 1:
        raise ValueError("wind.height_cells must be greater than or equal to 1.")
    return height_cells


def parse_environment_scale(value: Any) -> float:
    if isinstance(value, bool):
        raise ValueError("wind.scale must be a float in the range (0, 1].")
    environment_scale = float(value)
    if environment_scale <= 0 or environment_scale > 1:
        raise ValueError("wind.scale must be in the range (0, 1].")
    return environment_scale


def load_mesh_bounds(stl_path: Path) -> tuple[float, float, float, float, float, float]:
    mesh_utils = StlMeshUtils()
    mesh_utils.pv_load_convert_mesh(str(stl_path))
    if mesh_utils.pv_mesh is None:
        raise RuntimeError(f"Failed to load STL mesh: {stl_path}")
    return tuple(mesh_utils.pv_mesh.bounds)


def build_simulation_bounds(stl_path: Path) -> dict[str, int]:
    mesh_bounds = load_mesh_bounds(stl_path)
    return {
        "x_min": math.floor(mesh_bounds[0]) - INTERNAL_BOUND_PADDING["xy"],
        "x_max": math.ceil(mesh_bounds[1]) + INTERNAL_BOUND_PADDING["xy"],
        "y_min": math.floor(mesh_bounds[2]) - INTERNAL_BOUND_PADDING["xy"],
        "y_max": math.ceil(mesh_bounds[3]) + INTERNAL_BOUND_PADDING["xy"],
        "z_min": math.floor(mesh_bounds[4]) - INTERNAL_BOUND_PADDING["z_min"],
        "z_max": math.ceil(mesh_bounds[5]) + INTERNAL_BOUND_PADDING["z_max"],
    }


def build_box_vertices(bounds: dict[str, int]) -> list[tuple[int, int, int]]:
    return [
        (bounds["x_min"], bounds["y_min"], bounds["z_min"]),
        (bounds["x_max"], bounds["y_min"], bounds["z_min"]),
        (bounds["x_max"], bounds["y_max"], bounds["z_min"]),
        (bounds["x_min"], bounds["y_max"], bounds["z_min"]),
        (bounds["x_min"], bounds["y_min"], bounds["z_max"]),
        (bounds["x_max"], bounds["y_min"], bounds["z_max"]),
        (bounds["x_max"], bounds["y_max"], bounds["z_max"]),
        (bounds["x_min"], bounds["y_max"], bounds["z_max"]),
    ]


def measure_mesh_lengths(source_bounds: tuple[float, float, float, float, float, float]) -> dict[str, float]:
    return {
        "x": float(source_bounds[1] - source_bounds[0]),
        "y": float(source_bounds[3] - source_bounds[2]),
        "z": float(source_bounds[5] - source_bounds[4]),
    }


def build_scaling_transform(
    source_bounds: tuple[float, float, float, float, float, float],
    scale_factor: float,
) -> dict[str, Any]:
    source_min = np.array([source_bounds[0], source_bounds[2], source_bounds[4]], dtype=float)
    if scale_factor <= 0:
        raise ValueError("Computed STL scale factor must be positive.")
    translation = source_min - (source_min * scale_factor)

    return {
        "scale_factor": scale_factor,
        "translation": translation.tolist(),
        "source_bounds": list(source_bounds),
        "source_lengths": measure_mesh_lengths(source_bounds),
    }


def apply_forward_scaling(points: np.ndarray, scaling_transform: dict[str, Any]) -> np.ndarray:
    scale_factor = float(scaling_transform["scale_factor"])
    translation = np.asarray(scaling_transform["translation"], dtype=float)
    return (points * scale_factor) + translation


def apply_inverse_scaling(points: np.ndarray, scaling_transform: dict[str, Any]) -> np.ndarray:
    scale_factor = float(scaling_transform["scale_factor"])
    translation = np.asarray(scaling_transform["translation"], dtype=float)
    return (points - translation) / scale_factor


def maybe_scale_stl(source_stl: Path, environment_scale: float) -> tuple[Path, Path | None, dict[str, Any] | None]:
    source_bounds = load_mesh_bounds(source_stl)
    if math.isclose(environment_scale, 1.0, rel_tol=0.0, abs_tol=1e-12):
        return source_stl, None, None

    print(f"Applying wind.scale to STL geometry. Applied scaling factor: {environment_scale:.9f}")
    scaling_transform = build_scaling_transform(source_bounds, environment_scale)
    mesh = trimesh.load_mesh(str(source_stl), file_type="stl", process=False)
    if isinstance(mesh, trimesh.Scene):
        mesh = trimesh.util.concatenate(tuple(mesh.geometry.values()))
    if not isinstance(mesh, trimesh.Trimesh):
        raise RuntimeError(f"Failed to load STL mesh for scaling: {source_stl}")
    handle, temp_path = tempfile.mkstemp(prefix="dronewisp_wr_", suffix=".stl")
    os.close(handle)
    scaled_stl = Path(temp_path)
    mesh.vertices = apply_forward_scaling(np.array(mesh.vertices, dtype=float), scaling_transform)
    mesh.export(str(scaled_stl))
    return scaled_stl, scaled_stl, scaling_transform


def cleanup_case_artifacts(case_root: Path) -> None:
    for pattern in ("wisp_*.csv", "wisp_*.h5", "wisp_*.pkl", "log.*"):
        for artifact in case_root.glob(pattern):
            artifact.unlink(missing_ok=True)


def normalize_wind_type(value: str | None) -> str:
    normalized = (value or "Constant Wind").strip().lower()
    if "turbulent" in normalized:
        return "turbulent"
    return "uniform"


def direction_to_unit_vector(direction: Any, convention: str) -> tuple[float, float]:
    if isinstance(direction, (int, float)):
        angle_deg = float(direction)
    else:
        text = str(direction).strip().upper()
        if text in COMPASS_UNIT_VECTORS:
            x_value, y_value = COMPASS_UNIT_VECTORS[text]
            return (-x_value, -y_value) if convention == "from" else (x_value, y_value)
        try:
            angle_deg = float(text)
        except ValueError as exc:
            raise ValueError(f"Unsupported wind direction: {direction}") from exc
    radians_value = math.radians(angle_deg)
    x_value = math.sin(radians_value)
    y_value = math.cos(radians_value)
    return (-x_value, -y_value) if convention == "from" else (x_value, y_value)


def aggregate_wind_definitions(wind_definitions: list[dict[str, Any]], direction_convention: str) -> dict[str, Any]:
    vector_x = 0.0
    vector_y = 0.0
    fluctuation_values: list[float] = []
    has_turbulence = False
    for item in wind_definitions:
        if "wind_velocity" not in item or "wind_direction" not in item:
            raise ValueError("Each wind definition must include wind_velocity and wind_direction.")
        velocity = float(item["wind_velocity"])
        dir_x, dir_y = direction_to_unit_vector(item["wind_direction"], direction_convention)
        vector_x += velocity * dir_x
        vector_y += velocity * dir_y
        if "fluctuation_percentage" in item and item["fluctuation_percentage"] is not None:
            fluctuation_values.append(float(item["fluctuation_percentage"]))
        has_turbulence = has_turbulence or normalize_wind_type(item.get("wind_type")) == "turbulent"
    count = len(wind_definitions)
    avg_x = vector_x / count
    avg_y = vector_y / count
    speed = math.hypot(avg_x, avg_y)
    if math.isclose(speed, 0.0, abs_tol=1e-9):
        raise ValueError("Averaged wind vector is zero. The source wind definitions cancel each other out.")
    angle_deg = (math.degrees(math.atan2(avg_x, avg_y)) + 360.0) % 360.0
    wind_type = "turbulent" if has_turbulence else "uniform"
    turb_percent = max(fluctuation_values) if fluctuation_values else 0.0
    if wind_type == "turbulent" and turb_percent <= 0:
        turb_percent = 10.0
    if wind_type == "turbulent" and turb_percent <= 0:
        wind_type = "uniform"
    return {
        "wind_speed_x": avg_x,
        "wind_speed_y": avg_y,
        "wind_speed_z": 0.0,
        "wind_type": wind_type,
        "turb_percent": turb_percent if wind_type == "turbulent" else 0.0,
        "speed": speed,
        "direction_deg": angle_deg,
    }


def resolve_control_settings(aggregate_wind: dict[str, Any]) -> dict[str, float | int]:
    if aggregate_wind["wind_type"] == "turbulent":
        return {"dt": 1.0, "end_time": 26.0, "write_interval": 1}
    return {"dt": 1.0, "end_time": 51.0, "write_interval": 50}


def configure_case(
    controller: OpenFoamController,
    terrain_stl: Path,
    bounds: dict[str, int],
    wind: dict[str, Any],
    controls: dict[str, float | int],
    height_cells: int,
) -> None:
    vertices = build_box_vertices(bounds)
    x_size = bounds["x_max"] - bounds["x_min"] + 1
    y_size = bounds["y_max"] - bounds["y_min"] + 1
    z_size = height_cells

    cleanup_case_artifacts(Path(controller.case_root))
    controller.clean()
    if not controller.replace_mesh_with_file(str(terrain_stl)):
        raise RuntimeError(f"Failed to replace mesh with STL: {terrain_stl}")
    controller.update_vertices(vertices)
    controller.update_shm_inside_point(controller.calculate_shm_inside_point(vertices))
    controller.update_dimension(x_size, y_size, z_size)
    controller.update_end_time(controls["end_time"])
    controller.update_write_interval(controls["write_interval"])
    controller.update_dt(controls["dt"])
    controller.update_wind(
        wind["wind_speed_x"],
        wind["wind_speed_y"],
        wind["wind_speed_z"],
        wind["wind_type"],
        wind["turb_percent"],
    )


def preprocess_velocity_dataframe(
    cell: np.ndarray,
    velocity: np.ndarray,
    fill_missing: bool,
    bounds: dict[str, int] | None,
) -> pd.DataFrame:
    frame = pd.DataFrame(
        np.column_stack((cell[:, 0], cell[:, 1], cell[:, 2], velocity[:, 0], velocity[:, 1], velocity[:, 2])),
        columns=["x", "y", "z", "u", "v", "w"],
    )
    frame[["x", "y", "z"]] = frame[["x", "y", "z"]].round().astype(int)
    frame.drop_duplicates(subset=["x", "y", "z"], keep="first", inplace=True)
    frame.sort_values(by=["x", "y", "z"], inplace=True)
    frame.reset_index(drop=True, inplace=True)
    if fill_missing:
        if bounds is None:
            raise ValueError("Bounds are required when fill_missing is enabled.")
        x_coords = np.arange(bounds["x_min"], bounds["x_max"] + 1, dtype=int)
        y_coords = np.arange(bounds["y_min"], bounds["y_max"] + 1, dtype=int)
        z_coords = np.arange(bounds["z_min"], bounds["z_max"] + 1, dtype=int)
        mesh = pd.DataFrame(
            np.array(np.meshgrid(x_coords, y_coords, z_coords, indexing="ij")).T.reshape(-1, 3),
            columns=["x", "y", "z"],
        )
        frame = mesh.merge(frame, on=["x", "y", "z"], how="left")
    return frame


def restore_output_scale(frame: pd.DataFrame, scaling_transform: dict[str, Any] | None) -> pd.DataFrame:
    if scaling_transform is None:
        return frame
    restored_frame = frame.copy()
    restored_coords = apply_inverse_scaling(restored_frame[["x", "y", "z"]].to_numpy(dtype=float), scaling_transform)
    restored_frame[["x", "y", "z"]] = np.round(restored_coords, 6)
    restored_frame.sort_values(by=["x", "y", "z"], inplace=True)
    restored_frame.reset_index(drop=True, inplace=True)
    return restored_frame


def export_merged_csv(
    controller: OpenFoamController,
    output_csv: Path,
    fill_missing: bool,
    bounds: dict[str, int] | None,
    scaling_transform: dict[str, Any] | None,
) -> None:
    time_folders = controller.get_time_folders()
    if not time_folders:
        raise RuntimeError("No OpenFOAM time folders were produced.")
    final_time_folder = time_folders[-1]
    cell, velocity = controller.read_cell_and_velocity(final_time_folder)
    if cell is None or velocity is None:
        raise RuntimeError(f"Failed to read cell and velocity data for time {final_time_folder}.")
    frame = preprocess_velocity_dataframe(cell, velocity, fill_missing, bounds)
    frame = restore_output_scale(frame, scaling_transform)
    output_csv.parent.mkdir(parents=True, exist_ok=True)
    output_csv.unlink(missing_ok=True)
    frame.to_csv(output_csv, index=False)
    print(f"Exported final time step {final_time_folder} to {output_csv}", flush=True)


def main() -> None:
    args = parse_args()
    if not args.stl_path:
        raise SystemExit("Missing STL path. Set WR_INPUT_STL_PATH or pass --stl-path.")
    if not args.output_csv:
        raise SystemExit("Missing output CSV path. Set WR_OUTPUT_CSV_PATH or pass --output-csv.")
    if not args.config_path:
        raise SystemExit("Missing config path. Set WR_INPUT_CONFIG_PATH or pass --config-path.")

    stl_path = Path(args.stl_path)
    output_csv = Path(args.output_csv)
    config_path = Path(args.config_path)
    if not stl_path.is_file():
        raise SystemExit(f"STL file does not exist: {stl_path}")
    if not config_path.is_file():
        raise SystemExit(f"Simulation config file does not exist: {config_path}")

    config_payload = load_config_payload(config_path)
    wind_config = parse_wind_config_from_payload(config_payload)
    wind_definitions = wind_config["sources"]
    wind = aggregate_wind_definitions(wind_definitions, DEFAULT_DIRECTION_CONVENTION)
    controls = resolve_control_settings(wind)

    terrain_stl, temporary_stl, scaling_transform = maybe_scale_stl(stl_path, wind_config["scale"])
    bounds = build_simulation_bounds(terrain_stl)
    print("Resolved wind config:", json.dumps({
        "source_count": len(wind_definitions),
        "height_cells": wind_config["height_cells"],
        "scale": wind_config["scale"],
        "radius": wind_config["radius"],
    }))
    print("Resolved wind vector:", json.dumps({
        "wind_speed_x": round(wind["wind_speed_x"], 6),
        "wind_speed_y": round(wind["wind_speed_y"], 6),
        "wind_speed_z": 0.0,
        "wind_type": wind["wind_type"],
        "turb_percent": round(wind["turb_percent"], 6),
        "direction_deg": round(wind["direction_deg"], 6),
    }))
    print("Simulation bounds:", json.dumps(bounds))
    if scaling_transform is not None:
        print("Applied STL scaling:", json.dumps({
            "scale_factor": round(float(scaling_transform["scale_factor"]), 9),
            "source_bounds": scaling_transform["source_bounds"],
            "source_lengths": {
                axis: round(float(length), 6)
                for axis, length in scaling_transform["source_lengths"].items()
            },
        }))

    try:
        controller = OpenFoamController(args.case_root)
        configure_case(controller, terrain_stl, bounds, wind, controls, wind_config["height_cells"])
        controller.run()
        if not controller.check_run_valid():
            controller.debug_failed_run()
            raise RuntimeError("OpenFOAM run failed validation.")
        export_merged_csv(controller, output_csv, False, None, scaling_transform)
    finally:
        if temporary_stl is not None:
            temporary_stl.unlink(missing_ok=True)


if __name__ == "__main__":
    main()
