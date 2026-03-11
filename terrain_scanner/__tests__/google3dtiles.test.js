/**
 * Tests that Google 3D Tiles building data is correctly used and loaded:
 * - Tile selection: regionIntersectsBox, getTileRegion, getContentUrl
 * - fetchGoogle3DTilesInBbox: requires googleApiKey or accessToken (throws otherwise)
 * - Building triangles in voxel occupancy: voxelOccupiedByBuildings true when
 *   triangle intersects box, false when far or empty list
 * Full fetch (network + loaders.gl) is not run in Jest due to dynamic ESM import.
 */

const {
  fetchGoogle3DTilesInBbox,
  GOOGLE_3D_TILES_ASSET_ID,
  regionIntersectsBox,
  getTileRegion,
  getContentUrl,
  collectTilesInRegion,
  GOOGLE_3DTILES_ROOT,
} = require('../src/google3dtiles');

const { voxelOccupiedByBuildings, voxelOccupiedByTerrain } = require('../src/voxelOccupancy');
const { buildVoxelGrid } = require('../src/coordinates');

describe('Google 3D Tiles helpers', () => {
  test('regionIntersectsBox returns true when region overlaps box', () => {
    const region = [-87.63 * (Math.PI / 180), 41.88 * (Math.PI / 180), -87.62 * (Math.PI / 180), 41.89 * (Math.PI / 180), 0, 200];
    const westDeg = -87.625;
    const southDeg = 41.875;
    const eastDeg = -87.615;
    const northDeg = 41.885;
    expect(regionIntersectsBox(region, westDeg, southDeg, eastDeg, northDeg, 0, 500)).toBe(true);
  });

  test('regionIntersectsBox returns false when region is west of box', () => {
    const region = [-87.64 * (Math.PI / 180), 41.88 * (Math.PI / 180), -87.63 * (Math.PI / 180), 41.89 * (Math.PI / 180), 0, 200];
    const westDeg = -87.62;
    const southDeg = 41.875;
    const eastDeg = -87.61;
    const northDeg = 41.885;
    expect(regionIntersectsBox(region, westDeg, southDeg, eastDeg, northDeg, 0, 500)).toBe(false);
  });

  test('getTileRegion returns region when boundingVolume.region is present', () => {
    const tile = {
      boundingVolume: {
        region: [1, 2, 3, 4, 0, 100],
      },
    };
    const result = getTileRegion(tile);
    expect(result).toEqual([1, 2, 3, 4, 0, 100]);
  });

  test('getTileRegion returns null for tile without boundingVolume', () => {
    expect(getTileRegion({})).toBeNull();
    expect(getTileRegion({ boundingVolume: null })).toBeNull();
  });

  test('getContentUrl resolves relative URI against basePath', () => {
    const tile = { content: { uri: 'tiles/0.b3dm' } };
    const basePath = 'https://tile.googleapis.com/v1/3dtiles';
    expect(getContentUrl(tile, basePath)).toBe('https://tile.googleapis.com/v1/3dtiles/tiles/0.b3dm');
  });

  test('getContentUrl returns absolute URI unchanged', () => {
    const tile = { content: { uri: 'https://example.com/tile.b3dm' } };
    expect(getContentUrl(tile, 'https://other.com')).toBe('https://example.com/tile.b3dm');
  });
});

describe('fetchGoogle3DTilesInBbox', () => {
  test('throws when neither Google API key nor Cesium token provided', async () => {
    await expect(
      fetchGoogle3DTilesInBbox({
        originLon: -87.625,
        originLat: 41.885,
        originHeightM: 140,
        rangeX: 100,
        rangeY: 100,
        googleApiKey: null,
        accessToken: null,
      })
    ).rejects.toThrow(/Google 3D Tiles require/);
  });
});

describe('3D voxel grid (z > 0)', () => {
  test('buildVoxelGrid produces multiple z levels when rangeZ > stepSize', () => {
    const { xs, ys, zs } = buildVoxelGrid(100, 100, 100, 10);
    expect(zs.length).toBeGreaterThan(1);
    expect(zs[0]).toBe(5);
    expect(zs[zs.length - 1]).toBeGreaterThanOrEqual(95);
  });

  test('voxelOccupiedByTerrain marks only the z-layer containing terrain height', () => {
    expect(voxelOccupiedByTerrain(10, 5, 5)).toBe(true);
    expect(voxelOccupiedByTerrain(10, 25, 5)).toBe(false);
  });
});

