/**
 * Voxel occupancy: terrain height in voxel z-range, and triangle-box intersection for buildings.
 */

function pointInBox(p, boxMin, boxMax) {
  if (!p || !Array.isArray(p) || p.length < 3 || !boxMin || !boxMax) return false;
  return p[0] >= boxMin[0] && p[0] <= boxMax[0] &&
    p[1] >= boxMin[1] && p[1] <= boxMax[1] &&
    p[2] >= boxMin[2] && p[2] <= boxMax[2];
}

function projectPointOnTriangle(p, a, b, c) {
  const n = [
    (b[1] - a[1]) * (c[2] - a[2]) - (b[2] - a[2]) * (c[1] - a[1]),
    (b[2] - a[2]) * (c[0] - a[0]) - (b[0] - a[0]) * (c[2] - a[2]),
    (b[0] - a[0]) * (c[1] - a[1]) - (b[1] - a[1]) * (c[0] - a[0]),
  ];
  const nDot = n[0] * n[0] + n[1] * n[1] + n[2] * n[2];
  if (nDot < 1e-20) return { inside: false };
  const dist = ((p[0] - a[0]) * n[0] + (p[1] - a[1]) * n[1] + (p[2] - a[2]) * n[2]) / nDot;
  const px = p[0] - n[0] * dist;
  const py = p[1] - n[1] * dist;
  const pz = p[2] - n[2] * dist;
  const e1x = b[0] - a[0];
  const e1y = b[1] - a[1];
  const e1z = b[2] - a[2];
  const e2x = c[0] - a[0];
  const e2y = c[1] - a[1];
  const e2z = c[2] - a[2];
  const dx = px - a[0];
  const dy = py - a[1];
  const dz = pz - a[2];
  const d11 = e1x * e1x + e1y * e1y + e1z * e1z;
  const d12 = e1x * e2x + e1y * e2y + e1z * e2z;
  const d22 = e2x * e2x + e2y * e2y + e2z * e2z;
  const d1p = e1x * dx + e1y * dy + e1z * dz;
  const d2p = e2x * dx + e2y * dy + e2z * dz;
  const denom = d11 * d22 - d12 * d12;
  if (Math.abs(denom) < 1e-20) return { inside: false };
  const u = (d22 * d1p - d12 * d2p) / denom;
  const v = (d11 * d2p - d12 * d1p) / denom;
  return { inside: u >= -1e-9 && v >= -1e-9 && u + v <= 1 + 1e-9 };
}

function pointInTriangle(p, a, b, c) {
  return projectPointOnTriangle(p, a, b, c).inside;
}

function segmentIntersectsBox(A, B, boxMin, boxMax) {
  if (!A || !B || !Array.isArray(A) || !Array.isArray(B) || A.length < 3 || B.length < 3 || !boxMin || !boxMax) return false;
  let tMin = 0;
  let tMax = 1;
  for (let i = 0; i < 3; i++) {
    const o = A[i];
    const d = B[i] - A[i];
    const lo = boxMin[i];
    const hi = boxMax[i];
    if (Math.abs(d) < 1e-15) {
      if (o < lo || o > hi) return false;
      continue;
    }
    const t1 = (lo - o) / d;
    const t2 = (hi - o) / d;
    const tLo = Math.min(t1, t2);
    const tHi = Math.max(t1, t2);
    tMin = Math.max(tMin, tLo);
    tMax = Math.min(tMax, tHi);
    if (tMin > tMax) return false;
  }
  return true;
}

function triangleIntersectsBox(a, b, c, boxMin, boxMax) {
  if (!a || !b || !c || !boxMin || !boxMax) return false;
  if (pointInBox(a, boxMin, boxMax) || pointInBox(b, boxMin, boxMax) || pointInBox(c, boxMin, boxMax)) {
    return true;
  }
  const corners = [
    [boxMin[0], boxMin[1], boxMin[2]],
    [boxMax[0], boxMin[1], boxMin[2]],
    [boxMax[0], boxMax[1], boxMin[2]],
    [boxMin[0], boxMax[1], boxMin[2]],
    [boxMin[0], boxMin[1], boxMax[2]],
    [boxMax[0], boxMin[1], boxMax[2]],
    [boxMax[0], boxMax[1], boxMax[2]],
    [boxMin[0], boxMax[1], boxMax[2]],
  ];
  for (const p of corners) {
    if (pointInTriangle(p, a, b, c)) return true;
  }
  if (segmentIntersectsBox(a, b, boxMin, boxMax)) return true;
  if (segmentIntersectsBox(b, c, boxMin, boxMax)) return true;
  if (segmentIntersectsBox(c, a, boxMin, boxMax)) return true;
  return false;
}

function voxelOccupiedByTerrain(terrainZ, voxelZCenter, halfSize) {
  const zMin = voxelZCenter - halfSize;
  const zMax = voxelZCenter + halfSize;
  return terrainZ >= zMin - 1e-9 && terrainZ <= zMax + 1e-9;
}

/**
 * Voxel occupied by top surface (terrain or building) from headless scan.
 * topHeightLocal is height above ground (m) of the top at this (east, north).
 */
function voxelOccupiedByTopSurface(topHeightLocal, voxelZCenter, halfSize) {
  const zMin = voxelZCenter - halfSize;
  return topHeightLocal >= zMin - 1e-9;
}

function voxelOccupiedByBuildings(boxMin, boxMax, buildingTriangles) {
  if (!buildingTriangles || !boxMin || !boxMax) return false;
  for (const tri of buildingTriangles) {
    const a = tri && tri.a;
    const b = tri && tri.b;
    const c = tri && tri.c;
    if (!a || !b || !c || !Array.isArray(a) || !Array.isArray(b) || !Array.isArray(c) || a.length < 3 || b.length < 3 || c.length < 3) continue;
    if (triangleIntersectsBox(a, b, c, boxMin, boxMax)) return true;
  }
  return false;
}

module.exports = {
  voxelOccupiedByTerrain,
  voxelOccupiedByBuildings,
  voxelOccupiedByTopSurface,
};
