# Drone Wind Force Study

This directory contains OpenFOAM cases and utilities for studying wind forces on drone models using a **Blended Drag Model** approach.

## Overview

The goal is to calculate wind force coefficients for drone models that can be used to predict aerodynamic forces for any wind direction. The analysis uses a **Blended Drag Model** that correctly accounts for cross-flow effects and total airflow energy.

### Key Features

- **3 Principal Direction Simulations**: Only 3 CFD simulations needed (front-back, left-right, top-down)
- **Blended Drag Model**: Physically correct formula that accounts for total velocity magnitude
- **Automated Analysis**: Single script runs all simulations and generates coefficients
- **Ready-to-Use Formula**: Python implementation provided for integration into flight simulators

## Directory Structure

```
drone_model_study/
├── obj/                    # Original OBJ drone model files
├── stl/                    # Converted STL drone model files (scaled to meters)
├── case_front_back/        # OpenFOAM case: X-direction wind (15 m/s)
├── case_left_right/        # OpenFOAM case: Y-direction wind (15 m/s)
├── case_top_down/          # OpenFOAM case: Z-direction wind (15 m/s)
├── openfoam_case/          # Template case directory (not used directly)
├── analyze_drone_model.py  # Main analysis script
├── analyze_existing_results.py  # Analyze results without re-running
├── convert_obj_to_stl.py   # Convert OBJ to STL format
├── scale_stl_to_meters.py  # Scale STL from cm to meters
├── clean_all_cases.sh      # Clean all OpenFOAM cases
├── run_analysis.sh         # Wrapper script for analyze_drone_model.py
├── *_analysis.txt          # Analysis results (generated)
└── README.md               # This file
```

## Quick Start

### 1. Convert OBJ to STL (if needed)

```bash
python3 convert_obj_to_stl.py
```

This converts all OBJ files in `obj/` to STL format in `stl/`.

### 2. Scale STL to Meters (if needed)

By default, Unreal Engine exports OBJ files in centimeters.
STL files must be in meters for OpenFOAM. If your STL is in centimeters:

```bash
python3 scale_stl_to_meters.py stl/AureliaX6Pro2_core_Internal.stl
python3 scale_stl_to_meters.py stl/WhiteQuadrotor1_Internal.stl
```

### 3. Analyze a Drone Model

**Using the wrapper script (recommended):**

```bash
./run_analysis.sh AureliaX6Pro2_core_Internal.stl
```

**Custom wind speed:**


By default, the wind speed is 15 m/s. This wind speed is used to calculate the drag coefficients and the reference forces at this speed.

To change the wind speed, use the `--wind-speed` flag:

```bash
../../python/venv/bin/python3 analyze_drone_model.py model.stl --wind-speed 15.0
```

The script will:
1. Clean all 3 OpenFOAM cases
2. Copy STL to each case
3. Run simulations for front-back, left-right, and top-down directions
4. Extract force data from each simulation
5. Calculate drag coefficients (Dx, Dy, Dz)
6. Generate a formula and Python implementation
7. Save results to `<model_name>_analysis.txt`

### 4. Analyze Existing Results (without re-running)

If simulations have already been run, you can analyze results without re-running:

```bash
../../python/venv/bin/python3 analyze_existing_results.py case_front_back
```

### 5. Clean All Cases

To clean all OpenFOAM cases (remove mesh, results, etc.):

```bash
./clean_all_cases.sh
```

## The Blended Drag Model

### Physics Background

The **Blended Drag Model** is a corrected physics approach that addresses a flaw in simple interpolation methods. Traditional methods treat X, Y, Z drag independently, which fails when there's significant cross-flow.

**Example Problem:**
- Drone falling at 20 m/s (vz=-20) while moving forward at 1 m/s (vx=1)
- Old formula: Fx based only on 1 m/s → predicts almost zero X-drag
- Reality: The 20 m/s vertical flow creates turbulent wake, increasing X-drag
- New formula: Uses total speed ||V|| = sqrt(1² + 20²) ≈ 20 m/s to scale drag energy

### Formula

For a wind with velocity components (vx, vy, vz) and total speed ||V|| = sqrt(vx² + vy² + vz²):

```
F_drag = -||V|| * [Dx*vx, Dy*vy, Dz*vz]
```

Component-wise:
```
Fx = -||V|| * Dx * vx
Fy = -||V|| * Dy * vy
Fz = -||V|| * Dz * vz
```

Where:
- **Dx, Dy, Dz**: Drag coefficients (N/(m/s)²) from principal direction simulations
- **||V||**: Total wind speed magnitude
- **vx, vy, vz**: Wind velocity components (NOT normalized)

