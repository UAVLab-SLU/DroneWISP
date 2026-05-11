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
- it receives one simulation config JSON file
- it writes one output CSV
- it exits when the job is complete

## Required Inputs

WR must provide these values:

| Variable | Meaning |
| --- | --- |
| `WR_INPUT_STL_DIR` | Host directory that contains the terrain STL |
| `WR_INPUT_STL_FILE` | STL filename inside `WR_INPUT_STL_DIR` |
| `WR_INPUT_CONFIG_DIR` | Host directory that contains the simulation config JSON |
| `WR_INPUT_CONFIG_FILE` | Config filename inside `WR_INPUT_CONFIG_DIR` |
| `WR_OUTPUT_DIR` | Host directory where the result CSV will be written |
| `WR_OUTPUT_FILE` | Output CSV filename inside `WR_OUTPUT_DIR` |

## Optional Inputs

WR does not need to provide separate wind JSON, bounds JSON, control JSON, padding JSON, or preprocess parameters.

## Config Contract

The runner reads wind definitions from the single config file.

Expected location:
- `environment.wind.sources`

The runner also accepts the older `environment.wind` array and a top-level `wind` field for backward compatibility.

Current wind object shape:

```json
{
  "environment": {
    "origin": {
      "radius": 0.3
    },
    "wind": {
      "sources": [
        {
          "wind_velocity": 4.2,
          "wind_direction": "NE",
          "wind_type": "Constant Wind",
          "fluctuation_percentage": 5.5
        }
      ],
      "height_cells": 10,
      "scale": 1.0
    }
  }
}
```

Config fields:

| Field | Meaning | Default |
| --- | --- | --- |
| `environment.wind.sources` | Wind source array | required in the new schema |
| `environment.wind.height_cells` | Number of CFD cells in the vertical direction | `10` |
| `environment.wind.scale` | Uniform STL scale factor in `(0, 1]` | `1.0` |
| `environment.origin.radius` | Region radius from the simulation config | unchanged |

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

## Mesh Scale And Height Cells

`environment.wind.scale` is the config-controlled computation limit.

There is no hardcoded maximum effective `x` or `y` cell count in the runner; WR controls that through the config value.

When `scale` is less than `1.0`:
- the full STL is uniformly scaled by that factor in `x`, `y`, and `z`
- the STL is not sliced or clipped
- triangle count stays unchanged
- exported `x,y,z` coordinates are mapped back to the original STL scale
- the solver adds a small fixed clearance around the STL, so exported coordinates can extend slightly beyond the STL extents after inverse scaling

Example:
- input STL `x`: `400`
- configured `scale`: `0.5`
- solver-scale `x`: `200`

`environment.wind.height_cells` is used directly as the CFD `z` cell count. It is not multiplied by `scale`.

The input STL is expected to be box-like in most runs, with `z` usually being the least predictable dimension.

## Output Contract

The container writes exactly one CSV file to:

`WR_OUTPUT_DIR/WR_OUTPUT_FILE`

The CSV contains only the final time step.

CSV header:

```csv
x,y,z,u,v,w
```

Column meanings:
- `x`, `y`, `z`: output location in the source STL coordinate scale
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
      WR_INPUT_CONFIG_DIR: /host/config
      WR_INPUT_CONFIG_FILE: sim_config_3_drone_new.json
      WR_OUTPUT_DIR: /host/output
      WR_OUTPUT_FILE: wind.csv
    volumes:
      - /host/input:/wr/input:ro
      - /host/config:/wr/config:ro
      - /host/output:/wr/output
```

## Example Config Fragment

```json
{
  "environment": {
    "origin": {
      "radius": 0.3
    },
    "wind": {
      "sources": [
        {
          "wind_velocity": 5,
          "wind_direction": "W",
          "wind_type": "Constant Wind",
          "fluctuation_percentage": 0.0
        },
        {
          "wind_velocity": 3,
          "wind_direction": "SE",
          "wind_type": "Constant Wind",
          "fluctuation_percentage": 0.0
        }
      ],
      "height_cells": 10,
      "scale": 1.0
    }
  }
}
```
