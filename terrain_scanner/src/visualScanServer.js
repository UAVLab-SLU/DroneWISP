/**
 * Local HTTP server for visual scan: serves the scan page and receives the 2D height map.
 * GET / → scan page, GET /params → scan params, POST /result → height map (resolves wait promise).
 */

const http = require('http');
const fs = require('fs');
const path = require('path');

const SCAN_PAGE_PATH = path.join(__dirname, '..', 'visual', 'scan-page.html');

function readBody(req) {
  return new Promise((resolve, reject) => {
    const chunks = [];
    req.on('data', (chunk) => chunks.push(chunk));
    req.on('end', () => resolve(Buffer.concat(chunks).toString('utf8')));
    req.on('error', reject);
  });
}

/**
 * Create and start the visual scan server.
 * @param {object} params - { originLon, originLat, groundHeight, rangeX, rangeY, stepSize, ionToken }
 * @returns {Promise<{ server: import('http').Server, url: string, resultPromise: Promise<object> }>}
 */
function startVisualScanServer(params) {
  let resolveResult;
  const resultPromise = new Promise((resolve) => {
    resolveResult = resolve;
  });

  const server = http.createServer(async (req, res) => {
    const url = req.url && req.url.split('?')[0];

    if (req.method === 'GET' && (url === '/' || url === '')) {
      try {
        const html = fs.readFileSync(SCAN_PAGE_PATH, 'utf8');
        res.writeHead(200, { 'Content-Type': 'text/html' });
        res.end(html);
      } catch (e) {
        res.writeHead(500, { 'Content-Type': 'text/plain' });
        res.end('Could not read scan page: ' + (e.message || e));
      }
      return;
    }

    if (req.method === 'GET' && url === '/params') {
      res.writeHead(200, { 'Content-Type': 'application/json' });
      res.end(JSON.stringify(params));
      return;
    }

    if (req.method === 'POST' && url === '/result') {
      let body;
      try {
        body = await readBody(req);
        const data = JSON.parse(body);
        resolveResult(data);
        res.writeHead(200, { 'Content-Type': 'application/json' });
        res.end(JSON.stringify({ ok: true }));
      } catch (e) {
        res.writeHead(400, { 'Content-Type': 'application/json' });
        res.end(JSON.stringify({ error: (e.message || String(e)) }));
      }
      return;
    }

    res.writeHead(404, { 'Content-Type': 'text/plain' });
    res.end('Not found');
  });

  return new Promise((resolve) => {
    server.listen(0, '127.0.0.1', () => {
      const port = server.address().port;
      const url = `http://127.0.0.1:${port}/`;
      resolve({ server, url, resultPromise });
    });
  });
}

module.exports = { startVisualScanServer };
