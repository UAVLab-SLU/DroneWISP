/**
 * Fetch OpenStreetMap buildings in a bounding box and extrude them to triangles
 * in local ENU (same coordinate system as terrain). Adds height diversity to
 * urban scans (e.g. Chicago) where Cesium terrain alone is flat.
 */

const https = require('https');
const { geodeticToLocalEnu } = require('./coordinates');
const { METERS_PER_DEG_LAT } = require('./coordinates');

const OVERPASS_URL = 'https://overpass-api.de/api/interpreter';
const DEFAULT_METERS_PER_LEVEL = 3;
const DEFAULT_HEIGHT_M = 5;

/**
 * Parse OSM height tag (e.g. "20m", "50 ft", "7") to meters.
 * @param {string} value - Tag value
 * @returns {number} Height in meters, or null if unparseable
 */
function parseHeightTag(value) {
  if (value == null || typeof value !== 'string') return null;
  const s = value.trim();
  const m = s.match(/^([\d.]+)\s*(m|meters?|ft|feet|')?$/i);
  if (!m) return null;
  let num = parseFloat(m[1]);
  if (Number.isNaN(num)) return null;
  const unit = (m[2] || '').toLowerCase();
  if (unit.startsWith('ft') || unit === "'") num *= 0.3048;
  return num > 0 ? num : null;
}

/**
 * Get building height in meters from OSM tags.
 * Uses "height", then "building:levels" (× DEFAULT_METERS_PER_LEVEL).
 * @param {Record<string, string>} tags
 * @returns {number}
 */
function getBuildingHeight(tags) {
  const height = parseHeightTag(tags && tags.height);
  if (height != null) return height;
  const levels = tags && tags['building:levels'];
  if (levels != null) {
    const n = parseFloat(levels);
    if (!Number.isNaN(n) && n > 0) return n * DEFAULT_METERS_PER_LEVEL;
  }
  return DEFAULT_HEIGHT_M;
}

/**
 * Compute centroid of a polygon (array of [x,y]).
 * @param {Array<[number, number]>} ring
 * @returns {[number, number]}
 */
function polygonCentroid(ring) {
  let cx = 0;
  let cy = 0;
  let area = 0;
  const n = ring.length;
  for (let i = 0; i < n; i++) {
    const j = (i + 1) % n;
    const pi = ring[i];
    const pj = ring[j];
    if (!pi || !pj || pi.length < 2 || pj.length < 2) continue;
    const cross = pi[0] * pj[1] - pj[0] * pi[1];
    area += cross;
    cx += (pi[0] + pj[0]) * cross;
    cy += (pi[1] + pj[1]) * cross;
  }
  area *= 0.5;
  if (Math.abs(area) < 1e-12 || !Number.isFinite(area)) {
    cx = ring.reduce((s, p) => (p && p[0] != null ? s + p[0] : s), 0) / (n || 1);
    cy = ring.reduce((s, p) => (p && p[1] != null ? s + p[1] : s), 0) / (n || 1);
    return [Number.isFinite(cx) ? cx : 0, Number.isFinite(cy) ? cy : 0];
  }
  cx /= 6 * area;
  cy /= 6 * area;
  return [Number.isFinite(cx) ? cx : 0, Number.isFinite(cy) ? cy : 0];
}

/**
 * Triangulate a simple polygon with a fan from centroid (roof).
 * Vertices in local ENU (x, y). Output z is set when building triangles.
 * @param {Array<[number, number]>} ring - Closed polygon (x,y)
 * @param {number} z
 * @returns {Array<{ a: [number,number,number], b: [number,number,number], c: [number,number,number] }>}
 */
function triangulatePolygonAtZ(ring, z) {
  const triangles = [];
  const [cx, cy] = polygonCentroid(ring);
  const center = [cx, cy, z];
  const n = ring.length;
  for (let i = 0; i < n; i++) {
    const j = (i + 1) % n;
    const pi = ring[i];
    const pj = ring[j];
    if (!pi || !pj || pi.length < 2 || pj.length < 2) continue;
    const a = [pi[0], pi[1], z];
    const b = [pj[0], pj[1], z];
    triangles.push({ a: center.slice(), b: a, c: b });
  }
  return triangles;
}

/**
 * Build wall triangles for one segment (p0 at z0, p1 at z1) and height h.
 * p0, p1 are [x,y]; we extrude from z=0 to z=h.
 * @param {[number, number]} p0
 * @param {[number, number]} p1
 * @param {number} h
 * @returns {Array<{ a: [number,number,number], b: [number,number,number], c: [number,number,number] }>}
 */
function wallQuad(p0, p1, h) {
  const a = [p0[0], p0[1], 0];
  const b = [p1[0], p1[1], 0];
  const c = [p1[0], p1[1], h];
  const d = [p0[0], p0[1], h];
  return [
    { a, b, c },
    { a, c, d },
  ];
}

/**
 * Fetch buildings from Overpass and return triangles in local ENU.
 * @param {Object} options
 * @param {number} options.originLon - Center longitude (degrees)
 * @param {number} options.originLat - Center latitude (degrees)
 * @param {number} options.originHeightM - Ground height at origin (m)
 * @param {number} options.rangeX - Half extent east (m)
 * @param {number} options.rangeY - Half extent north (m)
 * @returns {Promise<Array<{ a: [number,number,number], b: [number,number,number], c: [number,number,number] }>>}
 */
async function fetchBuildingsInBbox(options) {
  const { originLon, originLat, originHeightM, rangeX, rangeY } = options;
  const latRad = (originLat * Math.PI) / 180;
  const metersPerDegLon = METERS_PER_DEG_LAT * Math.cos(latRad);
  const south = originLat - rangeY / METERS_PER_DEG_LAT;
  const north = originLat + rangeY / METERS_PER_DEG_LAT;
  const west = originLon - rangeX / metersPerDegLon;
  const east = originLon + rangeX / metersPerDegLon;

  const query = `[out:json][timeout:25];
(
  way["building"](${south},${west},${north},${east});
);
out body geom;`;

  const body = await postOverpass(query);
  const elements = (body && body.elements) || [];
  const allTriangles = [];

  for (const el of elements) {
    if (el.type !== 'way' || !el.geometry || el.geometry.length < 3) continue;
    try {
      const ring = [];
      for (const node of el.geometry) {
        const lon = node.lon;
        const lat = node.lat;
        if (typeof lon !== 'number' || typeof lat !== 'number' || !Number.isFinite(lon) || !Number.isFinite(lat)) continue;
        const local = geodeticToLocalEnu(originLon, originLat, originHeightM, lon, lat, 0);
        ring.push([local.x, local.y]);
      }
      const ringFiltered = ring.filter((p) => Array.isArray(p) && p.length >= 2 && Number.isFinite(p[0]) && Number.isFinite(p[1]));
      if (ringFiltered.length < 3) continue;
      const height = getBuildingHeight(el.tags);
      const roofTris = triangulatePolygonAtZ(ringFiltered, height);
      allTriangles.push(...roofTris);
      const n = ringFiltered.length;
      for (let i = 0; i < n; i++) {
        const j = (i + 1) % n;
        const p0 = ringFiltered[i];
        const p1 = ringFiltered[j];
        if (p0 && p1 && p0.length >= 2 && p1.length >= 2) allTriangles.push(...wallQuad(p0, p1, height));
      }
    } catch (err) {
      console.warn('Skip building', el.id, err.message);
    }
  }

  return allTriangles;
}

function postOverpass(query) {
  return new Promise((resolve, reject) => {
    const url = new URL(OVERPASS_URL);
    const post = Buffer.from(query, 'utf8');
    const opts = {
      hostname: url.hostname,
      port: 443,
      path: url.pathname + url.search,
      method: 'POST',
      headers: {
        'Content-Type': 'application/x-www-form-urlencoded',
        'Content-Length': post.length,
      },
    };
    const req = https.request(opts, (res) => {
      let data = '';
      res.on('data', (chunk) => { data += chunk; });
      res.on('end', () => {
        if (res.statusCode !== 200) {
          reject(new Error(`Overpass API returned ${res.statusCode}: ${data.slice(0, 200)}`));
          return;
        }
        try {
          resolve(JSON.parse(data));
        } catch (e) {
          reject(new Error('Overpass API returned invalid JSON'));
        }
      });
    });
    req.on('error', reject);
    req.write(post);
    req.end();
  });
}

module.exports = {
  fetchBuildingsInBbox,
  getBuildingHeight,
  parseHeightTag,
};
