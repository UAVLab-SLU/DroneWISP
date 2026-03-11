/**
 * Write a triangle mesh to binary STL.
 * Each triangle: 3 vertices (x,y,z), normal (nx,ny,nz). Origin at (0,0,0) = lat/lon ground.
 */

const fs = require('fs');

/**
 * Write triangles to a binary STL file.
 * @param {string} outputPath - Output file path
 * @param {Array<{ a: [number,number,number], b: [number,number,number], c: [number,number,number] }>} triangles
 */
function validVertex(v) {
  return Array.isArray(v) && v.length >= 3 &&
    Number.isFinite(v[0]) && Number.isFinite(v[1]) && Number.isFinite(v[2]);
}

function writeBinaryStl(outputPath, triangles) {
  const validTriangles = triangles.filter((tri) =>
    tri && validVertex(tri.a) && validVertex(tri.b) && validVertex(tri.c));
  if (validTriangles.length < triangles.length) {
    console.warn('Skipped', triangles.length - validTriangles.length, 'invalid triangle(s)');
  }
  const buffer = Buffer.alloc(84 + validTriangles.length * 50);
  let offset = 0;
  buffer.fill(0, 0, 80);
  offset = 80;
  buffer.writeUInt32LE(validTriangles.length, offset);
  offset += 4;

  for (const tri of validTriangles) {
    const a = tri.a;
    const b = tri.b;
    const c = tri.c;
    const nx = (b[1] - a[1]) * (c[2] - a[2]) - (b[2] - a[2]) * (c[1] - a[1]);
    const ny = (b[2] - a[2]) * (c[0] - a[0]) - (b[0] - a[0]) * (c[2] - a[2]);
    const nz = (b[0] - a[0]) * (c[1] - a[1]) - (b[1] - a[1]) * (c[0] - a[0]);
    const len = Math.sqrt(nx * nx + ny * ny + nz * nz) || 1;
    buffer.writeFloatLE(nx / len, offset); offset += 4;
    buffer.writeFloatLE(ny / len, offset); offset += 4;
    buffer.writeFloatLE(nz / len, offset); offset += 4;
    buffer.writeFloatLE(a[0], offset); offset += 4;
    buffer.writeFloatLE(a[1], offset); offset += 4;
    buffer.writeFloatLE(a[2], offset); offset += 4;
    buffer.writeFloatLE(b[0], offset); offset += 4;
    buffer.writeFloatLE(b[1], offset); offset += 4;
    buffer.writeFloatLE(b[2], offset); offset += 4;
    buffer.writeFloatLE(c[0], offset); offset += 4;
    buffer.writeFloatLE(c[1], offset); offset += 4;
    buffer.writeFloatLE(c[2], offset); offset += 4;
    buffer.writeUInt16LE(0, offset); offset += 2;
  }

  fs.writeFileSync(outputPath, buffer);
}

/**
 * Build triangle list from a height grid in local ENU (x=east, y=north, z=up).
 * Grid: heightGrid[j][i] = z at (xs[i], ys[j]). xs and ys are in meters.
 * @param {number[]} xs - East coordinates (meters), increasing
 * @param {number[]} ys - North coordinates (meters), increasing
 * @param {number[][]} heightGrid - heightGrid[j][i] = height (m) at (xs[i], ys[j])
 * @returns {Array<{ a: [number,number,number], b: [number,number,number], c: [number,number,number] }>}
 */
function heightGridToTriangles(xs, ys, heightGrid) {
  const triangles = [];
  for (let j = 0; j < ys.length - 1; j++) {
    for (let i = 0; i < xs.length - 1; i++) {
      const x0 = xs[i];
      const x1 = xs[i + 1];
      const y0 = ys[j];
      const y1 = ys[j + 1];
      const z00 = heightGrid[j][i];
      const z10 = heightGrid[j][i + 1];
      const z01 = heightGrid[j + 1][i];
      const z11 = heightGrid[j + 1][i + 1];
      if (
        z00 == null || z10 == null || z01 == null || z11 == null ||
        Number.isNaN(z00) || Number.isNaN(z10) || Number.isNaN(z01) || Number.isNaN(z11)
      ) {
        continue;
      }
      const a = [x0, y0, z00];
      const b = [x1, y0, z10];
      const c = [x1, y1, z11];
      const d = [x0, y1, z01];
      triangles.push({ a, b, c });
      triangles.push({ a: d, b: a, c: c });
    }
  }
  return triangles;
}

/**
 * Generate 12 triangles for an axis-aligned cube (6 faces, 2 triangles per face).
 * Cube center (cx, cy, cz), half-size h (cube extends from center ± h in each axis).
 * @param {number} cx - center x (east, m)
 * @param {number} cy - center y (north, m)
 * @param {number} cz - center z (up, m)
 * @param {number} halfSize - half of step size (m)
 * @returns {Array<{ a: [number,number,number], b: [number,number,number], c: [number,number,number] }>}
 */
function cubeToTriangles(cx, cy, cz, halfSize) {
  const h = halfSize;
  const x0 = cx - h;
  const x1 = cx + h;
  const y0 = cy - h;
  const y1 = cy + h;
  const z0 = cz - h;
  const z1 = cz + h;
  const triangles = [];
  const add = (a, b, c) => triangles.push({ a: [...a], b: [...b], c: [...c] });
  add([x0, y0, z0], [x1, y0, z0], [x1, y1, z0]);
  add([x0, y0, z0], [x1, y1, z0], [x0, y1, z0]);
  add([x0, y0, z1], [x1, y1, z1], [x1, y0, z1]);
  add([x0, y0, z1], [x0, y1, z1], [x1, y1, z1]);
  add([x0, y0, z0], [x1, y0, z1], [x1, y0, z0]);
  add([x0, y0, z0], [x0, y0, z1], [x1, y0, z1]);
  add([x1, y0, z0], [x1, y0, z1], [x1, y1, z1]);
  add([x1, y0, z0], [x1, y1, z1], [x1, y1, z0]);
  add([x0, y1, z0], [x1, y1, z1], [x0, y1, z1]);
  add([x0, y1, z0], [x1, y1, z0], [x1, y1, z1]);
  add([x0, y0, z0], [x0, y1, z1], [x0, y1, z0]);
  add([x0, y0, z0], [x0, y0, z1], [x0, y1, z1]);
  return triangles;
}

module.exports = {
  writeBinaryStl,
  heightGridToTriangles,
  cubeToTriangles,
};
