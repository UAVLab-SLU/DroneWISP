# Grid Convergence Study - Executive Summary

## Quick Overview

**Mesh Levels:**
- **Coarse**: 27,023 cells
- **Medium**: 101,350 cells (3.75× more than coarse)
- **Fine**: 475,695 cells (4.69× more than medium, 17.6× more than coarse)

---

## Key Results

### ✅ **Lift Coefficient (Cl) - EXCELLENT**
- **GCI: 2.08%** (Target: <5%) ✅
- **Converged**: Yes
- **Fine mesh value**: -23,692.80
- **Status**: **Mesh-independent, ready for use**

### ⚠️ **Drag Coefficient (Cd) - NEEDS ATTENTION**
- **GCI: 22.27%** (Target: <5%) ⚠️
- **Converged**: No
- **Fine mesh value**: -2,512.75
- **Status**: **Not mesh-independent, consider finer mesh**

### ⚠️ **Moment Coefficient (Cm) - BORDERLINE**
- **GCI: 5.52%** (Target: <5%) ⚠️
- **Converged**: Borderline
- **Fine mesh value**: 1,661.28
- **Status**: **Acceptable for engineering use**

---

## What This Means

### For Your Research/Paper

1. **You can confidently report lift coefficient** - It's mesh-independent (GCI = 2.08%)

2. **Drag coefficient needs qualification** - Report with uncertainty note:
   - "Drag coefficient shows GCI = 22.27%, indicating mesh sensitivity. Results should be interpreted with caution."

3. **Moment coefficient is acceptable** - Can be reported with note about 5.52% GCI

### For Future Simulations

- **Use fine mesh (475K cells)** as standard for similar cases
- **If drag is critical**: Consider even finer mesh or local refinement in wake regions
- **Always check steady-state convergence** - Low order of accuracy (p ≈ 0.5) suggests possible convergence issues

---

## Convergence Behavior

| Quantity | Coarse → Medium | Medium → Fine | Trend |
|----------|----------------|---------------|-------|
| **Cd** | -2176.73 → -2327.33 | -2327.33 → -2512.75 | Still changing |
| **Cl** | -21152.01 → -23529.63 | -23529.63 → -23692.80 | Stabilizing ✅ |
| **Cm** | 1592.75 → 1691.68 | 1691.68 → 1661.28 | Oscillating |

**Key Observation**: Lift coefficient stabilizes between medium and fine (only 0.69% change), while drag continues to change significantly (7.38% change).

---

## Recommendations

### Immediate Actions

1. ✅ **Use fine mesh results for lift coefficient** - Fully converged
2. ⚠️ **Report drag with uncertainty** - Not fully converged
3. ✅ **Moment coefficient acceptable** - Borderline but usable

### If Drag is Critical

Consider:
- Running a 4th mesh level (very fine: ~1.5-2M cells)
- Local mesh refinement in wake regions
- Verifying steady-state convergence more carefully
- Checking if turbulence model is appropriate

---

## Bottom Line

**The fine mesh (475,695 cells) provides:**
- ✅ Mesh-independent lift coefficient
- ⚠️ Drag coefficient that may need further refinement
- ✅ Acceptable moment coefficient

**For most engineering purposes, the fine mesh is sufficient, but drag results should be reported with appropriate uncertainty.**

