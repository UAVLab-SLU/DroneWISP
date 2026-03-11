#!/usr/bin/env node
const { program } = require('commander');
const { scanTerrainToStl } = require('./scanner');

program
  .name('terrain-scanner')
  .description('Export Cesium World Terrain to STL. Origin (0,0,0) at lat/lon ground. Requires CESIUM_ION_ACCESS_TOKEN.')
  .requiredOption('--latitude <deg>', 'Center latitude (degrees)', parseFloat)
  .requiredOption('--longitude <deg>', 'Center longitude (degrees)', parseFloat)
  .option('--range-x <m>', 'Half-extent east (meters)', parseFloat, 100)
  .option('--range-y <m>', 'Half-extent north (meters)', parseFloat, 100)
  .option('--range-z <m>', 'Vertical extent above ground (meters)', parseFloat, 50)
  .option('--resolution <m>', 'Grid resolution (meters)', parseFloat, 5)
  .option('--step-size <m>', 'Step size in x/y (meters); same area, fewer cells when larger (e.g. 10 = 10x fewer cells than 1)', parseFloat)
  .option('--token-file <path>', 'Path to file containing Cesium Ion token for terrain (e.g. ./token)')
  .option('--google-api-key-file <path>', 'Path to file containing Google API key for 3D Tiles (e.g. ./google_api_key)')
  .option('--no-buildings', 'Skip Google 3D Tiles (terrain-only, flat output)')
  .requiredOption('--output <path>', 'Output STL file path')
  .action(async (opts) => {
    try {
      const result = await scanTerrainToStl({
        latitude: opts.latitude,
        longitude: opts.longitude,
        rangeX: opts.rangeX,
        rangeY: opts.rangeY,
        rangeZ: opts.rangeZ,
        resolution: opts.stepSize != null ? opts.stepSize : opts.resolution,
        output: opts.output,
        tokenFile: opts.tokenFile,
        googleApiKeyFile: opts.googleApiKeyFile,
        includeBuildings: opts.buildings !== false,
      });
      console.log('Ground height (m):', result.groundHeight);
      console.log('Triangles:', result.numTriangles);
      console.log('Written:', opts.output);
    } catch (e) {
      const msg = e && (e.message || (e.statusCode && `HTTP ${e.statusCode}`)) || String(e);
      console.error(msg);
      process.exit(1);
    }
  });

program.parse();
