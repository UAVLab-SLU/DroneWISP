# WR Runtime Estimation

This note documents the measured run sizes and runtimes for the current Workflow Runner batch interface.

## Scope

- Input style: one STL, one simulation config JSON, one output CSV
- Geometry assumption: the STL is box-like in `x` and `y`
- User-known inputs: `x` and `y`
- Unknown at request time: `z`, which is determined later during terrain scanning

## Measurement Method

- Each benchmark was run through `docker compose` with the current WR interface.
- "Cells" below means the number of exported data rows in the final CSV, excluding the header.
- The exported CSV writes one row per final cell-centre sample, so this is the most practical cell-count measure for WR-side estimation.

## Lookup Table

| Input `x` | Input `y` | `wind.scale` | Effective `x` | Effective `y` | Exported cells | Time (sec) | Time (min) | Notes |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 30 | 30 | 1.0 | 30 | 30 | 15,021 | 191.026 | 3.18 | Full scale |
| 100 | 100 | 1.0 | 100 | 100 | 145,277 | 276.732 | 4.61 | Full scale |
| 400 | 400 | 0.5 | 200 | 200 | 364,797 | 1,019.100 | 16.99 | Configured scale reduces horizontal size |

## Scale Rule

The runner uses `environment.wind.scale` from the simulation config.

Use:

```text
s = wind.scale
x_eff = x * s
y_eff = y * s
A_eff = x_eff * y_eff
```

Where:

- `s` is the STL scale factor applied by the runner, in `(0, 1]`
- `x_eff` and `y_eff` are the effective post-scale dimensions
- `A_eff` is the effective post-scale area used for runtime estimation
- `wind.height_cells` controls vertical CFD cells directly and is not multiplied by `s`

## Estimated Cells From `x` and `y`

Empirical fit from the benchmark table:

```text
cells_est ~= -0.000178938947 * A_eff^2
            + 16.2642807 * A_eff
            + 528.08794
```

This is useful when only `x` and `y` are known before terrain scanning finishes.

## Estimated Time From Cells

Empirical fit from the benchmark table:

```text
time_sec_est ~= 7.78726162e-09 * cells_est^2
               - 5.90301256e-04 * cells_est
               + 198.135872
```

## Direct `x,y`-Only Runtime Formula

For WR-side planning, the most convenient form is the combined formula below.

```text
time_sec_est ~= 3.92004047e-07 * A_eff^2
               + 0.00514539764 * A_eff
               + 186.077619
```

Equivalent minutes form:

```text
time_min_est ~= 6.53340078e-09 * A_eff^2
               + 8.57566273e-05 * A_eff
               + 3.10129365
```

## Example

For an input STL with:

```text
x = 400
y = 400
```

Then:

```text
wind.scale = 0.5
s = 0.5
x_eff = 400 * 0.5 = 200
y_eff = 400 * 0.5 = 200
A_eff = 200 * 200 = 40,000
```

Estimated runtime:

```text
time_sec_est ~= 1,019 seconds
time_min_est ~= 17.0 minutes
```

Which matches the measured benchmark closely.

## Limitations

- This is an empirical estimate, not a physics-based law.
- It is based on the current Docker image, current solver settings, and the current box-like benchmark geometries.
- If the scanned terrain produces a much larger or more complex `z` profile than these benchmarks, the real runtime can be higher.
- The runner adds a small fixed CFD clearance around the STL, so exported coordinates can extend slightly beyond the STL extents after inverse scaling.
