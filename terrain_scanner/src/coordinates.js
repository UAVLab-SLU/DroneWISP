/**
 * Geodetic (WGS84) to local East-North-Up (ENU) conversion.
 * Local origin is at (originLon, originLat, originHeightM).
 * Output: X = east (m), Y = north (m), Z = up (m).
 */

const DEG2RAD = Math.PI / 180;

// WGS84 approximate: 1 degree latitude in meters (average)
const METERS_PER_DEG_LAT = 111320;
// At a given latitude, meters per degree longitude = METERS_PER_DEG_LAT * cos(lat)
function metersPerDegLon(latRad) {
  return METERS_PER_DEG_LAT * Math.cos(latRad);
}

/**
 * Convert a meter offset (east, north, up) from origin to (lat, lon, height).
 * Origin is (originLon, originLat) in degrees, originHeightM in meters.
 * @param {number} originLon - longitude in degrees
 * @param {number} originLat - latitude in degrees
 * @param {number} originHeightM - height in meters (e.g. ground)
 * @param {number} eastM - offset east in meters
 * @param {number} northM - offset north in meters
 * @param {number} upM - offset up in meters
 * @returns {{ lon: number, lat: number, height: number }} in degrees and meters
 */
function localEnuToGeodetic(originLon, originLat, originHeightM, eastM, northM, upM) {
  const latRad = originLat * DEG2RAD;
  const dLatDeg = northM / METERS_PER_DEG_LAT;
  const dLonDeg = eastM / (METERS_PER_DEG_LAT * Math.cos(latRad));
  return {
    lon: originLon + dLonDeg,
    lat: originLat + dLatDeg,
    height: originHeightM + upM,
  };
}

/**
 * Convert (lon, lat, height) to local ENU relative to (originLon, originLat, originHeightM).
 * @returns {{ x: number, y: number, z: number }} east, north, up in meters
 */
function geodeticToLocalEnu(originLon, originLat, originHeightM, lon, lat, heightM) {
  const latRad = originLat * DEG2RAD;
  const dLatDeg = lat - originLat;
  const dLonDeg = lon - originLon;
  const northM = dLatDeg * METERS_PER_DEG_LAT;
  const eastM = dLonDeg * METERS_PER_DEG_LAT * Math.cos(latRad);
  const upM = heightM - originHeightM;
  return { x: eastM, y: northM, z: upM };
}

/**
 * Build a 2D grid of (east, north) sample positions in meters.
 * Grid is centered at origin; extent is [-rangeX, rangeX] in X and [-rangeY, rangeY] in Y.
 * @param {number} rangeX - half-extent X (east), meters
 * @param {number} rangeY - half-extent Y (north), meters
 * @param {number} resolutionM - spacing between samples, meters
 * @returns {{ xs: number[], ys: number[] }} xs = east values, ys = north values (ordered)
 */
function buildSampleGrid(rangeX, rangeY, resolutionM) {
  const xs = [];
  for (let x = -rangeX; x <= rangeX + 1e-9; x += resolutionM) {
    xs.push(Math.round(x * 1e9) / 1e9);
  }
  const ys = [];
  for (let y = -rangeY; y <= rangeY + 1e-9; y += resolutionM) {
    ys.push(Math.round(y * 1e9) / 1e9);
  }
  return { xs, ys };
}

/**
 * Build 3D voxel grid centers. X/Y as in buildSampleGrid; Z from ground (0) to rangeZ.
 * @param {number} rangeX - half-extent X (east), meters
 * @param {number} rangeY - half-extent Y (north), meters
 * @param {number} rangeZ - height of bounding box (meters above ground)
 * @param {number} stepSize - voxel step in x, y, z (meters)
 * @returns {{ xs: number[], ys: number[], zs: number[] }}
 */
function buildVoxelGrid(rangeX, rangeY, rangeZ, stepSize) {
  const xs = [];
  for (let x = -rangeX; x <= rangeX + 1e-9; x += stepSize) {
    xs.push(Math.round(x * 1e9) / 1e9);
  }
  const ys = [];
  for (let y = -rangeY; y <= rangeY + 1e-9; y += stepSize) {
    ys.push(Math.round(y * 1e9) / 1e9);
  }
  const zs = [];
  for (let z = stepSize / 2; z <= rangeZ + 1e-9; z += stepSize) {
    zs.push(Math.round(z * 1e9) / 1e9);
  }
  return { xs, ys, zs };
}

module.exports = {
  METERS_PER_DEG_LAT,
  metersPerDegLon,
  localEnuToGeodetic,
  geodeticToLocalEnu,
  buildSampleGrid,
  buildVoxelGrid,
};
