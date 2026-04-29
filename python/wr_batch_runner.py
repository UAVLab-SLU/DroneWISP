import argparse
import json
import math
import os
import tempfile
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from my_stl.mesh_utils import StlMeshUtils
from open_foam_controller import OpenFoamController


DEFAULT_PADDING = {"xy": 1, "z_min": 1, "z_max": 1}
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
    parser.add_argument("--wind-json", default=os.getenv("WR_WIND_JSON"))
    parser.add_argument("--case-root", default=os.getenv("WR_CASE_ROOT", "openFoamCase"))
    parser.add_argument("--preprocess-mode", default=os.getenv("WR_PREPROCESS_MODE", "int_precision"))
    parser.add_argument(
        "--direction-convention",
        default=os.getenv("WR_DIRECTION_CONVENTION", "to"),
        choices=["to", "from"],
    )
    parser.add_argument("--control-json", default=os.getenv("WR_CONTROL_JSON"))
    parser.add_argument("--bounds-json", default=os.getenv("WR_BOUNDS_JSON"))
    parser.add_argument("--mesh-padding-json", default=os.getenv("WR_MESH_PADDING_JSON"))
    parser.add_argument("--fill-missing", default=os.getenv("WR_FILL_MISSING", "false"))
    return parser.parse_args()


def parse_bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if value is None:
        return False
    return str(value).strip().lower() in {"1", "true", "yes", "on"}


def parse_json(value: str | None, label: str) -> Any:
    if value in (None, ""):
        return None
    try:
        return json.loads(value)
    except json.JSONDecodeError as exc:
        raise ValueError(f"Invalid JSON for {label}: {exc}") from exc


def parse_wind_payload(wind_json: str | None) -> list[dict[str, Any]]:
    payload = parse_json(wind_json, "wind_json")
    if payload is None:
        raise ValueError("WR_WIND_JSON or --wind-json is required.")
    if isinstance(payload, dict):
        if isinstance(payload.get("environment"), dict) and "wind" in payload["environment"]:
            payload = payload["environment"]["wind"]
        elif "wind" in payload:
            payload = payload["wind"]
        else:
            payload = [payload]
    if not isinstance(payload, list) or not payload:
        raise ValueError("Wind payload must be a non-empty object or array.")
    normalized: list[dict[str, Any]] = []
    for item in payload:
        if not isinstance(item, dict):
            raise ValueError("Each wind definition must be an object.")
        normalized.append(item)
    return normalized


def parse_padding(padding_json: str | None) -> dict[str, int]:
    if padding_json in (None, ""):
        return DEFAULT_PADDING.copy()
    payload = parse_json(padding_json, "mesh_padding_json")
    if isinstance(payload, (int, float)):
        padding_value = int(math.ceil(float(payload)))
        return {"xy": padding_value, "z_min": padding_value, "z_max": padding_value}
    if not isinstance(payload, dict):
        raise ValueError("mesh_padding_json must be a number or object.")
    xy = int(math.ceil(float(payload.get("xy", 0))))
    return {
        "xy": xy,
        "z_min": int(math.ceil(float(payload.get("z_min", payload.get("z", 0))))),
        "z_max": int(math.ceil(float(payload.get("z_max", payload.get("z", 0))))),
    }


def normalize_bounds(bounds_payload: dict[str, Any]) -> dict[str, int]:
    required_keys = ["x_min", "x_max", "y_min", "y_max", "z_min", "z_max"]
    missing = [key for key in required_keys if key not in bounds_payload]
    if missing:
        raise ValueError(f"Bounds JSON is missing keys: {', '.join(missing)}")
    bounds = {
        "x_min": math.floor(float(bounds_payload["x_min"])),
        "x_max": math.ceil(float(bounds_payload["x_max"])),
        "y_min": math.floor(float(bounds_payload["y_min"])),
        "y_max": math.ceil(float(bounds_payload["y_max"])),
        "z_min": math.floor(float(bounds_payload["z_min"])),
        "z_max": math.ceil(float(bounds_payload["z_max"])),
    }
    if bounds["x_min"] >= bounds["x_max"] or bounds["y_min"] >= bounds["y_max"] or bounds["z_min"] >= bounds["z_max"]:
        raise ValueError("Bounds min values must be smaller than max values.")
    return bounds


def load_mesh_bounds(stl_path: Path) -> tuple[float, float, float, float, float, float]:
    mesh_utils = StlMeshUtils()
    mesh_utils.pv_load_convert_mesh(str(stl_path))
    if mesh_utils.pv_mesh is None:
        raise RuntimeError(f"Failed to load STL mesh: {stl_path}")
    return tuple(mesh_utils.pv_mesh.bounds)


