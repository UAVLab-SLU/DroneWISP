# Grid Convergence Study Plan

## Base Case Selection

**Recommended Base Case: `tallBuilding`**

### Rationale:
1. **Representative geometry**: Tall building is a common scenario in your simulations
2. **Well-documented**: Has clear setup and results
3. **Dual mesh system**: Uses both blockMesh (base) and snappyHexMesh (refinement), allowing systematic variation
4. **Available metrics**: Force coefficients (Cd, Cl, Cm) and velocity/pressure fields are already computed
5. **Steady-state**: Uses simpleFoam (RANS), making convergence analysis straightforward

### Current Mesh Configuration:
- **blockMesh**: `(30 50 25)` cells in (x y z) directions = 37,500 base cells
- **snappyHexMesh**: 
  - Surface refinement: level (1 2)
  - Feature refinement: level 2
  - Region refinement: level 2

---

## Grid Convergence Strategy

### Option 1: Systematic blockMesh Refinement (Recommended for Initial Study)

Vary the base mesh resolution while keeping snappyHexMesh settings constant.

#### Mesh Levels:
1. **Coarse (Level 1)**: `(15 25 12)` → ~4,500 base cells
2. **Medium (Level 2)**: `(30 50 25)` → ~37,500 base cells (current)
3. **Fine (Level 3)**: `(60 100 50)` → ~300,000 base cells
4. **Very Fine (Level 4)**: `(90 150 75)` → ~1,012,500 base cells (if computational resources allow)

**Refinement ratio**: ~2x in each direction (r = 2)

### Option 2: snappyHexMesh Refinement Level Variation

Keep blockMesh constant, vary snappyHexMesh refinement levels.

#### Refinement Levels:
1. **Coarse**: Surface level (0 1), Feature level 1, Region level 1
2. **Medium**: Surface level (1 2), Feature level 2, Region level 2 (current)
3. **Fine**: Surface level (2 3), Feature level 3, Region level 3
4. **Very Fine**: Surface level (3 4), Feature level 4, Region level 4

### Option 3: Combined Refinement (Most Comprehensive)

Vary both blockMesh and snappyHexMesh systematically.

---

## Quantities to Monitor

### Primary Quantities (Integral):
1. **Force Coefficients** (from `postProcessing/forceCoeffs1/`):
   - Drag coefficient: **Cd**
   - Lift coefficient: **Cl**
   - Moment coefficient: **Cm**
   - These are the most reliable for grid convergence as they integrate over the entire surface

### Secondary Quantities (Point-wise):
2. **Velocity at key locations**:
   - Upstream reference point: e.g., (-20, 0, 10)
   - Wake region: e.g., (10, 0, 10)
   - Building top: e.g., (0, 0, 20)
   
3. **Pressure at key locations**:
   - Stagnation point (front face)
   - Separation point (side/rear faces)

4. **Turbulence quantities**:
   - Turbulent kinetic energy (k) at wake center
   - Specific dissipation rate (omega) at wake center

### Mesh Quality Metrics:
5. **Total cell count** (from `log.snappyHexMesh` or `checkMesh`)
6. **Mesh quality metrics**: skewness, non-orthogonality (from `checkMesh`)

---

## Expected Results

### Convergence Behavior:

1. **Force Coefficients**:
   - Should show monotonic convergence (or oscillatory convergence) as mesh refines
   - Relative error between successive levels should decrease
   - Typical convergence: Cd, Cl, Cm should stabilize within 1-5% between fine and very fine meshes

2. **Velocity/Pressure Fields**:
   - Point values may show more scatter initially
   - Should converge to asymptotic values
   - Wake region typically requires finer mesh than freestream

3. **Cell Count Growth**:
   - With r=2 refinement: cell count increases by ~8x (2³) per level
   - Computational time typically increases by ~8-16x per level

### Convergence Criteria (Richardson Extrapolation):

