/**
 * Integration test: full pipeline from grid + height data to STL file (no Cesium).
 * Validates that for any location parameters we can produce a valid STL.
 */
const fs = require('fs');
const os = require('os');
const path = require('path');
const { buildSampleGrid } = require('../src/coordinates');
const { heightGridToTriangles, writeBinaryStl } = require('../src/stlWriter');

function buildFakeHeightGrid(xs, ys, groundHeightM = 180) {
  const grid = [];
  for (let j = 0; j < ys.length; j++) {
    const row = [];
    for (let i = 0; i < xs.length; i++) {
      row.push(groundHeightM + Math.sin(xs[i] * 0.01) * 2 + Math.cos(ys[j] * 0.01) * 2);
    }
    grid.push(row);
  }
  return grid;
}

test('full pipeline produces valid STL for given range and resolution', () => {
  const rangeX = 50;
  const rangeY = 50;
  const resolution = 10;
  const { xs, ys } = buildSampleGrid(rangeX, rangeY, resolution);
  const heightGrid = buildFakeHeightGrid(xs, ys, 180);
  const triangles = heightGridToTriangles(xs, ys, heightGrid);
  expect(triangles.length).toBeGreaterThan(0);

  const outPath = path.join(os.tmpdir(), `terrain_scanner_${Date.now()}.stl`);
  writeBinaryStl(outPath, triangles);
  try {
    expect(fs.existsSync(outPath)).toBe(true);
    const size = fs.statSync(outPath).size;
    expect(size).toBe(84 + triangles.length * 50);
    const full = fs.readFileSync(outPath);
    const buf = full.slice(0, 84);
    expect(buf.length).toBe(84);
    const numTri = full.readUInt32LE(80);
    expect(numTri).toBe(triangles.length);
  } finally {
    fs.unlinkSync(outPath);
  }
});

test('pipeline works for asymmetric range and different resolution', () => {
  const { xs, ys } = buildSampleGrid(200, 100, 25);
  const heightGrid = buildFakeHeightGrid(xs, ys, 0);
  const triangles = heightGridToTriangles(xs, ys, heightGrid);
  const outPath = path.join(os.tmpdir(), `terrain_scanner_${Date.now()}.stl`);
  writeBinaryStl(outPath, triangles);
  try {
    expect(fs.existsSync(outPath)).toBe(true);
    expect(fs.statSync(outPath).size).toBe(84 + triangles.length * 50);
  } finally {
    fs.unlinkSync(outPath);
  }
});
