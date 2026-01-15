# Wind Simulation Validation and Realism Assessment Plan

## Overview
This plan addresses Reviewer 1's concerns about wind simulation realism and validation. The goal is to validate the Chicago wind simulation against real meteorological data and demonstrate physical reasonableness of the results.

## Objectives
1. **Chicago Scenario Validation**: Compare simulated wind speeds against actual measurements
2. **Wind Speed Distribution Analysis**: Provide statistical analysis showing realistic distributions
3. **Physical Reasonableness Check**: Document that wind acceleration effects are physically plausible

---

## Phase 1: Data Collection and Setup

### 1.1 Meteorological Data Sources
**Objective**: Obtain real wind measurement data for Chicago

**Data Sources**:
- **NOAA/NWS Weather Stations**: 
  - Chicago O'Hare International Airport (KORD) - ASOS station
  - Chicago Midway Airport (KMDW)
  - Download via NOAA API or NCDC database
- **Chicago Urban Weather Stations**:
  - City of Chicago Open Data Portal (if available)
  - Illinois State Water Survey stations
- **Historical Weather Data**:
  - Time period: Match simulation conditions (or use representative period)
  - Parameters needed: Wind speed, wind direction, temperature, pressure

**Implementation**:
- Create script: `scripts/fetch_chicago_weather_data.py`
- Use `requests` library to query NOAA API
- Store data in CSV format: `data/chicago_weather_stations.csv`
- Include station metadata (lat, lon, elevation)

**Deliverables**:
- [ ] Weather station data CSV file
- [ ] Station location map/coordinates
- [ ] Data quality assessment report

### 1.2 Simulation Domain Mapping
**Objective**: Map simulation coordinates to real-world Chicago locations

**Tasks**:
- Identify coordinate system origin in simulation
- Map simulation domain bounds to Chicago geographic coordinates
- Identify key landmarks/buildings in the model
- Create coordinate transformation utilities

**Implementation**:
- Script: `scripts/map_simulation_to_geographic.py`
- Document coordinate system in `docs/coordinate_system.md`

**Deliverables**:
- [ ] Coordinate transformation matrix/function
- [ ] Geographic bounds of simulation domain
- [ ] Landmark mapping document

---

## Phase 2: Wind Speed Distribution Analysis

### 2.1 Extract Wind Speed Data from Simulation
**Objective**: Extract comprehensive wind speed data from OpenFOAM results

**Approach**:
1. Use existing `OpenFoamController` class to read velocity fields
2. Extract data at multiple heights (e.g., 10m, 50m, 100m - typical measurement heights)
3. Extract data at multiple horizontal planes
4. Calculate wind speed magnitude: `|U| = sqrt(u² + v² + w²)`

**Implementation**:
- Script: `scripts/extract_wind_statistics.py`
- Functions:
  - Extract velocity at specific heights
  - Calculate statistics (mean, std, min, max, percentiles)
  - Generate spatial distribution maps
  - Identify extreme value locations

**Outputs**:
- CSV files: `results/wind_speed_at_height_{Z}m.csv`
- Statistics file: `results/wind_statistics_summary.json`
- Spatial distribution plots

**Deliverables**:
- [ ] Wind speed extraction script
- [ ] Statistics summary (mean, std, percentiles, max)
- [ ] Spatial distribution plots at multiple heights
- [ ] Extreme value location analysis

### 2.2 Statistical Analysis
**Objective**: Compare simulation distributions to known urban wind patterns

**Analysis Components**:
1. **Histogram/PDF Analysis**:
   - Wind speed distribution at different heights
   - Compare to Weibull distribution (common for wind)
   - Identify distribution parameters

2. **Spatial Statistics**:
   - Mean wind speed by region (upwind, building wake, downwind)
   - Standard deviation by region
   - Coefficient of variation

3. **Extreme Value Analysis**:
   - Maximum wind speeds and locations
   - Percentiles (95th, 99th)
   - Justification for 35 m/s maximum

**Implementation**:
- Script: `scripts/analyze_wind_distributions.py`
- Use `scipy.stats` for distribution fitting
- Generate comparison plots

**Deliverables**:
- [ ] Distribution fitting results (Weibull parameters)
- [ ] Comparison plots: simulation vs. literature distributions
- [ ] Statistical summary table
- [ ] Extreme value justification document

### 2.3 Literature Comparison
**Objective**: Compare against published urban wind studies

**Literature Sources**:
- Urban wind tunnel studies
- CFD validation studies for urban environments
- Building aerodynamics references
- Wind speed amplification factors around buildings

**Key Metrics to Compare**:
- Mean wind speed reduction in urban canyons
- Wind speed amplification around building corners
- Wake region characteristics
- Height-dependent wind profiles

**Implementation**:
- Document: `docs/literature_comparison.md`
- Create comparison tables
- Reference key papers

