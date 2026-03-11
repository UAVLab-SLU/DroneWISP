# Terrain Scanner

Produces an STL voxel mesh from the same Cesium terrain and 3D Tiles source used by the SADE-GUI. The mesh is in local Cartesian coordinates with origin `(0, 0, 0)` at the given latitude, longitude, and ground height.

## Terrain and buildings

- **Elevation**: Cesium World Terrain (`createWorldTerrainAsync`), sampled with `sampleTerrainMostDetailed` (same as SADE-GUI).
- **Buildings**: When `--buildings` is used (default), the scanner tries sources in order until one returns usable geometry:
  1. **OSM buildings (preferred)**: Fetches building footprints from OpenStreetMap Overpass in the bounding box, extrudes them to 3D (roof + walls) in local ENU, then voxelizes with triangle–box intersection. This produces full 3D (terrain + buildings at multiple height layers) and does not require Cesium Ion 3D Tiles or a browser. No API key beyond the terrain token.
  2. **Google 3D Tiles mesh**: If OSM returns no buildings, fetches Google Photorealistic 3D Tiles (Ion or Google API), parses b3dm into triangles in local ENU, and voxelizes. This path can fail if tile transforms do not produce valid local coordinates.
  3. **Headless Cesium**: If no mesh is used, a headless browser (Puppeteer) loads 3D Tiles and samples the top surface per column; in headless Chrome, 3D Tiles may not participate in picking, so you may get terrain only.
- Use `--no-buildings` for terrain-only output (flat or single-layer).

## Requirements

- Node.js 18+
- `CESIUM_ION_ACCESS_TOKEN`: same token as SADE-GUI (`REACT_APP_CESIUM_ION_ACCESS_TOKEN`). Cesium World Terrain and Ion 3D Tiles use it.
- **Buildings (headless)**: `puppeteer` is an optional dependency. Install with `npm install` (optionalDependencies). If Puppeteer is missing or headless scan fails, the scanner falls back to terrain-only.

## Usage

**Option A: token from file (e.g. `token` in project root)**

```bash
npm install
npm run scan -- --latitude 41.8781 --longitude -87.6298 --range-x 200 --range-y 200 --output ./out.stl --token-file ./token
```

**Option B: token from environment**

```bash
export CESIUM_ION_ACCESS_TOKEN='your-token'
npm run scan -- --latitude 41.8781 --longitude -87.6298 --range-x 200 --range-y 200 --output ./out.stl
```

### Parameters

| Option       | Description                                              |
|-------------|----------------------------------------------------------|
| `--latitude`  | Center latitude (degrees).                               |
| `--longitude` | Center longitude (degrees).                              |
| `--range-x`   | Half-extent in X (east) direction, meters (default 100).  |
| `--range-y`   | Half-extent in Y (north) direction, meters (default 100). |
| `--range-z`   | Vertical extent above ground, meters (default 50).       |
| `--resolution`| Grid resolution in meters (default 5).                   |
| `--token-file`| Path to file containing Cesium Ion token (optional).     |
| `--no-buildings` | Skip headless building scan (terrain-only output). |
| `--output`    | Output STL file path (required).                          |

Output STL: origin `(0, 0, 0)` is at (latitude, longitude) at ground height; X = east, Y = north, Z = up, in meters.

## Tests

```bash
npm test
```

Tests cover coordinate conversion, grid generation, and STL writing without hitting the Cesium API.