describe('Building triangles at z > 0 produce upper-layer voxels', () => {
  test('voxelOccupiedByBuildings returns true for box at z=5..15 when triangle at z=10', () => {
    const boxMin = [0, 0, 5];
    const boxMax = [10, 10, 15];
    const buildingTriangles = [
      { a: [2, 2, 10], b: [8, 2, 10], c: [5, 8, 10] },
    ];
    expect(voxelOccupiedByBuildings(boxMin, boxMax, buildingTriangles)).toBe(true);
  });

  test('voxelOccupiedByBuildings returns true for multiple z-levels (building stack)', () => {
    const triangles = [
      { a: [5, 5, 10], b: [15, 5, 10], c: [10, 15, 10] },
      { a: [5, 5, 25], b: [15, 5, 25], c: [10, 15, 25] },
    ];
    expect(voxelOccupiedByBuildings([0, 0, 5], [20, 20, 15], triangles)).toBe(true);
    expect(voxelOccupiedByBuildings([0, 0, 20], [20, 20, 30], triangles)).toBe(true);
  });

  test('voxelOccupiedByBuildings returns false for box at z=0 when building only at z=20', () => {
    const buildingTriangles = [
      { a: [5, 5, 20], b: [15, 5, 20], c: [10, 15, 20] },
    ];
    expect(voxelOccupiedByBuildings([0, 0, 0], [20, 20, 10], buildingTriangles)).toBe(false);
  });
});

describe('Building triangles used in voxel occupancy', () => {
  test('voxelOccupiedByBuildings returns true when triangle intersects box', () => {
    const boxMin = [0, 0, 5];
    const boxMax = [10, 10, 15];
    const buildingTriangles = [
      { a: [2, 2, 10], b: [8, 2, 10], c: [5, 8, 10] },
    ];
    expect(voxelOccupiedByBuildings(boxMin, boxMax, buildingTriangles)).toBe(true);
  });

  test('voxelOccupiedByBuildings returns true when triangle vertex is inside box', () => {
    const boxMin = [0, 0, 0];
    const boxMax = [5, 5, 5];
    const buildingTriangles = [
      { a: [1, 1, 1], b: [20, 20, 20], c: [30, 30, 30] },
    ];
    expect(voxelOccupiedByBuildings(boxMin, boxMax, buildingTriangles)).toBe(true);
  });

  test('voxelOccupiedByBuildings returns false when triangle is far from box', () => {
    const boxMin = [0, 0, 0];
    const boxMax = [5, 5, 5];
    const buildingTriangles = [
      { a: [100, 100, 100], b: [105, 100, 100], c: [102, 108, 100] },
    ];
    expect(voxelOccupiedByBuildings(boxMin, boxMax, buildingTriangles)).toBe(false);
  });

  test('voxelOccupiedByBuildings returns false for empty triangle list', () => {
    expect(voxelOccupiedByBuildings([0, 0, 0], [10, 10, 10], [])).toBe(false);
  });
});

describe('Tile collection when root has no boundingVolume', () => {
  test('collectTilesInRegion still collects child tiles when root getTileRegion returns null', () => {
    const regionBox = [-87.63, 41.88, -87.62, 41.89, 0, 500];
    const basePath = 'https://tile.googleapis.com';
    const collected = [];
    const root = {
      boundingVolume: {},
      children: [
        {
          boundingVolume: {
            region: [-87.63 * (Math.PI / 180), 41.88 * (Math.PI / 180), -87.62 * (Math.PI / 180), 41.89 * (Math.PI / 180), 0, 200],
          },
          content: { uri: '/v1/3dtiles/tile0.b3dm' },
          children: [],
        },
      ],
    };
    collectTilesInRegion(root, basePath, regionBox, collected, 50);
    expect(collected.length).toBe(1);
    expect(collected[0].contentUrl).toContain('tile0.b3dm');
  });
});

describe('Google 3D Tiles constants', () => {
  test('GOOGLE_3D_TILES_ASSET_ID is 2275207', () => {
    expect(GOOGLE_3D_TILES_ASSET_ID).toBe(2275207);
  });

  test('GOOGLE_3DTILES_ROOT points to tile.googleapis.com', () => {
    expect(GOOGLE_3DTILES_ROOT).toContain('tile.googleapis.com');
    expect(GOOGLE_3DTILES_ROOT).toContain('root.json');
  });
});
