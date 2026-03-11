/**
 * Headless Cesium driver: run the scan page in Puppeteer to sample terrain + 3D Tiles
 * (same pipeline as SADE-GUI) and return top-surface height grid in meters (geodetic).
 */

const path = require('path');
const fs = require('fs');

/**
 * Run headless scan: launch browser, load Cesium + Google 3D Tiles, sample top height at each grid point.
 * @param {Object} options
 * @param {number} options.originLon - Center longitude (degrees)
 * @param {number} options.originLat - Center latitude (degrees)
 * @param {number} options.originHeight - Ground height at origin (m, WGS84)
 * @param {number} options.rangeX - Half extent east (m)
 * @param {number} options.rangeY - Half extent north (m)
 * @param {number} options.rangeZ - Height extent above ground (m)
 * @param {number} options.stepSize - Grid step (m)
 * @param {string} options.ionToken - Cesium Ion access token
 * @returns {Promise<{ occupiedGrid?: boolean[][][], xs?: number[], ys?: number[], zs?: number[], topHeightGrid?: number[][], error?: string }>}
 */
async function runHeadlessScan(options) {
  const {
    originLon,
    originLat,
    originHeight,
    rangeX,
    rangeY,
    rangeZ,
    stepSize,
    ionToken,
  } = options;

  let puppeteer;
  try {
    puppeteer = require('puppeteer');
  } catch (e) {
    return {
      topHeightGrid: [],
      xs: [],
      ys: [],
      error: 'puppeteer not installed. Run: npm install puppeteer',
    };
  }

  const scanPagePath = path.join(__dirname, '..', 'headless', 'scan-page.html');
  if (!fs.existsSync(scanPagePath)) {
    return {
      topHeightGrid: [],
      xs: [],
      ys: [],
      error: 'headless/scan-page.html not found',
    };
  }

  const fileUrl = 'file://' + path.resolve(scanPagePath);
  let browser;
  try {
    const headless = process.env.HEADLESS_VISIBLE !== '1' && process.env.HEADLESS_VISIBLE !== 'true';
    browser = await puppeteer.launch({
      headless,
      args: [
        '--no-sandbox',
        '--disable-setuid-sandbox',
        '--disable-dev-shm-usage',
        '--disable-web-security',
        '--disable-features=IsolateOrigins,site-per-process',
      ],
    });
    const page = await browser.newPage();
    await page.setViewport({ width: 1024, height: 1024 });
    await page.goto(fileUrl, { waitUntil: 'networkidle0', timeout: 30000 });

    const result = await page.evaluate(
      async (opts) => {
        if (typeof window.runHeadlessScan !== 'function') return { error: 'runHeadlessScan not defined' };
        try {
          return await window.runHeadlessScan(opts);
        } catch (err) {
          return { error: (err && err.message) || String(err) };
        }
      },
      {
        originLon,
        originLat,
        originHeight,
        rangeX,
        rangeY,
        rangeZ,
        stepSize,
        ionToken,
      }
    );

    await browser.close();

    if (result.error) {
      return {
        topHeightGrid: [],
        occupiedGrid: [],
        xs: result.xs || [],
        ys: result.ys || [],
        zs: result.zs || [],
        error: result.error,
      };
    }

    return {
      topHeightGrid: result.topHeightGrid || [],
      occupiedGrid: result.occupiedGrid || [],
      xs: result.xs || [],
      ys: result.ys || [],
      zs: result.zs || [],
    };
  } catch (err) {
    if (browser) await browser.close().catch(() => {});
    return {
      topHeightGrid: [],
      occupiedGrid: [],
      xs: [],
      ys: [],
      zs: [],
      error: (err && err.message) || String(err),
    };
  }
}

module.exports = { runHeadlessScan };
