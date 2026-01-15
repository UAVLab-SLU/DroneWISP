# Real Urban Wind Data Sources for CFD Validation

## Overview
This document provides comprehensive information about available real-world wind measurement data from complex urban environments that can be used to validate CFD simulations.

---

## 1. Government & Institutional Data Sources

### 1.1 NOAA National Centers for Environmental Information (NCEI)
- **Website**: https://www.ncei.noaa.gov/
- **Data Type**: High-quality meteorological data including wind speed, direction, temperature
- **Coverage**: Thousands of weather stations across major US cities
- **Access Method**: 
  - Web interface: Climate Data Online (CDO)
  - API: https://www.ncdc.noaa.gov/cdo-web/webservices/v2
  - FTP downloads available
- **Temporal Resolution**: Hourly, daily, monthly
- **Best For**: Long-term urban wind patterns, validation of mesoscale to microscale CFD models
- **Data Format**: CSV, JSON, XML

**How to Access**:
1. Visit https://www.ncdc.noaa.gov/cdo-web/
2. Select "Local Climatological Data (LCD)" for hourly observations
3. Filter by urban locations (airports, city centers)
4. Download historical data (free with registration)

### 1.2 US EPA Air Quality System (AQS)
- **Website**: https://www.epa.gov/aqs
- **Data Type**: Meteorological data from air quality monitoring stations
- **Coverage**: Urban and suburban monitoring sites across the US
- **Access Method**: 
  - EPA AQS API
  - Pre-generated data files
  - AirData download portal
- **Temporal Resolution**: Hourly
- **Best For**: Urban canopy layer wind measurements
- **Data Format**: CSV, API responses

**How to Access**:
1. Visit https://aqs.epa.gov/aqsweb/documents/data_api.html
2. Register for API key
3. Query meteorological parameters for urban stations

### 1.3 MesoWest/Synoptic Data
- **Website**: https://synopticdata.com/ (formerly MesoWest)
- **Data Type**: Real-time and historical meteorological data
- **Coverage**: Dense network including urban areas, rooftops, building-mounted sensors
- **Access Method**: 
  - API access (free for research)
  - Web interface for visualization
- **Temporal Resolution**: 5-minute to hourly
- **Best For**: High-resolution urban wind field validation
- **Data Format**: JSON, CSV

**How to Access**:
1. Register at https://synopticdata.com/
2. Request API token
3. Access thousands of stations including urban networks

---

## 2. Research Datasets & Field Campaigns

### 2.1 BUBBLE (Basel Urban Boundary Layer Experiment)
- **Location**: Basel, Switzerland
- **Description**: Comprehensive urban boundary layer measurement campaign
- **Data Available**:
  - Multiple measurement heights on towers
  - Sonic anemometer data (3D wind components)
  - Turbulence statistics
  - Temperature and humidity profiles
- **Temporal Coverage**: 2001-2002
- **Spatial Coverage**: Multiple sites across Basel urban area
- **Best For**: Validation of urban canopy parameterizations, street canyon flows
- **Access**: Contact researchers or check published papers for data availability
- **Reference**: Rotach et al. (2005), "BUBBLE – an Urban Boundary Layer Meteorology Project"

### 2.2 Oklahoma City Joint Urban 2003 (JU2003)
- **Location**: Oklahoma City, USA
- **Description**: Intensive urban dispersion study with extensive wind measurements
- **Data Available**:
  - Multiple sonic anemometers
  - Building-mounted sensors
  - Mobile measurements
  - Lidar and sodar profiles
- **Temporal Coverage**: July 2003
- **Best For**: Urban street canyon validation, dispersion modeling
- **Access**: Available through NOAA or research publications
- **Reference**: Allwine et al. (2004), "Joint Urban 2003"

### 2.3 COST Action 732 Database
- **Description**: European cooperation on urban meteorology and air quality
- **Data Available**:
  - Urban wind tunnel experiments
  - Full-scale urban measurements
  - CFD benchmark datasets
- **Coverage**: Multiple European cities
- **Best For**: Standardized CFD validation cases
- **Access**: http://www.cost.eu/ (search for COST 732)

### 2.4 Tokyo Urban Climate Project
- **Location**: Tokyo, Japan
- **Description**: Dense urban meteorological network
- **Data Available**:
  - High-rise building wind measurements
  - Street-level anemometers
  - Vertical profiles
- **Best For**: High-density urban environment validation
- **Access**: Through research collaborations or published datasets

---

## 3. Open Data Platforms

### 3.1 AWS Open Data Registry
- **Website**: https://registry.opendata.aws/
- **Relevant Datasets**:
  - NOAA Global Historical Climatology Network (GHCN)
  - Weather station data
  - Climate model outputs
- **Access Method**: Direct S3 bucket access, no API required
- **Data Format**: Various (NetCDF, CSV, HDF5)
- **Best For**: Large-scale data processing, batch downloads

### 3.2 Zenodo Research Data Repository
- **Website**: https://zenodo.org/
- **Search For**: "urban wind measurements", "CFD validation data"
- **Data Type**: Published research datasets
- **Access Method**: Direct download (DOI-referenced)
- **Best For**: Specific research campaign data

### 3.3 Pangaea Data Publisher
- **Website**: https://www.pangaea.de/
- **Data Type**: Earth science data including meteorological measurements
- **Access Method**: Web interface, API available
- **Best For**: Academic research datasets

---

## 4. Local Urban Networks

### 4.1 Urban Microclimate Networks
Many cities operate their own meteorological networks:

