# Localized Wake Refinement Study

**Purpose:** Address Reviewer 2 major comment #1 — "Consider adding localized wake refinement or at least discuss limitations more explicitly."

## Approach

Instead of refining the entire domain uniformly (as in `grid_conv_study/`), this study applies **localized refinement** in the wake region using snappyHexMesh's `searchableBox` + `refinementRegions` feature.

### Refinement Strategy

| Region | Box Coordinates | Level |
|--------|----------------|-------|
| Building box | (-1,-0.7,0) to (8,0.7,2.5) | 2 (all cases) |
| Wake box | (-20,-90,0) to (20,0,50) | Varies by case |

### Case Variants

| Case | Base Mesh | Wake Level | Cells | Description |
|------|-----------|------------|-------|-------------|
| **fine_wake** | 30x50x25 | 1 | ~217K | Baseline (minimal wake refinement) |
| **coarse_wake** | 30x50x25 | 2 | ~1.34M | Moderate wake refinement |
| **medium_wake** | 30x50x25 | 3 | ~10.4M | Fine wake refinement |

**Note:** Level 4 wake refinement was attempted but exceeded available memory (~80M cells).
The wake box covers ~67% of the domain volume, so each refinement level increases cell count by ~8x.

**Key insight:** The base blockMesh (30x50x25) is identical across all cases. Only the snappyHexMesh wake refinement level varies. This isolates the effect of wake resolution on force coefficients.

## Running the Simulations

### Run All Cases

```bash
cd /home/bohanzhang/DroneWISP/run/local_refine
bash ./run_all_cases.sh
```

### Run Individual Cases

```bash
cd coarse_wake && bash ./Allclean && bash ./Allrun && cd ..
cd medium_wake && bash ./Allclean && bash ./Allrun && cd ..
cd fine_wake && bash ./Allclean && bash ./Allrun && cd ..
```

### Clean All Cases

```bash
bash ./clean_all_cases.sh
```

## Analyzing Results

After all simulations complete:

```bash
cd /home/bohanzhang/DroneWISP/run/local_refine
python local_refine_analysis.py fine_wake coarse_wake medium_wake --output results
```

This generates:
- `results/convergence_plots.png` — Convergence plots
- `results/relative_error_plot.png` — Error analysis
- `results/gci_comparison.png` — GCI comparison (uniform vs localized)
- `results/local_refine_report.txt` — Detailed comparison report
- `results/convergence_report.txt` — Standard convergence report

The script auto-detects the uniform refinement results from `../grid_conv_study/results/` for comparison.

## Success Criteria

- **Cd GCI < 5%** for the fine wake mesh (target from Reviewer 2)
- **Improvement over uniform refinement** (Cd GCI reduced from 22.27%)
- **Monotonic convergence** of force coefficients with wake refinement

## How It Works (SHM Localized Refinement)

OpenFOAM 10's `snappyHexMesh` supports localized refinement via `searchableBox` in the `geometry` section combined with `refinementRegions` in `castellatedMeshControls`:

```
geometry
{
    wakeRefinementBox
    {
        type searchableBox;
        min (-20.0 -90.0 0.0);
        max ( 20.0   0.0 50.0);
    }
};

castellatedMeshControls
{
    refinementRegions
    {
        wakeRefinementBox
        {
            mode    inside;
            level   3;  // Only cells INSIDE this box get refined
        }
    }
}
```

This refines only cells within the bounding box, keeping the far-field mesh coarse. The result is higher resolution where flow gradients are largest (near body and wake) without the computational cost of uniform global refinement.
