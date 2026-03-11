# Localized Wake Refinement: Performance Comparison

**Purpose:** Demonstrate that localized wake refinement on a coarse base mesh can approximate fine uniform mesh accuracy at a fraction of the computational cost.

## Approach

| Case | Base Mesh | Wake Refinement | Description |
|------|-----------|----------------|-------------|
| **fine_uniform** | 60x100x50 | None (level 2 building box only) | Fully refined reference |
| **coarse_local_wake** | 15x25x12 | (-20,-90,0) to (20,0,50) at level 2 | Coarse base + local wake |

Both cases use:
- Same geometry (`combined.stl`)
- Same solver settings (simpleFoam, kOmegaSST)
- Same boundary conditions
- Same SHM building refinement box at level 2

The **only** difference: `coarse_local_wake` uses 1/8th the base mesh cells but adds a `wakeRefinementBox` covering x(-20,20), y(-90,0), z(0,50) at refinement level 2, concentrating resolution in the wake region.

## Running

```bash
cd /home/bohanzhang/DroneWISP/run/local_refine_performance
bash ./run_all_cases.sh
```

Then analyze:

```bash
python performance_analysis.py
```

## Outputs

- `results/performance_report.txt` — Detailed comparison (cells, time, Cd/Cl/Cm)
- `results/performance_comparison.png` — Bar chart comparison
- `results/timing.txt` — Raw timing data

## Key Metrics

- **Cell ratio**: fine_uniform cells / coarse_local_wake cells
- **Speedup**: fine_uniform time / coarse_local_wake time
- **Accuracy**: relative difference in Cd, Cl, Cm between the two approaches
- **Efficiency**: accuracy achieved per unit of computational cost
