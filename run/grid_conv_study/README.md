# Grid Convergence Study Cases

This directory contains three mesh variants of the `tallBuilding` case for performing a grid convergence study.

## Mesh Variants

| Case | Cell Counts (nx × ny × nz) | Base Cells | Refinement Ratio |
|------|---------------------------|------------|------------------|
| **coarse** | 15 × 25 × 12 | 4,500 | 0.5× (baseline) |
| **medium** | 30 × 50 × 25 | 37,500 | 1.0× (original) |
| **fine** | 60 × 100 × 50 | 300,000 | 2.0× |

**Refinement ratio**: Each level has 2× more cells in each direction (8× total cells per level).

## Running the Simulations

### Option 1: Run All Simulations Automatically (Recommended)

Run all cases sequentially with a single command:

```bash
cd /home/bohanzhang/DroneWISP/run/grid_conv_study
bash ./run_all_simulations.sh
```

This script will:
- Run each case in order (coarse → medium → fine)
- Clean previous results before each run
- Report completion time for each case
- Verify that results were generated

### Option 2: Run Each Case Manually

Run each case independently:

```bash
# Coarse mesh
cd coarse
bash ./Allclean
bash ./Allrun

# Medium mesh
cd ../medium
bash ./Allclean
bash ./Allrun

# Fine mesh
cd ../fine
bash ./Allclean
bash ./Allrun
```

### Cleaning All Simulations

To clean all simulation results at once:

```bash
cd /home/bohanzhang/DroneWISP/run/grid_conv_study
bash ./clean_all_simulations.sh
```

This will clean all three cases (coarse, medium, fine) by running `Allclean` in each directory.

**Note**: Each finer mesh takes approximately 8× longer to run than the previous level.

## Expected Computational Time

- **Coarse**: ~1× baseline time
- **Medium**: ~8× baseline time
- **Fine**: ~64× baseline time

**Total**: ~73× the time of a single coarse simulation

## Analyzing Results

**Important**: Make sure all simulations have completed before running the analysis!

After all simulations complete, run the convergence analysis:

```bash
cd /home/bohanzhang/DroneWISP/run
python grid_convergence_analysis.py \
    grid_conv_study/coarse \
    grid_conv_study/medium \
    grid_conv_study/fine \
    --output grid_conv_study/results
```

This will generate:
- `grid_conv_study/results/convergence_plots.png` - Convergence plots
- `grid_conv_study/results/relative_error_plot.png` - Error analysis
- `grid_conv_study/results/convergence_report.txt` - Detailed report

**Note**: If you run the analysis before simulations are complete, the script will provide clear error messages indicating which cases need to be run.

## Quantities Monitored

The analysis will extract and compare:
- **Force coefficients**: Cd (drag), Cl (lift), Cm (moment)
- **Cell counts**: Total mesh cells after snappyHexMesh
- **Convergence metrics**: GCI, order of accuracy, convergence ratio

## Success Criteria

A successful grid convergence study should show:
- **GCI < 5%** for force coefficients on the fine mesh
- **Monotonic convergence** (values approach a limit)
- **Order of accuracy p ≈ 1.5-2.5** for RANS simulations
- **Relative error** decreases with each refinement level

## Case Structure

Each case is a complete, independent OpenFOAM case with:
- Modified `system/blockMeshDict` with appropriate cell counts
- Original `system/snappyHexMeshDict` (unchanged)
- All boundary conditions and solver settings from `tallBuilding`
- Clean state (no previous results)

## Notes

- All cases use the same geometry, boundary conditions, and solver settings
- Only the base mesh resolution (blockMesh) is varied
- snappyHexMesh refinement levels remain constant across all cases
- Results are extracted from `postProcessing/forceCoeffs1/0/forceCoeffs.dat`

## Troubleshooting

### Common Issues

**Error: "cannot find file processorX/0/p"**
- This means the initial conditions weren't properly decomposed
- Fix by running: `bash ./fix_cases.sh`
- This will ensure the 0 directory exists and is properly distributed to all processors

**If a simulation fails:**
1. Check `log.simpleFoam` for errors
2. Run `checkMesh` to verify mesh quality
3. Ensure sufficient computational resources for fine mesh
4. Verify OpenFOAM environment is properly sourced
5. If processor directories are missing initial conditions, run `bash ./fix_cases.sh`

### Fixing Cases

If cases need to be fixed (e.g., missing 0 directory or processor files), run:

```bash
cd /home/bohanzhang/DroneWISP/run/grid_conv_study
bash ./fix_cases.sh
```

This script will:
- Ensure the 0 directory exists in each case
- Clean processor directories and logs
- Run blockMesh to create the base mesh
- Run decomposePar -copyZero to distribute initial conditions
- Verify that all processor directories have the necessary files

