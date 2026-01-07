# Grid Convergence Study - Key Insights

## Executive Summary

The grid convergence study analyzed three mesh resolutions (coarse, medium, fine) for the tall building CFD simulation. The results provide important insights into mesh independence and solution accuracy.

**Mesh Sizes:**
- **Coarse**: 27,023 cells
- **Medium**: 101,350 cells (3.75× refinement)
- **Fine**: 475,695 cells (4.69× refinement, 17.6× total)

---

## Key Findings

### 1. **Drag Coefficient (Cd) - Needs Attention**

**Values:**
- Coarse: -2176.73
- Medium: -2327.33  
- Fine: -2512.75

**Analysis:**
- **GCI (fine mesh): 22.27%** ⚠️ **HIGH** - Exceeds the 5% target for engineering accuracy
- **Convergence ratio (R): 0.812** - Indicates "Uncertain" convergence (not monotonic)
- **Relative difference (fine-medium): 7.38%** - Significant change between medium and fine
- **Order of accuracy (p): 0.5** - Lower than expected (typically 1.5-2.5 for RANS)

**Interpretation:**
- The drag coefficient is **NOT mesh-independent** at the fine mesh level
- The solution is still changing significantly with mesh refinement
- **Recommendation**: Consider using an even finer mesh or investigate if the solution has reached steady state

---

### 2. **Lift Coefficient (Cl) - Good Convergence**

**Values:**
- Coarse: -21152.01
- Medium: -23529.63
- Fine: -23692.80

**Analysis:**
- **GCI (fine mesh): 2.08%** ✅ **EXCELLENT** - Well below 5% target
- **Convergence ratio (R): 14.571** - Indicates "Divergence" (but this is misleading - see note below)
- **Relative difference (fine-medium): 0.69%** - Very small change
- **Order of accuracy (p): 0.5** - Clamped to minimum (actual convergence is very good)

**Interpretation:**
- The lift coefficient shows **excellent convergence** between medium and fine meshes
- The "divergence" classification is misleading - it's due to the very small difference between medium and fine (0.69%), making the convergence ratio calculation sensitive
- **Recommendation**: Lift coefficient is mesh-independent at the fine mesh level ✅

**Note on "Divergence" classification:**
The high convergence ratio (14.571) occurs because the difference between fine and medium is very small (0.69%), while the difference between medium and coarse is larger. This is actually a sign of **good convergence**, not divergence. The solution is stabilizing.

---

### 3. **Moment Coefficient (Cm) - Acceptable Convergence**

**Values:**
- Coarse: 1592.75
- Medium: 1691.68
- Fine: 1661.28

**Analysis:**
- **GCI (fine mesh): 5.52%** ⚠️ **BORDERLINE** - Slightly above 5% target
- **Convergence ratio (R): -3.254** - Indicates "Oscillatory convergence"
- **Relative difference (fine-medium): 1.83%** - Small change
- **Order of accuracy (p): 0.5** - Lower than expected

**Interpretation:**
- The moment coefficient shows **oscillatory convergence** (value decreases from medium to fine)
- GCI is slightly above the 5% target, but close
- The oscillation suggests the solution may be approaching a limit
- **Recommendation**: Acceptable for engineering purposes, but could benefit from a 4th mesh level for confirmation

---

## Overall Assessment

### Mesh Independence Status

| Quantity | Status | GCI | Assessment |
|----------|--------|-----|------------|
| **Cd (Drag)** | ⚠️ Not Independent | 22.27% | Needs finer mesh |
| **Cl (Lift)** | ✅ Independent | 2.08% | Excellent |
| **Cm (Moment)** | ⚠️ Borderline | 5.52% | Acceptable |

### Key Insights

1. **Lift coefficient is well-converged** - The fine mesh provides mesh-independent results for lift (GCI = 2.08%)

2. **Drag coefficient needs attention** - The 22.27% GCI indicates the solution is still changing significantly. This could be due to:
   - Mesh not fine enough in critical regions (wake, boundary layers)
   - Solution not fully converged to steady state
   - Turbulence model sensitivity

3. **Moment coefficient is acceptable** - At 5.52% GCI, it's borderline but likely acceptable for engineering analysis

4. **Order of accuracy is low** - All quantities show p ≈ 0.5, which is lower than the theoretical p ≈ 2 for second-order schemes. This suggests:
   - Solution may not be fully converged
   - Turbulence model effects
   - Possible numerical issues

---

## Recommendations

### For Current Study

1. **Use fine mesh for lift coefficient** - Results are mesh-independent (GCI = 2.08%)

2. **Exercise caution with drag coefficient** - The 22.27% GCI suggests:
   - Report drag with uncertainty bounds
   - Consider running a 4th mesh level (very fine) if drag is critical
   - Verify solution has reached steady state

3. **Moment coefficient is acceptable** - Can be used with note about 5.52% GCI

### For Future Simulations

1. **Recommended mesh**: Use the **fine mesh** (60×100×50 base cells) as the standard for similar cases

2. **If drag is critical**: Consider:
   - Adding a 4th mesh level (very fine: 90×150×75)
   - Local mesh refinement in wake regions
   - Checking steady-state convergence more carefully

3. **Documentation**: Report GCI values alongside results to indicate mesh independence status

---

## Extrapolated Values (h → 0)

Using Richardson extrapolation, the estimated values at infinite mesh resolution:

- **Cd_extrapolated**: -2960.38 (compared to fine mesh: -2512.75)
- **Cl_extrapolated**: -24086.73 (compared to fine mesh: -23692.80)
- **Cm_extrapolated**: 1587.88 (compared to fine mesh: 1661.28)

**Note**: These extrapolated values assume the observed order of accuracy (p = 0.5) continues. The large difference for Cd suggests the fine mesh may not be fine enough.

---

## Conclusion

The grid convergence study shows **mixed results**:
- ✅ **Lift coefficient**: Excellent convergence (GCI = 2.08%)
- ⚠️ **Drag coefficient**: Not converged (GCI = 22.27%) - needs attention
- ⚠️ **Moment coefficient**: Borderline (GCI = 5.52%) - acceptable

**Overall**: The fine mesh provides reliable results for lift, but drag coefficient requires further investigation or finer mesh refinement.