**Deliverables**:
- [ ] Literature review summary
- [ ] Comparison tables (simulation vs. literature)
- [ ] Discussion of agreement/discrepancies

---

## Phase 3: Chicago Scenario Validation

### 3.1 Point-to-Point Comparison
**Objective**: Compare simulated wind speeds at specific locations to weather station data

**Approach**:
1. Identify weather station locations within/near simulation domain
2. Extract simulated wind speeds at corresponding coordinates
3. Compare time-averaged values (if time series available) or steady-state values
4. Account for:
   - Measurement height differences
   - Local terrain effects
   - Station exposure (open field vs. urban)

**Implementation**:
- Script: `scripts/validate_against_stations.py`
- Functions:
  - Interpolate simulation data to station coordinates
  - Extract data at station measurement heights
  - Calculate comparison metrics (bias, RMSE, correlation)

**Metrics**:
- Mean bias: `mean(simulated - observed)`
- Root Mean Square Error (RMSE)
- Correlation coefficient
- Scatter plots: simulated vs. observed

**Deliverables**:
- [ ] Validation script
- [ ] Comparison plots (scatter, time series if applicable)
- [ ] Validation metrics table
- [ ] Discussion of discrepancies

### 3.2 Spatial Validation
**Objective**: Compare spatial patterns of wind speed

**Approach**:
1. Create wind speed maps from simulation
2. Compare spatial patterns to known Chicago wind patterns (if available)
3. Validate that high-speed regions occur in physically reasonable locations:
   - Building corners (acceleration)
   - Narrow passages (Venturi effect)
   - Upwind of obstacles

**Implementation**:
- Use ParaView or Python visualization
- Create comparison maps
- Document physical mechanisms

**Deliverables**:
- [ ] Wind speed contour maps
- [ ] Annotated maps showing physical mechanisms
- [ ] Pattern validation discussion

### 3.3 Height Profile Validation
**Objective**: Validate vertical wind speed profiles

**Approach**:
1. Extract wind speed profiles at multiple locations
2. Compare to:
   - Power law profile: `U(z) = U_ref * (z/z_ref)^α`
   - Logarithmic profile (if applicable)
   - Weather station vertical profiles (if available)

**Implementation**:
- Script: `scripts/validate_height_profiles.py`
- Extract profiles at representative locations
- Fit power law and compare α values to literature

**Deliverables**:
- [ ] Height profile plots
- [ ] Power law exponent comparison
- [ ] Profile validation discussion

---

## Phase 4: Physical Reasonableness Assessment

### 4.1 Wind Acceleration Mechanisms
**Objective**: Document and validate physical mechanisms causing wind acceleration

**Mechanisms to Analyze**:
1. **Corner Acceleration**:
   - Wind speed increase around building corners
   - Expected amplification factors: 1.2-1.5× (literature)
   - Locations: Identify and quantify

2. **Venturi Effect**:
   - Narrow passages between buildings
   - Speed increase in constrictions
   - Expected: 1.1-1.3× (depending on geometry)

3. **Channeling**:
   - Street canyons aligned with wind direction
   - Speed enhancement along channels

4. **Wake Effects**:
   - Reduced speeds behind buildings
   - Expected: 0.3-0.7× of free stream

**Implementation**:
- Script: `scripts/analyze_acceleration_mechanisms.py`
- Identify regions with each mechanism
- Quantify amplification factors
- Compare to literature values

**Deliverables**:
- [ ] Mechanism identification maps
- [ ] Amplification factor statistics
- [ ] Literature comparison table
- [ ] Physical mechanism validation document

### 4.2 Extreme Value Justification
**Objective**: Justify that 35 m/s maximum wind speed is physically reasonable

**Analysis**:
1. **Location Analysis**:
   - Where do maximum speeds occur?
   - Are locations physically reasonable? (corners, narrow passages)
   - Are they isolated or widespread?

2. **Amplification Factor**:
   - Calculate: `max_speed / inlet_speed`
   - Compare to literature values (typically 1.5-2.0× for extreme cases)

3. **Frequency Analysis**:
   - What percentage of domain exceeds certain thresholds?
   - Are extreme values rare (as expected)?

4. **Context**:
   - Reference real-world extreme wind events in Chicago
   - Historical maximum wind speeds in Chicago area
   - Comparison to design wind speeds (e.g., ASCE 7)

**Implementation**:
- Script: `scripts/justify_extreme_values.py`
- Extract maximum speed locations
- Calculate amplification factors
- Research Chicago wind records

**Deliverables**:
- [ ] Extreme value location map
- [ ] Amplification factor analysis
- [ ] Historical wind speed comparison
- [ ] Justification document

### 4.3 Literature References
**Objective**: Compile relevant literature on urban wind effects

