# Realworld CFD Validation Experiment Report

## Overview
This report documents the realworld CFD validation experiment using a dense wind station cluster and OpenFOAM. It covers data sourcing, cluster selection, CFD case setup, results, and improvements.

## Data Source
- Source: Synoptic/MesoWest API.
- Dataset file: `python/realworld/nyc_100m_1km_cluster_wind.csv`.
- Stations used: `0512W`, `0514W`, `0516W`.
- Coverage: 2026-01-01 to 2026-01-14 with 10 minute cadence and some gaps.

## Cluster Identification Process
- Objective: find three stations with spacing between 100 m and 1 km to represent an urban micro area.
- Script: `python/realworld/find_synoptic_dense_cluster.py` with `--min-distance-m 100 --max-distance-m 1000`.
- Selected cluster: Hofstra area stations `0512W`, `0514W`, `0516W`.
- Visualization: `python/realworld/nyc_100m_1km_cluster_map_vectors.png`.

## Geometry and Bounding Box
- Bounding box rules:
  - North wall passes through station `0514W`.
  - South wall is 50 m south of station `0512W`.
  - Longitude to latitude ratio is 1:2.
- Map of bounding box: `python/realworld/nyc_100m_1km_cluster_bbox.png`.
- OSM building STL: `python/realworld/nyc_100m_1km_cluster_buildings.stl`.
- STL local coordinates (origin at bounding box center):
  - `0512W`: `x=16.031`, `y=-266.102`, `z=0.0`
  - `0514W`: `x=-16.031`, `y=316.102`, `z=0.0`

## CFD Case Setup
- Case directory: `run/realworld`.
- Template: `run/house_inspection`.
- Mesh:
  - Base domain in `system/blockMeshDict` set to `x=±158.051`, `y=±316.102`, `z=0..1`.
  - Refinement box in `system/snappyHexMeshDict` matches the domain.
  - STL used in `constant/geometry/nyc_100m_1km_cluster_buildings.stl`.
- Boundary conditions:
  - `0/U.orig` uses uniform wind inlet and back (fixedValue).
    - Inlet velocity taken from station `0512W` at `2026-01-09T17:30:00Z`.
    - `flowVelocity` in `0/include/initialConditions`: `(-1.6086 6.9677 0)`.
- Probe:
  - `system/controlDict` probe at `(-16.031 316.102 0.5)` corresponding to `0514W`.
- Solver: `simpleFoam`.

## Result and Error Assessment
- Script: `run/realworld/report_error.sh` and `run/realworld/report_error.py`.
- Comparison:
  - Extracts CFD velocity at the probe using nearest cell sampling.
  - Compares against observation vector for `0512W` at the configured timestamp.
  - Reports vector error and speed error.

Latest run summary using 0512W inflow and 0514W probe:
- CFD probe (U): `(0.968808, 6.97076, 0.000721532)`
- Observed wind (U): `(-1.609, 6.968, 0.0)`
- Vector error: `2.577`
- Speed error: `0.113`
- Probe time: `1.0`
- Observation timestamp: `2026-01-09T17:30:00Z`


## Implications
- This setup demonstrates a direct pointwise comparison between measured wind vectors and CFD output in an urban micro domain.
- The probe result highlights the sensitivity of local flow to boundary conditions and building-induced deflection.
- The workflow establishes a baseline for iterating on inflow definitions and mesh fidelity.

## Potential Improvements
- Increase domain height to reduce top boundary influence on the probe signal.
- Add more probes around the cluster to quantify directional bias from the geometry.
- Refine near-building cells to capture recirculation that can rotate the flow.
- Consider transient runs aligned to observation timestamps if time-resolved comparison is needed.

