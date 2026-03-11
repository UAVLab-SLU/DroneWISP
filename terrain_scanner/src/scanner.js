const {
  Cartographic,
  createWorldTerrainAsync,
  sampleTerrainMostDetailed,
  Ion,
} = require('cesium');
const { localEnuToGeodetic, geodeticToLocalEnu, buildSampleGrid } = require('./coordinates');
const { writeBinaryStl, heightGridToTriangles } = require('./stlWriter');
const { startVisualScanServer } = require('./visualScanServer');
const open = (function() {
  const o = require('open');
  return o.default != null ? o.default : o;
})();

async function getGroundHeight(terrainProvider, longitude, latitude) {
  const position = Cartographic.fromDegrees(longitude, latitude);
  const positions = [position];
  await sampleTerrainMostDetailed(terrainProvider, positions);
  const height = positions[0].height;
  return height != null && !Number.isNaN(height) ? height : null;
}

function wrapCesiumError(err, context) {
  if (err && typeof err.statusCode === 'number') {
    if (err.statusCode === 401) {
      return new Error(
        'Cesium Ion returned 401 Unauthorized. Set CESIUM_ION_ACCESS_TOKEN to a valid token (same as SADE-GUI REACT_APP_CESIUM_ION_ACCESS_TOKEN).'
      );
    }
    return new Error(`Terrain request failed (${context}): HTTP ${err.statusCode}. ${err.message || ''}`);
  }
  return err instanceof Error ? err : new Error(String(err));
}

function resolveToken(tokenFile) {
  if (tokenFile) {
    const fs = require('fs');
    const path = require('path');
    const p = path.isAbsolute(tokenFile) ? tokenFile : path.resolve(process.cwd(), tokenFile);
    if (!fs.existsSync(p)) throw new Error('Token file not found: ' + tokenFile);
    return fs.readFileSync(p, 'utf8').trim();
  }
  return process.env.CESIUM_ION_ACCESS_TOKEN || null;
}

async function scanTerrainToStl(options) {
  const { latitude, longitude, rangeX = 100, rangeY = 100, resolution = 5, output, tokenFile, includeBuildings = true } = options;
  const token = resolveToken(tokenFile);
  if (!token) throw new Error('No token. Set CESIUM_ION_ACCESS_TOKEN or use --token-file <path>.');
  Ion.defaultAccessToken = token;
  const stepSize = resolution;

  let terrainProvider;
  try {
    terrainProvider = await createWorldTerrainAsync();
  } catch (err) {
    throw wrapCesiumError(err, 'createWorldTerrain');
  }
  let groundHeight;
  try {
    groundHeight = await getGroundHeight(terrainProvider, longitude, latitude);
  } catch (err) {
    throw wrapCesiumError(err, 'getGroundHeight');
  }
  if (groundHeight == null) throw new Error('Could not get terrain height at (' + longitude + ',' + latitude + ').');

  const { xs, ys } = buildSampleGrid(rangeX, rangeY, stepSize);
  const nx = xs.length;
  const ny = ys.length;

  const positions = [];
  for (let j = 0; j < ny; j++) {
    for (let i = 0; i < nx; i++) {
      const geo = localEnuToGeodetic(longitude, latitude, groundHeight, xs[i], ys[j], 0);
      positions.push(Cartographic.fromDegrees(geo.lon, geo.lat));
    }
  }
  try {
    await sampleTerrainMostDetailed(terrainProvider, positions);
  } catch (err) {
    throw wrapCesiumError(err, 'sampleTerrain');
  }

  const heightGrid = [];
  let idx = 0;
  for (let j = 0; j < ny; j++) {
    const row = [];
    for (let i = 0; i < nx; i++) {
      const pos = positions[idx++];
      const height = pos.height != null && !Number.isNaN(pos.height) ? pos.height : groundHeight;
      const local = geodeticToLocalEnu(longitude, latitude, groundHeight, pos.longitude, pos.latitude, height);
      row.push(local.z);
    }
    heightGrid.push(row);
  }

  let triangles;

  if (includeBuildings) {
    console.warn('Visual scan: opening browser to sample top surface (Cesium + Google 3D Tiles)...');
    const params = {
      originLon: longitude,
      originLat: latitude,
      groundHeight,
      rangeX,
      rangeY,
      stepSize,
      ionToken: token,
    };
    const { server, url, resultPromise } = await startVisualScanServer(params);
    await open(url);
    const timeoutMs = 300000;
    const data = await Promise.race([
      resultPromise,
      new Promise((_, reject) =>
        setTimeout(() => reject(new Error('Visual scan timed out after ' + timeoutMs / 1000 + 's. Close the browser and try again.')), timeoutMs)
      ),
    ]).finally(() => {
      server.close();
    });
    if (!data || !data.xs || !data.ys || !data.topSurfaceHeightGrid) {
      throw new Error('Visual scan did not return height map. Check the browser for errors.');
    }
    const gh = data.groundHeight != null ? data.groundHeight : groundHeight;
    const localZGrid = (data.topSurfaceHeightGrid || []).map((row) =>
      row.map((h) => (typeof h === 'number' && !Number.isNaN(h) ? h - gh : 0))
    );
    triangles = heightGridToTriangles(data.xs, data.ys, localZGrid);
    console.warn('Visual scan: height map', (data.xs || []).length, 'x', (data.ys || []).length);
  } else {
    triangles = heightGridToTriangles(xs, ys, heightGrid);
  }

  writeBinaryStl(output, triangles);
  return { groundHeight, numTriangles: triangles.length };
}

module.exports = { getGroundHeight, scanTerrainToStl, resolveToken };