For a quantity φ at three mesh levels (coarse, medium, fine):
- **Grid Convergence Index (GCI)**:
  ```
  GCI_fine = (F_s * |ε|) / (r^p - 1)
  ```
  where:
  - F_s = safety factor (1.25 for 3 grids)
  - ε = relative error between fine and medium
  - r = refinement ratio
  - p = observed order of accuracy

- **Extrapolated value**:
  ```
  φ_extrapolated = φ_fine + (φ_fine - φ_medium) / (r^p - 1)
  ```

- **Convergence ratio**:
  ```
  R = (φ_medium - φ_coarse) / (φ_fine - φ_medium)
  ```
  - R ≈ 1: monotonic convergence
  - R < 0: oscillatory convergence
  - |R| > 1: divergence (mesh too coarse)

---

## Implementation Steps

### Step 1: Create Mesh Variants
1. Copy `tallBuilding` to new directories:
   - `tallBuilding_grid_coarse`
   - `tallBuilding_grid_medium` (or use existing)
   - `tallBuilding_grid_fine`
   - `tallBuilding_grid_veryFine`

2. Modify `system/blockMeshDict` in each:
   - Change cell counts: `(nx ny nz)` in blocks section

3. Keep all other settings identical:
   - Boundary conditions
   - Solver settings
   - snappyHexMesh settings (if using Option 1)
   - Wind speed and direction

### Step 2: Run Simulations
1. For each mesh level:
   ```bash
   cd tallBuilding_grid_<level>
   bash ./Allclean
   bash ./Allrun
   ```

2. Verify convergence:
   - Check residuals in `log.simpleFoam`
   - Ensure solution reaches steady state
   - Verify no mesh quality issues (`checkMesh`)

### Step 3: Extract Results
1. **Force coefficients**: Read from `postProcessing/forceCoeffs1/0/forceCoeffs.dat`
   - Use final time step value (time = 50s)

2. **Velocity/Pressure at points**: 
   - Use `postProcess -func probes` or
   - Extract from ParaView at specific coordinates
   - Or use Python script to read OpenFOAM fields

3. **Cell count**: 
   - From `log.snappyHexMesh`: "Final mesh has X cells"
   - Or run: `checkMesh | grep "cells:"`

### Step 4: Analysis
1. **Plot convergence**:
   - Quantity vs. cell count (log-log scale)
   - Quantity vs. characteristic cell size h
   - Relative error vs. refinement level

2. **Calculate GCI**:
   - Use Richardson extrapolation
   - Determine order of accuracy p
   - Calculate extrapolated values

3. **Document results**:
   - Table of quantities vs. mesh level
   - Convergence plots
   - GCI values
   - Recommended mesh for future simulations

---

## Recommended Starting Point

**Start with Option 1 (blockMesh refinement)** using 3 levels:
- Coarse: (15 25 12)
- Medium: (30 50 25) - current
- Fine: (60 100 50)

This provides:
- Clear refinement ratio (r = 2)
- Manageable computational cost
- Sufficient data for Richardson extrapolation

If computational resources allow, add a 4th level (90 150 75) for more confidence.

---

## Scripts Needed

1. **Mesh generation script**: Automate creation of mesh variants
2. **Result extraction script**: Extract force coefficients and point values
3. **Convergence analysis script**: Calculate GCI, plot convergence, perform Richardson extrapolation

---

## Success Criteria

Grid convergence study is successful if:
1. At least 3 mesh levels show monotonic or oscillatory convergence
2. GCI for fine mesh < 5% for primary quantities (Cd, Cl, Cm)
3. Order of accuracy p is reasonable (typically 1.5-2.5 for RANS)
4. Extrapolated values are within uncertainty bounds
5. Recommended mesh level is identified for future simulations

---

## Notes

- **Computational cost**: Each refinement level increases cost by ~8-16x
- **Convergence time**: May need to adjust `endTime` in `controlDict` for coarser meshes to ensure steady state
- **Mesh quality**: Always run `checkMesh` to ensure mesh quality is acceptable
- **Turbulence model**: Current setup uses k-omega SST; grid requirements may differ for other models

