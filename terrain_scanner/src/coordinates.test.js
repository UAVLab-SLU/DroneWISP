const c = require('./coordinates');

test('geodeticToLocalEnu at origin returns zero', () => {
  const out = c.geodeticToLocalEnu(-87.63, 41.88, 180, -87.63, 41.88, 180);
  expect(out.x).toBe(0);
  expect(out.y).toBe(0);
  expect(out.z).toBe(0);
});

test('localEnuToGeodetic round-trips with geodeticToLocalEnu', () => {
  const geo = c.localEnuToGeodetic(-87.63, 41.88, 180, 100, 200, 10);
  const local = c.geodeticToLocalEnu(-87.63, 41.88, 180, geo.lon, geo.lat, geo.height);
  expect(local.x).toBeCloseTo(100, 0);
  expect(local.y).toBeCloseTo(200, 0);
  expect(local.z).toBeCloseTo(10, 0);
});

test('buildSampleGrid includes origin and correct extent', () => {
  const { xs, ys } = c.buildSampleGrid(10, 10, 5);
  expect(xs).toContain(0);
  expect(ys).toContain(0);
  expect(Math.min(...xs)).toBe(-10);
  expect(Math.max(...xs)).toBe(10);
});
