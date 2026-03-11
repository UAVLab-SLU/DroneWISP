# Realworld CFD Validation — Multi-Timestamp T1 Report

## Overview
This report documents the second-timestamp (T1) realworld CFD validation experiment, reusing the same geometry and mesh as the original `run/realworld` case but with a different inflow condition derived from a different observation time. This addresses Reviewer 2 major comment #2 requesting multi-timestamp validation.

## Relationship to Original Case
- Original case: `run/realworld` — timestamp `2026-01-09T17:30:00Z`.
- This case: `run/realworld_t1` — timestamp `2026-01-09T15:30:00Z`.
- Same geometry (`nyc_100m_1km_cluster_buildings.stl`), same mesh, same solver settings.
- Only the inlet velocity (derived from station `0512W`) differs.

## Data Source
- Source: Synoptic/MesoWest API.
- Dataset file: `python/realworld/nyc_100m_1km_cluster_wind.csv`.
- Stations: `0512W` (inlet), `0514W` (probe/validation).
- Timestamp: `2026-01-09T15:30:00Z`.

## Inflow Condition
- Station `0512W` at `2026-01-09T15:30:00Z`: speed = 6.703 m/s, direction = 149°.
- Decomposed: `u = -3.4523 m/s`, `v = 5.7456 m/s`.
- `flowVelocity` in `0/include/initialConditions`: `(-3.4523 5.7456 0)`.

## Geometry and Bounding Box
- Identical to original case.
- Bounding box: north wall through `0514W`, south wall 50 m south of `0512W`, lon:lat = 1:2.
- STL: `constant/geometry/nyc_100m_1km_cluster_buildings.stl`.
- Probe at `0514W` local coordinates: `(-16.031, 316.102, 0.5)`.
- Map: `python/realworld/nyc_100m_1km_cluster_bbox_t1.png`.

## CFD Case Setup
- Template: cloned from `run/realworld` (which used `run/house_inspection` as base).
- Mesh: base domain `x=±158.051`, `y=±316.102`, `z=0..1`.
- Solver: `simpleFoam`, parallel on 6 processors.
- Turbulence: k-omega SST, `k=0.330`, `omega=10.0`.

## Result and Error Assessment
- Script: `run/realworld_t1/report_error.sh` and `run/realworld_t1/report_error.py`.
- Comparison at probe location (nearest cell to `0514W`):

| Quantity | T0 (17:30 UTC) | T1 (15:30 UTC) |
|---|---|---|
| Inlet station | 0512W | 0512W |
| Inlet speed (m/s) | 7.155 | 6.703 |
| Inlet direction (°) | 167 | 149 |
| CFD probe U (m/s) | (0.969, 6.971, 0.001) | (-0.911, 5.747, 0.001) |
| Observed U (m/s) | (-1.609, 6.968, 0.0) | (-3.452, 5.746, 0.0) |
| Vector error (m/s) | 2.577 | 2.541 |
| Speed error (m/s) | 0.113 | 0.884 |
| Best timestep | 1.0 | 1.0 |

## Discussion
- The vector error is comparable across both timestamps (~2.5 m/s), indicating consistent model behaviour rather than a one-off agreement.
- At T1 the wind has a stronger cross-flow component (direction shifts from 167° to 149°), yet the CFD still captures the v-component well (5.747 vs 5.746) while under-predicting the u-component magnitude (-0.911 vs -3.452).
- The speed error is larger at T1 (0.884 vs 0.113 m/s) because the directional deflection by buildings is more pronounced with the shifted inflow angle.
- Both timestamps show that building-induced flow deflection is the dominant source of error, consistent with the coarse mesh limitations discussed in the grid convergence study.

## Conclusion
The multi-timestamp comparison provides limited but broader evidence that the simulation pipeline produces physically plausible results across different wind conditions at the same urban location. The consistent vector error magnitude (~2.5 m/s) across two timestamps with different inflow angles supports the feasibility of the approach while highlighting the directional sensitivity as a key area for future refinement.