def build_auto_bounds(stl_path: Path, padding: dict[str, int]) -> dict[str, int]:
    mesh_bounds = load_mesh_bounds(stl_path)
    return {
        "x_min": math.floor(mesh_bounds[0]) - padding["xy"],
        "x_max": math.ceil(mesh_bounds[1]) + padding["xy"],
        "y_min": math.floor(mesh_bounds[2]) - padding["xy"],
        "y_max": math.ceil(mesh_bounds[3]) + padding["xy"],
        "z_min": math.floor(mesh_bounds[4]) - padding["z_min"],
        "z_max": math.ceil(mesh_bounds[5]) + padding["z_max"],
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


def maybe_clip_stl(source_stl: Path, bounds: dict[str, int], explicit_bounds: bool) -> tuple[Path, Path | None]:
    if not explicit_bounds:
        return source_stl, None
    vertices = build_box_vertices(bounds)
    handle, temp_path = tempfile.mkstemp(prefix="dronewisp_wr_", suffix=".stl")
    os.close(handle)
    clipped_stl = Path(temp_path)
    StlMeshUtils.clip_and_save_mesh(vertices, str(source_stl), str(clipped_stl))
    return clipped_stl, clipped_stl


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


def resolve_control_settings(aggregate_wind: dict[str, Any], control_json: str | None) -> dict[str, float | int]:
    if aggregate_wind["wind_type"] == "turbulent":
        resolved: dict[str, float | int] = {"dt": 1.0, "end_time": 26.0, "write_interval": 1}
    else:
        resolved = {"dt": 1.0, "end_time": 51.0, "write_interval": 50}
    payload = parse_json(control_json, "control_json")
    if payload is None:
        return resolved
    if not isinstance(payload, dict):
        raise ValueError("control_json must be an object.")
    if "dt" in payload:
        resolved["dt"] = float(payload["dt"])
    if "end_time" in payload:
        resolved["end_time"] = float(payload["end_time"])
    if "write_interval" in payload:
        resolved["write_interval"] = int(payload["write_interval"])
    return resolved


def configure_case(
    controller: OpenFoamController,
    terrain_stl: Path,
    bounds: dict[str, int],
    wind: dict[str, Any],
    controls: dict[str, float | int],
) -> None:
    vertices = build_box_vertices(bounds)
    x_size = bounds["x_max"] - bounds["x_min"] + 1
    y_size = bounds["y_max"] - bounds["y_min"] + 1
    z_size = bounds["z_max"] - bounds["z_min"] + 1
    if max(x_size, y_size, z_size) > 200:
        print(
            "Warning: simulation box is large. Consider passing WR_BOUNDS_JSON with a tighter region or a pre-clipped STL."
        )
        print(f"Simulation box size: {x_size} x {y_size} x {z_size}")

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


def export_merged_csv(
    controller: OpenFoamController,
    output_csv: Path,
    fill_missing: bool,
    bounds: dict[str, int] | None,
) -> None:
    frames: list[pd.DataFrame] = []
    time_folders = controller.get_time_folders()
    if not time_folders:
        raise RuntimeError("No OpenFOAM time folders were produced.")
    for time_folder in time_folders:
        cell, velocity = controller.read_cell_and_velocity(time_folder)
        if cell is None or velocity is None:
            raise RuntimeError(f"Failed to read cell and velocity data for time {time_folder}.")
        frame = preprocess_velocity_dataframe(cell, velocity, fill_missing, bounds)
        frame.insert(0, "time", float(time_folder))
        frames.append(frame)
    merged = pd.concat(frames, ignore_index=True)
    output_csv.parent.mkdir(parents=True, exist_ok=True)
    merged.to_csv(output_csv, index=False)
    print(f"Saved merged CSV to {output_csv}")


def main() -> None:
    args = parse_args()
    if not args.stl_path:
        raise SystemExit("Missing STL path. Set WR_INPUT_STL_PATH or pass --stl-path.")
    if not args.output_csv:
        raise SystemExit("Missing output CSV path. Set WR_OUTPUT_CSV_PATH or pass --output-csv.")

    stl_path = Path(args.stl_path)
    output_csv = Path(args.output_csv)
    if not stl_path.is_file():
        raise SystemExit(f"STL file does not exist: {stl_path}")

    wind_definitions = parse_wind_payload(args.wind_json)
    wind = aggregate_wind_definitions(wind_definitions, args.direction_convention)
    controls = resolve_control_settings(wind, args.control_json)
    fill_missing = parse_bool(args.fill_missing)

    bounds_payload = parse_json(args.bounds_json, "bounds_json")
    explicit_bounds = bounds_payload is not None
    if explicit_bounds:
        if not isinstance(bounds_payload, dict):
            raise SystemExit("bounds_json must be an object.")
        bounds = normalize_bounds(bounds_payload)
    else:
        bounds = build_auto_bounds(stl_path, parse_padding(args.mesh_padding_json))

    terrain_stl, temporary_stl = maybe_clip_stl(stl_path, bounds, explicit_bounds)
    print("Resolved wind vector:", json.dumps({
        "wind_speed_x": round(wind["wind_speed_x"], 6),
        "wind_speed_y": round(wind["wind_speed_y"], 6),
        "wind_speed_z": 0.0,
        "wind_type": wind["wind_type"],
        "turb_percent": round(wind["turb_percent"], 6),
        "direction_deg": round(wind["direction_deg"], 6),
    }))
    print("Simulation bounds:", json.dumps(bounds))

    try:
        controller = OpenFoamController(args.case_root, args.preprocess_mode)
        configure_case(controller, terrain_stl, bounds, wind, controls)
        controller.run()
        if not controller.check_run_valid():
            controller.debug_failed_run()
            raise RuntimeError("OpenFOAM run failed validation.")
        export_merged_csv(controller, output_csv, fill_missing, bounds if fill_missing else None)
    finally:
        if temporary_stl is not None:
            temporary_stl.unlink(missing_ok=True)


if __name__ == "__main__":
    main()