### Why This Works

1. **Total speed scales energy**: Uses ||V|| to scale overall drag energy
2. **Component speeds determine direction**: Uses vx, vy, vz for direction and proportion
3. **Accounts for cross-flow**: Correctly handles cases like falling + forward motion

## Results Format

After running analysis, you'll get a text file with:

1. **Drag Coefficients**: Dx, Dy, Dz in N/(m/s)²
2. **Reference Forces**: Forces at 15 m/s for each direction
3. **Formula Explanation**: Detailed physics explanation
4. **Python Implementation**: Ready-to-use code

### Example Results

```
Drag Coefficients:
Front-Back (X-direction): D = 0.210030 N/(m/s)^2  (Force at 15 m/s: 47.26 N)
Left-Right (Y-direction): D = 0.253285 N/(m/s)^2  (Force at 15 m/s: 56.99 N)
Top-Down (Z-direction):   D = -0.360562 N/(m/s)^2  (Force at 15 m/s: -81.13 N)
```

## OpenFOAM Case Configuration

### Mesh
- **Domain size**: (-5 -5 -2) to (5 5 4) meters, 40×40×20 cells
- **Refinement**: 500K maxGlobalCells, level 2-3 surface refinement
- **Geometry**: STL file in `constant/geometry/combined.stl`
- **Inside point**: (0.0 0.0 2.0) - must be in flow domain, not inside drone

### Solver
- **Solver**: `simpleFoam` (steady-state RANS)
- **Turbulence model**: k-omega SST
- **End time**: 10 iterations
- **Tolerances**: Relaxed for fast testing (1e-5)

### Boundary Conditions

Each case has different boundary conditions:

- **case_front_back**: Wind in +X direction (15 m/s)
  - `inlet` (x-face): fixedValue (15 0 0)
  - `outlet` (x+face): inletOutlet
  - `front`, `back`, `upperWall`, `lowerWall`: slip

- **case_left_right**: Wind in +Y direction (15 m/s)
  - `front` (y-face): fixedValue (0 15 0)
  - `back` (y+face): inletOutlet
  - `inlet`, `outlet`, `upperWall`, `lowerWall`: slip

- **case_top_down**: Wind in -Z direction (15 m/s)
  - `upperWall` (z+face): fixedValue (0 0 -15)
  - `lowerWall` (z-face): inletOutlet
  - `inlet`, `outlet`, `front`, `back`: slip

### Force Calculation
- **Forces**: Calculated using OpenFOAM's `forces` function object
- **Patches**: `combined` (drone surface)
- **Reference**: rhoInf = 1.225 kg/m³, pRef = 0, lRef = 1, Aref = 1
- **CofR**: (0 0 0) - center of rotation

## Workflow

1. **Prepare STL**: Convert OBJ → STL, scale to meters if needed
2. **Run Analysis**: `./run_analysis.sh <model>.stl`
3. **Check Results**: Review `<model>_analysis.txt`
4. **Use Formula**: Copy Python implementation to your flight simulator
5. **Clean Cases**: `./clean_all_cases.sh` when done

## Notes

- **STL Units**: Must be in meters. Use `scale_stl_to_meters.py` if needed.
- **Drone Orientation**: 
  - +Z is top (vertical up)
  - +X is front (forward direction)
  - +Y is right (lateral direction)
- **Landing Gear**: 
  - Aurelia: landing gear at z=0, centered at (0,0,0)
  - White Quadrotor: center at (0,0,0), landing gear at z≈-0.16m
- **Mesh Quality**: Current settings optimized for speed. Increase refinement in `snappyHexMeshDict` for higher accuracy.
- **Wind Speed**: Default is 15 m/s. Can be changed with `--wind-speed` flag.

## Troubleshooting

### Forces are zero
- Check that `combined` patch exists in mesh (run `analyze_existing_results.py`)
- Verify STL is properly scaled (should be ~1-2m in size)
- Check that `insidePoint` in `snappyHexMeshDict` is in flow domain, not inside drone

### Simulation fails
- Check OpenFOAM is sourced: `source /opt/openfoam10/etc/bashrc`
- Verify STL file exists in `constant/geometry/combined.stl`
- Check mesh logs: `log.snappyHexMesh`, `log.simpleFoam`

### Import errors
- Use venv Python: `../../python/venv/bin/python3`
- Or install dependencies: `pip install trimesh`

## References

- **ANALYSIS_METHOD.md**: Detailed explanation of the Blended Drag Model
- **Analysis Results**: See `*_analysis.txt` files for example outputs