- **New York City**: NYC Mesonet (https://nycmesonet.org/)
- **London**: London Air Quality Network (includes met data)
- **Singapore**: National Environment Agency weather stations
- **Hong Kong**: Hong Kong Observatory urban stations
- **Chicago**: Urban Heat Island monitoring network

### 4.2 Airport Meteorological Data (METAR/ASOS)
- **Coverage**: Major airports in/near urban areas
- **Data Type**: Hourly surface observations including wind
- **Access**: 
  - Iowa Environmental Mesonet: https://mesonet.agron.iastate.edu/
  - NOAA Aviation Weather Center
- **Temporal Resolution**: Hourly (some 20-minute)
- **Best For**: Reference conditions, boundary conditions for CFD

---

## 5. Recommended Datasets for CFD Validation

### Priority 1: High-Quality Research Datasets
1. **BUBBLE Basel** - Best documented urban boundary layer dataset
2. **Oklahoma City JU2003** - Excellent for street canyon validation
3. **COST 732 Cases** - Standardized validation cases

### Priority 2: Continuous Monitoring Networks
1. **MesoWest/Synoptic** - Easy API access, many urban stations
2. **NOAA LCD** - Reliable, long-term records
3. **City-specific networks** - High spatial resolution

### Priority 3: Supplementary Data
1. **Airport METAR data** - Reference conditions
2. **EPA AQS stations** - Urban canopy measurements
3. **AWS Open Data** - Large-scale analysis

---

## 6. Data Requirements for CFD Validation

### Essential Parameters
- Wind speed (m/s)
- Wind direction (degrees)
- Measurement height (m above ground)
- Timestamp (UTC)
- Location coordinates

### Highly Recommended
- Turbulence intensity
- Temperature (for buoyancy effects)
- Atmospheric stability indicators
- Surface roughness information
- Building geometry data

### Validation Metrics
- Mean wind speed profiles
- Turbulence kinetic energy
- Wind direction frequency distributions
- Vertical profiles at multiple locations
- Temporal variations (diurnal, seasonal)

---

## 7. Data Processing Tips

### Quality Control
1. Remove instrument errors and outliers
2. Check for sensor malfunction periods
3. Verify measurement heights and positions
4. Account for local obstructions

### Preprocessing for CFD Comparison
1. Convert to consistent coordinate system
2. Time-average to match CFD steady-state (typically 10-min to 1-hour)
3. Filter for specific atmospheric conditions (neutral stability preferred)
4. Normalize by reference height if needed

### Statistical Comparison
- Use metrics like RMSE, MAE, correlation coefficient
- Compare vertical profiles, not just single points
- Validate turbulence characteristics, not just mean flow
- Consider uncertainty in measurements

---

## 8. Quick Start Guide

### Step 1: Choose Your Dataset
For beginners: Start with **MesoWest/Synoptic** (easy API, good documentation)
For research: Use **BUBBLE** or **COST 732** datasets (peer-reviewed, well-documented)

### Step 2: Access the Data
```python
# Example: MesoWest API access
import requests

API_TOKEN = 'your_token_here'
station_id = 'URBAN_STATION_ID'
url = f'https://api.synopticdata.com/v2/stations/timeseries'

params = {
    'token': API_TOKEN,
    'stid': station_id,
    'start': '202601010000',
    'end': '202601020000',
    'vars': 'wind_speed,wind_direction',
    'units': 'metric'
}

response = requests.get(url, params=params)
data = response.json()
```

### Step 3: Process and Compare
1. Extract wind speed/direction time series
2. Calculate statistics (mean, std, percentiles)
3. Compare with CFD results at corresponding locations
4. Visualize profiles and scatter plots

---

## 9. Additional Resources

### Guidelines and Best Practices
- **AIJ Guidelines** (Architectural Institute of Japan): CFD validation standards
- **COST Action 732**: Best practice guideline for CFD simulation of flows in urban environment
- **ASHRAE Research**: Urban wind environment guidelines

### Software Tools
- **OpenFOAM**: Open-source CFD with urban validation tutorials
- **PALM Model System**: Large-eddy simulation for urban environments
- **WRF**: Weather Research and Forecasting model for mesoscale

### Academic Papers on Validation
- Franke et al. (2007): "Best practice guideline for CFD simulation of flows in the urban environment"
- Tominaga et al. (2008): "AIJ guidelines for practical applications of CFD to pedestrian wind environment"
- Blocken (2015): "Computational Fluid Dynamics for urban physics: Importance, scales, possibilities, limitations and ten tips"

---

## 10. Contact Information for Data Access

### For Research Datasets
- **BUBBLE Data**: Contact ETH Zurich or University of Basel
- **JU2003 Data**: NOAA Atmospheric Turbulence and Diffusion Division
- **COST 732**: Check university repositories (Hamburg, Southampton)

### For API Support
- **NOAA NCEI**: ncei.orders@noaa.gov
- **EPA AQS**: AQS_DataMart@epa.gov
- **Synoptic/MesoWest**: support@synopticdata.com

---

## Summary

The best approach for CFD validation in complex urban environments:

1. **Start with standardized research datasets** (BUBBLE, JU2003) for initial validation
2. **Use continuous monitoring networks** (MesoWest, NOAA) for site-specific validation
3. **Combine multiple sources** to cover different scales and conditions
4. **Document measurement conditions** thoroughly for reproducibility
5. **Apply proper quality control** before comparison

Most data sources are **free for research purposes** but may require registration or API tokens. Always cite data sources properly in publications.
