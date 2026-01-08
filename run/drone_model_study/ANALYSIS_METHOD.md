# Wind Force Analysis Method - Blended Drag Model

## Overview

This analysis uses a **Blended Drag Model** approach that is both computationally efficient and physically accurate. Instead of running simulations for every possible wind direction, we:

1. **Run 3 principal direction simulations**:
   - Front-Back (X-direction): Wind along the forward/backward axis
   - Left-Right (Y-direction): Wind along the lateral axis
   - Top-Down (Z-direction): Wind along the vertical axis

2. **Extract drag coefficients** (Dx, Dy, Dz) for each principal direction

3. **Use the Blended Drag Model formula** to calculate force for any wind direction

## Principal Directions

The three principal directions are:

| Direction | Velocity Vector | Description | Case Directory |
|-----------|----------------|-------------|----------------|
| Front-Back | (15, 0, 0) m/s | Headwind/Tailwind | `case_front_back` |
| Left-Right | (0, 15, 0) m/s | Lateral crosswind | `case_left_right` |
| Top-Down | (0, 0, -15) m/s | Vertical downwind | `case_top_down` |

**Note**: Wind speed is 15 m/s by default (configurable).

## Drag Coefficient Calculation

For each principal direction, we calculate a drag coefficient:

```
D = F / V²
```

Where:
- **D** = Drag coefficient (N/(m/s)²)
- **F** = Force component in that direction (N)
- **V** = Wind speed (m/s)

This gives us three coefficients:
- **Dx** = Coefficient for X-direction (front-back)
- **Dy** = Coefficient for Y-direction (left-right)
- **Dz** = Coefficient for Z-direction (top-down)

**Important**: These coefficients include the effect of (1/2 * ρ * A) implicitly, where ρ is air density and A is reference area.

## The Blended Drag Model Formula

### Physics Motivation

Traditional interpolation methods treat X, Y, Z drag independently, which is physically flawed. Consider this example:

**Scenario**: Drone falling at 20 m/s (vz=-20) while moving forward at 1 m/s (vx=1)

- **Old formula**: Fx based only on 1 m/s → predicts almost zero X-drag
- **Reality**: The 20 m/s vertical flow creates massive turbulent wake, increasing X-drag significantly
- **New formula**: Uses total speed ||V|| = sqrt(1² + 20²) ≈ 20 m/s to scale drag energy

The Blended Drag Model correctly accounts for **total airflow energy** while using **component speeds** for direction and proportion.

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

Total force magnitude:
```
F = sqrt(Fx² + Fy² + Fz²)
```

Where:
- **Dx, Dy, Dz**: Drag coefficients (N/(m/s)²) from principal direction simulations
- **||V||**: Total wind speed magnitude = sqrt(vx² + vy² + vz²)
- **vx, vy, vz**: Wind velocity components (NOT normalized)
- **Negative sign**: Force opposes velocity direction

### Why This Works

1. **Total speed scales energy**: Uses ||V|| to scale overall drag energy (accounts for cross-flow effects)
2. **Component speeds determine direction**: Uses vx, vy, vz for direction and proportion
3. **Physically consistent**: Matches standard drag formula when Dx = Dy = Dz (sphere case)
4. **Handles complex flows**: Correctly accounts for turbulent wake from cross-flow

## Python Implementation

```python
import math

def calculate_wind_force(vx, vy, vz, Dx, Dy, Dz):
    """
    Calculate wind force using Blended Drag Model.
    
    Args:
        vx, vy, vz: Wind velocity components (m/s) - NOT normalized
        Dx, Dy, Dz: Drag coefficients (N/(m/s)^2) from principal direction tests
    
    Returns:
        tuple: (Fx, Fy, Fz, F_magnitude) in Newtons
    """
    V_mag = math.sqrt(vx**2 + vy**2 + vz**2)
    
    if V_mag == 0:
        return 0.0, 0.0, 0.0, 0.0
    
    # Blended drag model: F = -||V|| * [Dx*vx, Dy*vy, Dz*vz]
    Fx = -V_mag * Dx * vx
    Fy = -V_mag * Dy * vy
    Fz = -V_mag * Dz * vz
    
    F_magnitude = math.sqrt(Fx**2 + Fy**2 + Fz**2)
    
    return Fx, Fy, Fz, F_magnitude
```

