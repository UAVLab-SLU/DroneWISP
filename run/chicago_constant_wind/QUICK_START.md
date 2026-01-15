# Wind Validation Quick Start Guide

## Overview
This guide provides a step-by-step approach to implementing the wind simulation validation plan.

## Prerequisites
- OpenFOAM simulation completed in `chicago_constant_wind/`
- Python environment with required packages
- Access to weather data APIs (NOAA)

## Step-by-Step Implementation

### Step 1: Extract Wind Speed Data from Simulation (Start Here)

**Why first**: You need simulation data before you can validate it.

**Script**: `scripts/extract_wind_statistics.py`

**What it does**:
- Reads OpenFOAM velocity fields using existing `OpenFoamController`
- Extracts wind speeds at multiple heights (10m, 50m, 100m)
- Calculates statistics (mean, std, min, max, percentiles)
- Saves data to CSV files

**Key outputs**:
- `results/wind_speed_at_height_10m.csv`
- `results/wind_statistics_summary.json`
- Initial distribution plots

**Time estimate**: 2-3 hours (script development + first run)

---

### Step 2: Collect Chicago Weather Station Data

**Why second**: Need observational data for comparison.

**Script**: `scripts/fetch_chicago_weather_data.py`

**Data sources**:
1. **NOAA API** (recommended):
   - Station: KORD (O'Hare) or KMDW (Midway)
   - API: `https://www.ncei.noaa.gov/data/`
   - Or use `meteostat` Python library

2. **Alternative**: Manual download from NOAA website

**What to collect**:
- Wind speed (m/s)
- Wind direction (degrees)
- Measurement height (typically 10m)
- Time period: Match simulation or use representative period

**Key outputs**:
- `data/chicago_weather_stations.csv`
- Station metadata (coordinates, elevation)

**Time estimate**: 1-2 hours

---

### Step 3: Map Simulation Coordinates to Geographic

**Why third**: Need to match simulation points to weather station locations.

**Script**: `scripts/map_simulation_to_geographic.py`

**Tasks**:
- Identify simulation domain origin and bounds
- Determine coordinate system (likely UTM or local)
- Create transformation to lat/lon
- Map key landmarks to verify accuracy

**Key outputs**:
- Coordinate transformation function
- `docs/coordinate_system.md`

**Time estimate**: 1-2 hours

---

### Step 4: Statistical Distribution Analysis

**Why fourth**: Understand simulation characteristics before validation.

**Script**: `scripts/analyze_wind_distributions.py`

**Analysis**:
- Fit Weibull distribution to wind speeds
- Calculate percentiles (50th, 95th, 99th)
- Identify extreme value locations
- Compare to literature distributions

**Key outputs**:
- Distribution parameters
- Percentile tables
- Extreme value location map
- `results/wind_statistics_summary.json`

**Time estimate**: 2-3 hours

---

### Step 5: Point-to-Point Validation

**Why fifth**: Direct comparison with observations.

**Script**: `scripts/validate_against_stations.py`

**Process**:
1. Interpolate simulation data to weather station coordinates
2. Extract at station measurement height
3. Calculate metrics: bias, RMSE, correlation
4. Create scatter plots

**Key outputs**:
- Validation metrics table
- Scatter plots (simulated vs. observed)
- `results/validation_metrics.json`

**Time estimate**: 2-3 hours

---

### Step 6: Physical Mechanism Analysis

**Why sixth**: Justify that results are physically reasonable.

**Script**: `scripts/analyze_acceleration_mechanisms.py`

**Analysis**:
- Identify corner acceleration regions
- Quantify Venturi effects
- Measure wake regions
- Calculate amplification factors
- Compare to literature values

**Key outputs**:
- Mechanism maps
- Amplification factor statistics
- Literature comparison table

**Time estimate**: 3-4 hours

---

### Step 7: Extreme Value Justification

**Why seventh**: Address reviewer concern about 35 m/s speeds.

**Script**: `scripts/justify_extreme_values.py`

**Analysis**:
- Locate maximum speed positions
- Calculate amplification (max/inlet)
- Research Chicago historical wind records
- Compare to design standards (ASCE 7)
- Document physical mechanisms at extreme locations

**Key outputs**:
- Extreme value location map
- Amplification factor analysis
- Historical comparison document

**Time estimate**: 2-3 hours

---

### Step 8: Documentation

**Why last**: Compile everything into reports and paper sections.

**Tasks**:
1. Write validation report: `docs/wind_simulation_validation_report.md`
2. Update paper sections:
   - Evaluation section: validation subsection
   - RQ1/RQ3: distribution analysis
   - Methodology: physical reasonableness
3. Generate final figures and tables

**Time estimate**: 4-6 hours

---

## Recommended Order (If Time-Limited)

**Minimum viable validation** (1-2 days):
1. Extract wind statistics (Step 1)
2. Basic distribution analysis (Step 4)
3. Physical mechanism analysis (Step 6)
4. Quick documentation

**Full validation** (1 week):
- All steps in order

**Parallel work**:
- Steps 1 and 2 can be done in parallel
- Step 7 (extreme values) can be done anytime after Step 1

---

## Quick Commands

```bash
# Navigate to case directory
cd /home/bohanzhang/DroneWISP/run/chicago_constant_wind

# Check if simulation is complete
ls -la | grep "^d" | grep -E "^[0-9]"

# Extract wind data (once script is created)
python scripts/extract_wind_statistics.py

# Run validation (once scripts are created)
python scripts/validate_against_stations.py
```

---

## Getting Help

- Check existing scripts in `python/` directory for examples
- Review `grid_convergence_analysis.py` for OpenFOAM data extraction patterns
- Consult `python/open_foam_controller.py` for velocity field reading methods