**Key Topics**:
- Urban wind tunnel studies
- Building aerodynamics
- Wind speed amplification around buildings
- Urban boundary layer characteristics
- CFD validation studies

**Implementation**:
- Document: `docs/physical_reasonableness_literature.md`
- Organize by topic
- Include key findings and values

**Deliverables**:
- [ ] Literature review document
- [ ] Key reference values table
- [ ] Comparison to simulation results

---

## Phase 5: Documentation and Reporting

### 5.1 Validation Report
**Objective**: Create comprehensive validation report

**Sections**:
1. **Executive Summary**
   - Validation objectives
   - Key findings
   - Overall assessment

2. **Methodology**
   - Data sources
   - Comparison methods
   - Metrics used

3. **Results**
   - Point-to-point validation
   - Distribution analysis
   - Physical mechanism analysis
   - Extreme value justification

4. **Discussion**
   - Agreement with observations
   - Discrepancies and explanations
   - Limitations
   - Recommendations

5. **Conclusions**
   - Validation status
   - Confidence in results
   - Use recommendations

**Location**: `docs/wind_simulation_validation_report.md`

### 5.2 Integration into Paper
**Objective**: Add validation content to research paper

**Locations** (per reviewer requirements):
1. **Evaluation Section - Validation Subsection**:
   - Chicago scenario validation results
   - Comparison to weather station data
   - Validation methodology

2. **RQ1 and RQ3 Analysis Sections**:
   - Wind speed distribution analysis
   - Statistical summaries
   - Comparison to urban wind literature

3. **Methodology or Evaluation Section**:
   - Physical reasonableness discussion
   - Literature references on urban wind effects
   - Building aerodynamics context

**Deliverables**:
- [ ] Validation subsection text
- [ ] Updated RQ1/RQ3 sections
- [ ] Physical reasonableness discussion
- [ ] Figures and tables for paper

---

## Implementation Timeline

### Week 1: Data Collection
- [ ] Set up weather data fetching scripts
- [ ] Collect Chicago weather station data
- [ ] Map simulation coordinates to geographic

### Week 2: Analysis Scripts
- [ ] Create wind speed extraction scripts
- [ ] Implement statistical analysis tools
- [ ] Develop visualization scripts

### Week 3: Validation Analysis
- [ ] Run point-to-point validation
- [ ] Perform distribution analysis
- [ ] Conduct physical mechanism analysis

### Week 4: Documentation
- [ ] Write validation report
- [ ] Create paper sections
- [ ] Generate figures and tables

---

## File Structure

```
chicago_constant_wind/
├── scripts/
│   ├── fetch_chicago_weather_data.py
│   ├── map_simulation_to_geographic.py
│   ├── extract_wind_statistics.py
│   ├── analyze_wind_distributions.py
│   ├── validate_against_stations.py
│   ├── validate_height_profiles.py
│   ├── analyze_acceleration_mechanisms.py
│   └── justify_extreme_values.py
├── data/
│   ├── chicago_weather_stations.csv
│   └── station_metadata.json
├── results/
│   ├── wind_speed_at_height_*.csv
│   ├── wind_statistics_summary.json
│   ├── validation_metrics.json
│   └── figures/
│       ├── wind_distribution_*.png
│       ├── validation_scatter_*.png
│       └── mechanism_maps_*.png
├── docs/
│   ├── coordinate_system.md
│   ├── literature_comparison.md
│   ├── physical_reasonableness_literature.md
│   └── wind_simulation_validation_report.md
└── VALIDATION_PLAN.md (this file)
```

---

## Dependencies

**Python Packages**:
- `numpy`, `pandas`, `matplotlib`, `seaborn`
- `scipy` (for statistics)
- `requests` (for API calls)
- `pyproj` or `geopy` (for coordinate transformations)
- Existing: `OpenFoamController` from `python/open_foam_controller.py`

**External Data**:
- NOAA/NWS weather station data
- Literature references (papers, books)

**Tools**:
- ParaView (for visualization)
- OpenFOAM (already available)

---

## Success Criteria

1. **Validation**:
   - RMSE < 20% of mean observed wind speed
   - Correlation coefficient > 0.6 (if multiple stations)
   - Bias < 15% of mean

2. **Distribution Analysis**:
   - Distribution parameters within literature ranges
   - Extreme values justified and located appropriately

3. **Physical Reasonableness**:
   - Amplification factors within literature ranges (1.2-2.0×)
   - Mechanisms identified and quantified
   - Literature references provided

4. **Documentation**:
   - Complete validation report
   - Paper sections updated
   - All figures and tables generated

---

## Next Steps

1. **Immediate**: Review this plan and adjust as needed
2. **Start with**: Weather data collection (Phase 1.1)
3. **Parallel work**: Begin wind speed extraction while collecting weather data
4. **Iterate**: Refine analysis based on initial results