## Example Usage

### Example 1: 15 m/s wind from 45 degrees (+x +y direction)

```python
import math

# Wind vector components
vx = 15 * math.cos(math.radians(45))  # 10.607 m/s
vy = 15 * math.sin(math.radians(45))  # 10.607 m/s
vz = 0.0  # Horizontal wind

# Drag coefficients (example from Aurelia drone)
Dx = 0.210030  # N/(m/s)^2
Dy = 0.253285  # N/(m/s)^2
Dz = -0.360562  # N/(m/s)^2

# Calculate force
Fx, Fy, Fz, F = calculate_wind_force(vx, vy, vz, Dx, Dy, Dz)

print(f"Force: Fx={Fx:.2f} N, Fy={Fy:.2f} N, Fz={Fz:.2f} N")
print(f"Total: {F:.2f} N")
```

### Example 2: Falling drone with forward motion

```python
# Drone falling at 20 m/s while moving forward at 1 m/s
vx = 1.0   # Forward motion
vy = 0.0
vz = -20.0  # Falling (negative Z is down)

# Calculate force
Fx, Fy, Fz, F = calculate_wind_force(vx, vy, vz, Dx, Dy, Dz)

# The formula correctly uses total speed ||V|| ≈ 20 m/s
# to scale the drag, accounting for cross-flow effects
```

## Advantages

1. **Efficiency**: Only 3 simulations needed instead of dozens
2. **Physical accuracy**: Correctly accounts for cross-flow and total airflow energy
3. **Interpolation**: Can calculate force for any direction without additional simulations
4. **Speed**: Results available quickly (each simulation ~5-10 minutes)
5. **Integration**: Easy to integrate into flight simulators (PX4, ArduPilot, etc.)

## Limitations

1. **Principal directions only**: Does not account for complex coupling between directions beyond what the blended model captures
2. **Steady-state**: Assumes steady wind conditions (no time-varying effects)
3. **RANS approximation**: Uses Reynolds-Averaged Navier-Stokes, not DNS/LES
4. **Mesh quality**: Accuracy depends on mesh refinement and turbulence model

## Validation

The Blended Drag Model can be validated by:

1. **45-degree test**: Run a simulation at 45 degrees (e.g., vx=10.6, vy=10.6, vz=0)
2. **Compare**: Actual OpenFOAM force vs. predicted force from formula
3. **Error check**: If error > 10%, may need to adjust coefficients or accept as approximation cost

## Results Interpretation

After running `analyze_drone_model.py`, you'll get:

- **Dx, Dy, Dz**: Drag coefficients in N/(m/s)²
- **Reference forces**: Forces at 15 m/s for each direction
- **Formula explanation**: Detailed physics explanation
- **Python code**: Ready-to-use implementation

The coefficients tell you:
- **Dx**: How much drag per (m/s)² when wind is purely in X-direction
- **Dy**: How much drag per (m/s)² when wind is purely in Y-direction
- **Dz**: How much drag per (m/s)² when wind is purely in Z-direction

For the Aurelia drone example:
- Dx = 0.210 N/(m/s)² → 47 N at 15 m/s headwind
- Dy = 0.253 N/(m/s)² → 57 N at 15 m/s crosswind
- Dz = -0.361 N/(m/s)² → -81 N at 15 m/s downwind (negative = upward force)

## References

- OpenFOAM Documentation: https://www.openfoam.com/
- Blended Drag Model: Based on corrected physics approach for cross-flow drag
- Analysis results: See `*_analysis.txt` files for actual coefficients
