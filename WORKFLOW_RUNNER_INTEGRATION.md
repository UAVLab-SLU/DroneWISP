# Workflow Runner Integration Interface

This document defines the external batch interface expected by Workflow Runner (WR).

It describes only the integration contract:
- required inputs
- optional inputs
- output format
- runtime behavior

## Compose Reference

Use [`compose.workflow-runner.yaml`](//wsl.localhost/Ubuntu-22.04/home/bohanzhang/DroneWISP/compose.workflow-runner.yaml:1) as the service reference when adding the WR service template entry.

The WR-facing service is a one-shot batch job:
- it receives an STL terrain file
- it receives wind input as JSON
- it writes one output CSV
- it exits when the job is complete

## Required Inputs

WR must provide these values:

| Variable | Meaning |
| --- | --- |
| `WR_INPUT_STL_DIR` | Host directory that contains the terrain STL |
| `WR_INPUT_STL_FILE` | STL filename inside `WR_INPUT_STL_DIR` |
| `WR_OUTPUT_DIR` | Host directory where the result CSV will be written |
| `WR_OUTPUT_FILE` | Output CSV filename inside `WR_OUTPUT_DIR` |
| `WR_WIND_JSON` | Wind definition JSON |

## Optional Inputs

WR may provide these values when needed:

| Variable | Meaning | Default |
| --- | --- | --- |
| `WR_DIRECTION_CONVENTION` | Interpret wind direction as `to` or `from` | `to` |
| `WR_CONTROL_JSON` | Optional runtime control JSON with `dt`, `end_time`, `write_interval` | internal defaults |
| `WR_BOUNDS_JSON` | Optional clipping / simulation bounds JSON | auto-derived from STL |
| `WR_MESH_PADDING_JSON` | Optional padding JSON used only when bounds are auto-derived | `{"xy":1,"z_min":1,"z_max":1}` |
| `WR_FILL_MISSING` | Whether to backfill missing integer grid cells in the exported CSV | `false` |

WR should not provide any preprocess-mode parameter.

## Wind Input Contract

`WR_WIND_JSON` may be:
- a single wind object
- an array of wind objects
- a larger JSON object that contains `wind`
- a larger JSON object that contains `environment.wind`

Minimum required fields for each wind object:

```json
{
  "wind_velocity": 4.2,
  "wind_direction": "NE"
}
```

Supported optional fields:

```json
{
  "wind_velocity": 4.2,
  "wind_direction": "NE",
  "wind_type": "Constant Wind",
  "fluctuation_percentage": 5.5
}
```

Accepted `wind_direction` forms:
- compass direction such as `N`, `NE`, `SW`
- numeric degrees

Accepted wind type behavior:
- values containing `Turbulent` are treated as turbulent
- all other values are treated as non-turbulent

## Multi-Source Wind Behavior

If multiple wind definitions are supplied:
- wind vectors are averaged component-wise into one effective wind vector
- if any source is turbulent, the merged run is treated as turbulent
- `fluctuation_percentage` is taken as the maximum provided value among the sources
- if turbulence is selected but no positive fluctuation is given, a default turbulence percentage is used internally

## Bounds Contract

If `WR_BOUNDS_JSON` is supplied, it must be:

```json
{
  "x_min": -16,
  "x_max": 16,
  "y_min": -16,
  "y_max": 16,
  "z_min": -2,
  "z_max": 11
}
```

If `WR_BOUNDS_JSON` is not supplied:
- bounds are auto-derived from the STL
- `WR_MESH_PADDING_JSON` is applied

## Output Contract

The container writes exactly one CSV file to:

`WR_OUTPUT_DIR/WR_OUTPUT_FILE`

The CSV contains only the final time step.

CSV header:

```csv
x,y,z,u,v,w
```

Column meanings:
- `x`, `y`, `z`: integer grid location
- `u`, `v`, `w`: velocity components at that grid point

No `time` column is written.

## Exit Behavior

- exit code `0` means the job completed and the CSV was written
- nonzero exit means WR should treat the job as failed

WR should treat the output CSV as the only required artifact.

## Example Service Shape

This is the intended integration shape on the WR side:

```yaml
services:
  wisp_wr_job:
    image: dronewisp_wr
    environment:
      WR_INPUT_STL_DIR: /host/input
      WR_INPUT_STL_FILE: terrain.stl
      WR_OUTPUT_DIR: /host/output
      WR_OUTPUT_FILE: wind.csv
      WR_WIND_JSON: '[{"wind_velocity":4.2,"wind_direction":"NE"}]'
      WR_DIRECTION_CONVENTION: to
    volumes:
      - /host/input:/wr/input:ro
      - /host/output:/wr/output
```

## Example Wind Payloads

Single-source example:

```json
[
  {
    "wind_velocity": 4.2,
    "wind_direction": "NE",
    "wind_type": "Constant Wind",
    "fluctuation_percentage": 5.5
  }
]
```

Multi-source example:

```json
[
  {
    "wind_velocity": 4.2,
    "wind_direction": "NE",
    "wind_type": "Constant Wind",
    "fluctuation_percentage": 5.5
  },
  {
    "wind_velocity": 6.0,
    "wind_direction": "SW",
    "wind_type": "Turbulent Wind",
    "fluctuation_percentage": 40.0
  }
]
```
