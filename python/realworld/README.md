# Realworld Wind Data and CFD Validation Case

This folder contains scripts to fetch wind data, find station clusters, plot maps, and build building geometry from OpenStreetMap for CFD validation. It also includes the current Hofstra cluster case files used for validation.

## Case Summary: Hofstra Cluster (100 m to 1 km spacing)

Stations:
- 0512W, Hofstra University South Campus
- 0514W, Hofstra Soccer Stadium
- 0516W, Hofstra Student Garden

Data and outputs:
- `nyc_100m_1km_cluster_wind.csv` contains Synoptic wind data for the three stations.
- `nyc_100m_1km_cluster_map_vectors.png` shows the stations with wind vectors at `2026-01-10T00:20:00Z`.
- `nyc_100m_1km_cluster_bbox.png` shows the bounding box used for geometry extraction.
- `nyc_100m_1km_cluster_buildings.stl` contains extruded OSM building geometry inside the bounding box.

Bounding box rules for the geometry:
- North wall passes through station `0514W`.
- South wall is 50 m south of station `0512W`.
- Longitude to latitude ratio is 1:2.

STL local coordinates for measurement points (origin at the bounding box center):
- `0512W`: `x=16.031`, `y=-266.102`, `z=0.0`
- `0514W`: `x=-16.031`, `y=316.102`, `z=0.0`

## Scripts

### `synoptic_wind_fetcher.py`
Fetches wind time series data from Synoptic and validates temporal resolution.

Example (expanded time window used in this case):
```
python3 synoptic_wind_fetcher.py \
  --stids 0512W,0514W,0516W \
  --start "2026-01-01 00:00" \
  --end "2026-01-14 23:50" \
  --out nyc_100m_1km_cluster_wind.csv
```

### `find_synoptic_dense_cluster.py`
Finds station clusters that match spacing constraints.

Example:
```
python3 find_synoptic_dense_cluster.py \
  --lat 40.7128 \
  --lon -74.0060 \
  --radius-km 25 \
  --min-distance-m 100 \
  --max-distance-m 1000 \
  --min-stations 3
```

### `plot_station_map.py`
Plots station locations on a map and optionally overlays wind vectors at a timestamp.

Example:
```
python3 plot_station_map.py \
  --csv nyc_100m_1km_cluster_wind.csv \
  --out nyc_100m_1km_cluster_map_vectors.png \
  --zoom 17 \
  --timestamp "2026-01-10T00:20:00Z"
```

### `plot_bbox.py`
Computes and plots the case bounding box as the map extent.

Example:
```
python3 plot_bbox.py \
  --csv nyc_100m_1km_cluster_wind.csv \
  --north-stid 0514W \
  --south-stid 0512W \
  --south-offset-m 50 \
  --ratio-long-lat 1:2 \
  --zoom 17 \
  --out nyc_100m_1km_cluster_bbox.png
```

### `osm_buildings_to_stl.py`
Fetches OSM buildings in the bounding box and exports STL geometry.

Example:
```
python3 osm_buildings_to_stl.py \
  --south 40.7126308444125 \
  --west -73.60032317563183 \
  --north 40.71831 \
  --east -73.59657682436817 \
  --out nyc_100m_1km_cluster_buildings.stl
```

### `filter_wind_direction.py`
Filters wind data by direction sectors.

Example:
```
python3 filter_wind_direction.py \
  --csv nyc_100m_1km_cluster_wind.csv \
  --out nyc_100m_1km_cluster_wind_north_ne.csv \
  --sectors north,northeast
```

### `wind_data_fetcher.py`
Fetches ASOS wind data from the IEM archive for quick checks.

Example:
```
python3 wind_data_fetcher.py \
  --station KJFK \
  --start "2025-01-01 00:00" \
  --end "2025-01-02 00:00" \
  --out kjfk_wind_sample.csv
```

### `find_urban_asos_cluster.py`
Finds nearby ASOS stations using either IEM or a local catalog fallback.

Example:
```
python3 find_urban_asos_cluster.py \
  --city nyc \
  --radius-km 40 \
  --max-stations 6
```

