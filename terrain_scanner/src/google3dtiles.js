/**
 * Fetch Google Photorealistic 3D Tiles (Cesium Ion asset 2275207) in a bounding
 * box and extract mesh triangles in local ENU (same coordinate system as terrain).
 * Uses the same asset as SADE-GUI. Requires Cesium Ion access token.
 */

const { Cartographic, Cartesian3, Transforms, Ellipsoid, Matrix4 } = require('cesium');
const { geodeticToLocalEnu } = require('./coordinates');

/** Transform point (x,y,z) by 4x4 column-major matrix (12 or 16 elements). Returns Cartesian3. */
function transformPointByMatrix(matrix, x, y, z) {
  if (!matrix || matrix.length < 12) return new Cartesian3(x, y, z);
  const m = matrix;
  const w = (m.length >= 16) ? (m[3] * x + m[7] * y + m[11] * z + (m[15] ?? 1)) : 1;
  const invW = w !== 0 ? 1 / w : 1;
  return new Cartesian3(
    (m[0] * x + m[4] * y + m[8] * z + (m[12] ?? 0)) * invW,
    (m[1] * x + m[5] * y + m[9] * z + (m[13] ?? 0)) * invW,
    (m[2] * x + m[6] * y + m[10] * z + (m[14] ?? 0)) * invW
  );
}

/** Expand 12-element (3 columns column-major) to 16-element 4x4 (last column 0,0,0,1). */
function expandTransformTo16(t) {
  if (!t || t.length < 12) return null;
  if (t.length >= 16) return t;
  return t.concat([0, 0, 0, 1]);
}

/** Multiply two 4x4 column-major matrices (12 or 16 elements). Returns 16-element array. */
function multiply4x4(A, B) {
  A = expandTransformTo16(A) || A;
  B = expandTransformTo16(B) || B;
  const out = new Array(16);
  for (let col = 0; col < 4; col++) {
    for (let row = 0; row < 4; row++) {
      let v = 0;
      for (let k = 0; k < 4; k++) v += (A[row + k * 4] ?? 0) * (B[k + col * 4] ?? 0);
      out[row + col * 4] = v;
    }
  }
  return out;
}

const GOOGLE_3D_TILES_ASSET_ID = 2275207;
const CESIUM_ION_ASSET_ENDPOINT = `https://api.cesium.com/v1/assets/${GOOGLE_3D_TILES_ASSET_ID}/endpoint`;
const GOOGLE_TILES_BASE = 'https://tile.googleapis.com';
const GOOGLE_3DTILES_ROOT = `${GOOGLE_TILES_BASE}/v1/3dtiles/root.json`;
const MAX_TILES_TO_LOAD = 50;
const DEG2RAD = Math.PI / 180;

/**
 * Fetch tileset URL and auth from Cesium Ion asset endpoint (bypasses loaders.gl
 * _getIonTilesetMetadata, which asserts type === '3DTILES' && url; Ion response
 * for this asset may use different shape).
 * @param {string} accessToken - Cesium Ion access token
 * @returns {Promise<{ url: string, headers: Record<string, string> }>}
 */
async function getGoogle3DTilesEndpoint(accessToken) {
  const response = await fetch(CESIUM_ION_ASSET_ENDPOINT, {
    headers: { Authorization: `Bearer ${accessToken}` },
  });
  if (!response.ok) {
    throw new Error(`Cesium Ion endpoint failed: ${response.status} ${response.statusText}`);
  }
  const data = await response.json();
  const opts = data.options && typeof data.options === 'object' ? data.options : {};
  const url = data.url ?? data.tilesetUrl ?? data.resource?.url ?? opts.url ?? opts.tilesetUrl ?? (typeof data.options === 'string' ? data.options : null);
  if (!url || typeof url !== 'string') {
    throw new Error('Cesium Ion endpoint did not return a tileset URL. Response keys: ' + Object.keys(data).join(', ') + (opts && Object.keys(opts).length ? '; options keys: ' + Object.keys(opts).join(', ') : ''));
  }
  return {
    url,
    headers: { Authorization: `Bearer ${accessToken}` },
  };
}

/**
 * Check if a 3D Tiles bounding region intersects our WGS84 box.
 * Region format: [west, south, east, north, minHeight, maxHeight] (radians, meters).
 */
function regionIntersectsBox(region, westDeg, southDeg, eastDeg, northDeg, minHeightM, maxHeightM) {
  if (!region || !Array.isArray(region) || region.length < 6) return false;
  const [w, s, e, n, minH, maxH] = region;
  const westRad = westDeg * DEG2RAD;
  const southRad = southDeg * DEG2RAD;
  const eastRad = eastDeg * DEG2RAD;
  const northRad = northDeg * DEG2RAD;
  if (e < westRad || w > eastRad || n < southRad || s > northRad) return false;
  if (maxH < minHeightM || minH > maxHeightM) return false;
  return true;
}

/**
 * Get bounding region from tile (region, box, or sphere).
 * Returns [west, south, east, north, minHeight, maxHeight] in radians/meters or null.
 */
function getTileRegion(tile) {
  const bv = tile && tile.boundingVolume;
  if (!bv) return null;
  if (bv.region && Array.isArray(bv.region) && bv.region.length >= 6) return bv.region;
  if (bv.box && Array.isArray(bv.box) && bv.box.length >= 12) {
    const b = bv.box;
    const cx = b[0], cy = b[1], cz = b[2];
    const x0 = b[3], x1 = b[4], x2 = b[5];
    const y0 = b[6], y1 = b[7], y2 = b[8];
    const z0 = b[9], z1 = b[10], z2 = b[11];
    let west = Infinity, south = Infinity, east = -Infinity, north = -Infinity;
    let minH = Infinity, maxH = -Infinity;
    const signs = [[1, 1, 1], [1, 1, -1], [1, -1, 1], [1, -1, -1], [-1, 1, 1], [-1, 1, -1], [-1, -1, 1], [-1, -1, -1]];
    for (const [sx, sy, sz] of signs) {
      const px = cx + sx * x0 + sy * y0 + sz * z0;
      const py = cy + sx * x1 + sy * y1 + sz * z1;
      const pz = cz + sx * x2 + sy * y2 + sz * z2;
      let carto;
      try {
        carto = Cartographic.fromCartesian(new Cartesian3(px, py, pz));
      } catch {
        continue;
      }
      if (typeof carto.longitude !== 'number') continue;
      west = Math.min(west, carto.longitude);
      south = Math.min(south, carto.latitude);
      east = Math.max(east, carto.longitude);
      north = Math.max(north, carto.latitude);
      minH = Math.min(minH, carto.height);
      maxH = Math.max(maxH, carto.height);
    }
    if (west === Infinity || minH === Infinity) return null;
    return [west, south, east, north, minH, maxH];
  }
  if (bv.sphere && Array.isArray(bv.sphere) && bv.sphere.length >= 4) {
    const [cx, cy, cz, r] = bv.sphere;
    let carto;
    try {
      carto = Cartographic.fromCartesian(new Cartesian3(cx, cy, cz));
    } catch {
      return null;
    }
    if (!carto || typeof carto.longitude !== 'number') return null;
    const west = carto.longitude - 0.001;
    const east = carto.longitude + 0.001;
    const south = carto.latitude - 0.001;
    const north = carto.latitude + 0.001;
    return [west, south, east, north, carto.height - r, carto.height + r];
  }
  return null;
}

/**
 * Build a 4x4 column-major ECEF transform for tile content.
 * Box is in tile local; tile.transform maps tile local to ECEF.
 * We transform the box center to ECEF and use ENU-at-that-point so that
 * glTF vertices (in local meters at the tile) map to correct ECEF and thus
 * to correct scan-origin local ENU.
 */
function boxToCartesianMatrix(box, tileTransform) {
  if (!box || box.length < 12) return null;
  const cx = box[0], cy = box[1], cz = box[2];
  const centerLocal = new Cartesian3(cx, cy, cz);
  const centerEcef = tileTransform
    ? transformPointByMatrix(tileTransform, cx, cy, cz)
    : centerLocal;
  const enuToFixed = Transforms.eastNorthUpToFixedFrame(centerEcef);
  return [
    enuToFixed[0], enuToFixed[1], enuToFixed[2], enuToFixed[3],
    enuToFixed[4], enuToFixed[5], enuToFixed[6], enuToFixed[7],
    enuToFixed[8], enuToFixed[9], enuToFixed[10], enuToFixed[11],
    enuToFixed[12], enuToFixed[13], enuToFixed[14], enuToFixed[15],
  ];
}

/**
 * Resolve content URL for a tile (basePath + content.uri).
 */
function getContentUrl(tile, basePath) {
  const content = tile && tile.content;
  const uri = (content && (content.uri || content.url)) || '';
  if (!uri) return null;
  if (uri.startsWith('http://') || uri.startsWith('https://')) return uri;
  if (uri.startsWith('/')) {
    try {
      return new URL(basePath).origin + uri;
    } catch {
      return basePath.replace(/\/?$/, '') + uri;
    }
  }
  const base = basePath.replace(/\/?$/, '');
  return base + '/' + uri;
}

/**
 * Extract triangles from B3DM content: glTF positions + indices, transform to ECEF, then to local ENU.
 */
function extractTrianglesFromContent(content, originLon, originLat, originHeightM) {
  const triangles = [];
  const gltf = content && content.gltf;
  if (!gltf) return triangles;
  const gltfJson = gltf.json || gltf;
  const meshes = gltfJson.meshes || gltf.meshes || [];
  const accessors = gltfJson.accessors || gltf.accessors || [];
  if (process.env.DEBUG_3DTILES && meshes.length > 0) {
    const m0 = meshes[0];
    console.warn('DEBUG extract: meshes', meshes.length, 'accessors', accessors.length, 'first mesh primitives', m0.primitives?.length, 'getTypedArray', typeof gltf.getTypedArrayForAccessor);
  }
  if (!meshes.length || !accessors.length) return triangles;

  /* RTC center from glTF (ECEF) or content; do not use content.rtcCenter if we overwrote it. */
  const rtcFromGltf = gltfJson.extensions && gltfJson.extensions.CESIUM_RTC && gltfJson.extensions.CESIUM_RTC.center;
  const rtcCenter = (Array.isArray(rtcFromGltf) && rtcFromGltf.length >= 3)
    ? rtcFromGltf
    : (content.rtcCenter && Array.isArray(content.rtcCenter) && content.rtcCenter.length >= 3)
      ? content.rtcCenter
      : [0, 0, 0];
  const rtcMag = Math.sqrt(
    (rtcCenter[0] || 0) ** 2 + (rtcCenter[1] || 0) ** 2 + (rtcCenter[2] || 0) ** 2
  );
  const rtcIsEcef = rtcMag >= 1e6 && rtcMag <= 1e8;

  let matrix = content.cartesianModelMatrix;

  /* Per 3D Tiles / CESIUM_RTC: ECEF = center_ECEF + local_vertex. When center is in ECEF, use that directly. */
  const transformPoint = (x, y, z) => {
    if (rtcIsEcef) {
      return new Cartesian3(
        (rtcCenter[0] || 0) + x,
        (rtcCenter[1] || 0) + y,
        (rtcCenter[2] || 0) + z
      );
    }
    if (!matrix) return new Cartesian3(x, y, z);
    const vx = x;
    const vy = y;
    const vz = z;
    if (matrix && typeof matrix.transformPoint === 'function') {
      const out = matrix.transformPoint([vx, vy, vz]);
      return Cartesian3.fromArray(out);
    }
    if (matrix && Array.isArray(matrix) && matrix.length >= 16) {
      const m = Matrix4.fromColumnMajorArray(matrix);
      const point = new Cartesian3(vx, vy, vz);
      return Matrix4.multiplyByPoint(m, point, new Cartesian3());
    }
    if (matrix && Array.isArray(matrix) && matrix.length >= 12) {
      const m = matrix;
      const w = (m[3] || 0) * vx + (m[7] || 0) * vy + (m[11] || 0) * vz + 1;
      const invW = w !== 0 ? 1 / w : 1;
      return new Cartesian3(
        ((m[0] || 0) * vx + (m[4] || 0) * vy + (m[8] || 0) * vz + (m[12] || 0)) * invW,
        ((m[1] || 0) * vx + (m[5] || 0) * vy + (m[9] || 0) * vz + (m[13] || 0)) * invW,
        ((m[2] || 0) * vx + (m[6] || 0) * vy + (m[10] || 0) * vz + (m[14] || 0)) * invW
      );
    }
    return new Cartesian3(vx, vy, vz);
  };

  if (!rtcIsEcef && !matrix) return triangles;

  const ecefToLocal = (cartesian) => {
    let carto;
    try {
      carto = Cartographic.fromCartesian(cartesian);
    } catch {
      return [NaN, NaN, NaN];
    }
    if (!carto || typeof carto.longitude !== 'number') return [NaN, NaN, NaN];
    const lonDeg = carto.longitude * (180 / Math.PI);
    const latDeg = carto.latitude * (180 / Math.PI);
    const local = geodeticToLocalEnu(originLon, originLat, originHeightM, lonDeg, latDeg, carto.height);
    return [local.x, local.y, local.z];
  };

  for (const mesh of meshes) {
    if (!mesh.primitives) continue;
    for (const prim of mesh.primitives) {
      const posRef = prim.attributes && (prim.attributes.POSITION ?? prim.attributes.POSITION_0);
      const posAcc = posRef != null ? (typeof posRef === 'object' && (posRef.bufferView != null || posRef.value != null) ? posRef : accessors[posRef]) : null;
      const indRef = prim.indices;
      const indAcc = indRef != null ? (typeof indRef === 'object' && (indRef.bufferView != null || indRef.value != null) ? indRef : accessors[indRef]) : null;
      const positions = posAcc && (posAcc.value || (typeof gltf.getTypedArrayForAccessor === 'function' && gltf.getTypedArrayForAccessor(posAcc)));
      if (!posAcc || !positions) continue;
      const compsFromType = { SCALAR: 1, VEC2: 2, VEC3: 3, VEC4: 4 };
      const comps = posAcc.components || compsFromType[posAcc.type] || 3;
      const count = posAcc.count ?? (positions.length / comps);

      let indices = null;
      if (indAcc) indices = indAcc.value || (typeof gltf.getTypedArrayForAccessor === 'function' && gltf.getTypedArrayForAccessor(indAcc));

      const getVertex = (i) => {
        const j = i * comps;
        const x = positions[j];
        const y = positions[j + 1];
        const z = comps >= 3 ? positions[j + 2] : 0;
        const ecef = transformPoint(x, y, z);
        return ecefToLocal(ecef);
      };

      if (indices) {
        for (let k = 0; k + 2 < indices.length; k += 3) {
          const i0 = indices[k];
          const i1 = indices[k + 1];
          const i2 = indices[k + 2];
          if (i0 >= count || i1 >= count || i2 >= count) continue;
          const a = getVertex(i0);
          const b = getVertex(i1);
          const c = getVertex(i2);
          if (a.every(Number.isFinite) && b.every(Number.isFinite) && c.every(Number.isFinite)) {
            triangles.push({ a, b, c });
          }
        }
      } else {
        for (let i = 0; i + 2 < count; i += 3) {
          const a = getVertex(i);
          const b = getVertex(i + 1);
          const c = getVertex(i + 2);
          if (a.every(Number.isFinite) && b.every(Number.isFinite) && c.every(Number.isFinite)) {
            triangles.push({ a, b, c });
          }
        }
      }
    }
  }
  return triangles;
}

/**
 * Recursively collect tiles that intersect the region (depth-first, up to maxTiles).
 */
function collectTilesInRegion(tile, basePath, regionBox, collected, maxTiles) {
  if (collected.length >= maxTiles) return;
  const tileRegion = getTileRegion(tile);
  const intersects = !tileRegion || regionIntersectsBox(tileRegion, ...regionBox);
  const contentUrl = getContentUrl(tile, basePath);
  if (process.env.DEBUG_3DTILES && contentUrl) {
    console.warn('DEBUG: tile has content, intersects=', intersects, 'tileRegion=', tileRegion ? 'ok' : 'null');
  }
  if (intersects && contentUrl) collected.push({ tile, contentUrl, basePath });

  const children = tile.children || [];
  for (const child of children) {
    collectTilesInRegion(child, basePath, regionBox, collected, maxTiles);
    if (collected.length >= maxTiles) return;
  }
}

/**
 * Fetch Google Photorealistic 3D Tiles in the given bounding box and return triangles in local ENU.
 * Uses Cesium Ion asset 2275207 (Google Photorealistic 3D Tiles).
 *
 * @param {Object} options
 * @param {number} options.originLon - Center longitude (degrees)
 * @param {number} options.originLat - Center latitude (degrees)
 * @param {number} options.originHeightM - Ground height at origin (m)
 * @param {number} options.rangeX - Half extent east (m)
 * @param {number} options.rangeY - Half extent north (m)
 * @param {string} [options.googleApiKey] - Google Map Tiles API key (preferred for Photorealistic 3D Tiles)
 * @param {string} [options.accessToken] - Cesium Ion access token (fallback when no Google API key)
 * @returns {Promise<Array<{ a: [number,number,number], b: [number,number,number], c: [number,number,number] }>>}
 */
async function fetchGoogle3DTilesInBbox(options) {
  const { originLon, originLat, originHeightM, rangeX, rangeY, googleApiKey, accessToken } = options;
  if (!googleApiKey && !accessToken) {
    throw new Error('Google 3D Tiles require a Google API key (--google-api-key-file) or Cesium Ion token (--token-file).');
  }

  const { load } = await import('@loaders.gl/core');
  const { Tiles3DLoader } = await import('@loaders.gl/3d-tiles');

  const METERS_PER_DEG_LAT = 111320;
  const latRad = (originLat * Math.PI) / 180;
  const metersPerDegLon = METERS_PER_DEG_LAT * Math.cos(latRad);
  const southDeg = originLat - rangeY / METERS_PER_DEG_LAT;
  const northDeg = originLat + rangeY / METERS_PER_DEG_LAT;
  const westDeg = originLon - rangeX / metersPerDegLon;
  const eastDeg = originLon + rangeX / metersPerDegLon;
  const regionBox = [westDeg, southDeg, eastDeg, northDeg, 0, 500];

  let tilesetUrl;
  let tilesetData;
  let customFetch;
  let basePath;

  if (googleApiKey) {
    tilesetUrl = GOOGLE_3DTILES_ROOT + '?key=' + encodeURIComponent(googleApiKey);
    const rootRes = await fetch(tilesetUrl);
    if (!rootRes.ok) {
      throw new Error(`Google 3D Tiles root failed: ${rootRes.status} ${rootRes.statusText}`);
    }
    tilesetData = await rootRes.json();
    const session = tilesetData.session ?? tilesetData.sessionToken ?? null;

    const appendGoogleAuth = (urlStr) => {
      if (!urlStr) return urlStr;
      try {
        const absolute = urlStr.startsWith('http') ? urlStr : (GOOGLE_TILES_BASE + (urlStr.startsWith('/') ? '' : '/') + urlStr);
        const u = new URL(absolute);
        u.searchParams.set('key', googleApiKey);
        if (session) u.searchParams.set('session', session);
        return u.toString();
      } catch {
        const sep = urlStr.includes('?') ? '&' : '?';
        const extra = 'key=' + encodeURIComponent(googleApiKey) + (session ? '&session=' + encodeURIComponent(session) : '');
        return (urlStr.startsWith('http') ? urlStr : GOOGLE_TILES_BASE + (urlStr.startsWith('/') ? '' : '/') + urlStr) + sep + extra;
      }
    };

    customFetch = (input, init = {}) => {
      const url = typeof input === 'string' ? input : (input && input.url);
      return fetch(appendGoogleAuth(url), init);
    };
    basePath = tilesetData.basePath || tilesetUrl.replace(/\?.*$/, '').replace(/\/[^/]*$/, '');
  } else {
    const { url: urlFromIon, headers } = await getGoogle3DTilesEndpoint(accessToken);
    tilesetUrl = urlFromIon;

    const appendToken = (urlStr) => {
      if (!urlStr || !accessToken) return urlStr;
      try {
        const u = new URL(urlStr);
        u.searchParams.set('access_token', accessToken);
        return u.toString();
      } catch {
        return urlStr + (urlStr.includes('?') ? '&' : '?') + 'access_token=' + encodeURIComponent(accessToken);
      }
    };

    customFetch = (input, init = {}) => {
      const url = typeof input === 'string' ? input : (input && input.url);
      return fetch(appendToken(url), { ...init, headers: { ...(init.headers || {}), ...headers } });
    };

    const tilesetRes = await customFetch(tilesetUrl);
    if (!tilesetRes.ok) {
      throw new Error(`Tileset fetch failed: ${tilesetRes.status} ${tilesetRes.statusText}`);
    }
    tilesetData = await tilesetRes.json();
    basePath = tilesetData.basePath || tilesetUrl.replace(/\/[^/]*$/, '');
  }

  const root = tilesetData.root || tilesetData;
  const rootTransformToEcef = (root && root.transform && Array.isArray(root.transform) && root.transform.length >= 12) ? root.transform : null;
  const toCollect = [];
  collectTilesInRegion(root, basePath, regionBox, toCollect, MAX_TILES_TO_LOAD);

  if (process.env.DEBUG_3DTILES) {
    console.warn('DEBUG: collected tiles:', toCollect.length, 'basePath:', basePath, 'rootTransform:', !!rootTransformToEcef);
  }
  if (toCollect.length === 0 && process.env.DEBUG_3DTILES) {
    const children = root && root.children || [];
    const c0 = children[0];
    if (c0) {
      const bv = c0.boundingVolume || {};
      console.warn('DEBUG: child0 boundingVolume keys:', Object.keys(bv), 'children:', (c0.children && c0.children.length) || 0, 'content:', c0.content ? (c0.content.uri || c0.content.url || 'empty') : 'none');
      if (c0.children && c0.children[0]) {
        const g = c0.children[0];
        const gv = g.boundingVolume || {};
        console.warn('DEBUG: grandchild0 boundingVolume keys:', Object.keys(gv), 'content:', g.content ? (g.content.uri || g.content.url || 'empty') : 'none');
      }
    }
    console.warn('DEBUG: toCollect.length:', toCollect.length);
  }

  const allTriangles = [];
  const contentQueue = toCollect.map(({ contentUrl, tile }) => ({ contentUrl, tile, parentTransformToEcef: rootTransformToEcef }));
  const seenUrls = new Set(contentQueue.map(({ contentUrl }) => contentUrl));
  let idx = 0;
  while (idx < contentQueue.length) {
    const { contentUrl, tile, parentTransformToEcef } = contentQueue[idx++];
    if (process.env.DEBUG_3DTILES) console.warn('DEBUG: fetch', idx, contentUrl.slice(0, 90));
    try {
      const response = await customFetch(contentUrl);
      let arrayBuffer = await (response.arrayBuffer ? response.arrayBuffer() : response);
      while (arrayBuffer && typeof arrayBuffer.then === 'function') arrayBuffer = await arrayBuffer;
      if (!(arrayBuffer instanceof ArrayBuffer) && arrayBuffer && arrayBuffer.byteLength !== undefined) {
        try {
          const u8 = new Uint8Array(arrayBuffer);
          arrayBuffer = u8.buffer.slice(u8.byteOffset, u8.byteOffset + u8.byteLength);
        } catch (e) {
          if (process.env.DEBUG_3DTILES) console.warn('DEBUG: buffer copy failed', e.message);
          continue;
        }
      }
      if (!(arrayBuffer instanceof ArrayBuffer)) {
        if (process.env.DEBUG_3DTILES) console.warn('DEBUG: response not ArrayBuffer', typeof arrayBuffer, arrayBuffer?.constructor?.name);
        continue;
      }
      const contentType = response.headers && response.headers.get ? response.headers.get('content-type') : '';
      const isJson = contentType.includes('application/json') ||
        (arrayBuffer.byteLength >= 2 && new Uint8Array(arrayBuffer)[0] === 0x7b);
      if (process.env.DEBUG_3DTILES) console.warn('DEBUG: len', arrayBuffer.byteLength, 'isJson', isJson, 'content-type', contentType.slice(0, 40));
      if (isJson) {
        const text = new TextDecoder().decode(arrayBuffer);
        const subtree = JSON.parse(text);
        const subRoot = subtree.root || subtree;
        const subBase = contentUrl.replace(/\?.*$/, '').replace(/\/[^/]*$/, '/');
        let parentTransformToEcef = tile && tile.transform ? tile.transform : null;
        if (subRoot && subRoot.transform) {
          parentTransformToEcef = parentTransformToEcef
            ? multiply4x4(parentTransformToEcef, subRoot.transform)
            : subRoot.transform;
        }
        const subCollected = [];
        collectTilesInRegion(subRoot, subBase, regionBox, subCollected, Math.max(0, MAX_TILES_TO_LOAD - contentQueue.length + 1));
        if (process.env.DEBUG_3DTILES) {
          console.warn('DEBUG: subtree from', contentUrl.slice(0, 70), '->', subCollected.length, 'tiles');
        }
        for (const { contentUrl: subUrl, tile: subTile } of subCollected) {
          if (!seenUrls.has(subUrl)) {
            seenUrls.add(subUrl);
            contentQueue.push({ contentUrl: subUrl, tile: subTile, parentTransformToEcef: parentTransformToEcef });
          }
        }
        continue;
      }
      const content = await load(contentUrl, Tiles3DLoader, {
        '3d-tiles': { isTileset: false, loadGLTF: true },
        gltf: { loadImages: false },
        fetch: customFetch,
      });
      if (!content || !content.gltf) {
        if (process.env.DEBUG_3DTILES) console.warn('DEBUG: tile no gltf', contentUrl.slice(0, 80));
        continue;
      }
      /* Build tile-to-ECEF from tile hierarchy. Avoid multiplying when parent === tile.transform (root tile case, would square the matrix). */
      const parentExp = parentTransformToEcef && Array.isArray(parentTransformToEcef) && parentTransformToEcef.length >= 12;
      const tileExp = tile.transform && Array.isArray(tile.transform) && tile.transform.length >= 12;
      const sameRef = parentTransformToEcef && tile.transform && parentTransformToEcef === tile.transform;
      let tileToEcef = null;
      if (tileExp && parentExp && !sameRef) {
        tileToEcef = multiply4x4(parentTransformToEcef, tile.transform);
      } else if (parentExp) {
        tileToEcef = expandTransformTo16(parentTransformToEcef);
      } else if (tileExp) {
        tileToEcef = expandTransformTo16(tile.transform);
      }
      if (tileToEcef && tileToEcef.length >= 16) {
        content.cartesianModelMatrix = tileToEcef;
        content.rtcCenter = [0, 0, 0];
      } else {
        let centerEcef = null;
        const bv = tile?.boundingVolume;
        if (bv?.region && Array.isArray(bv.region) && bv.region.length >= 6) {
          const [west, south, east, north, minH, maxH] = bv.region;
          const centerLon = (west + east) * 0.5;
          const centerLat = (south + north) * 0.5;
          const centerHeight = (minH + maxH) * 0.5;
          const carto = new Cartographic(centerLon, centerLat, centerHeight);
          centerEcef = Ellipsoid.WGS84.cartographicToCartesian(carto);
        }
        if (!centerEcef) {
          const rtc = content.rtcCenter || content.gltf?.json?.extensions?.CESIUM_RTC?.center;
          if (rtc && Array.isArray(rtc) && rtc.length >= 3) {
            const rtcMagnitude = Math.sqrt(rtc[0] * rtc[0] + rtc[1] * rtc[1] + rtc[2] * rtc[2]);
            const earthRadiusM = 6.371e6;
            const clearlyEcef = rtcMagnitude >= earthRadiusM * 0.95 && rtcMagnitude <= earthRadiusM * 1.05;
            if (clearlyEcef) {
              centerEcef = new Cartesian3(rtc[0], rtc[1], rtc[2]);
            } else if (tileToEcef && tileToEcef.length >= 12) {
              centerEcef = transformPointByMatrix(tileToEcef, rtc[0], rtc[1], rtc[2]);
            } else {
              centerEcef = new Cartesian3(rtc[0], rtc[1], rtc[2]);
            }
          }
        }
        if (!centerEcef && tile?.boundingVolume?.box) {
          const box = tile.boundingVolume.box;
          centerEcef = (tileToEcef && tileToEcef.length >= 12)
            ? transformPointByMatrix(tileToEcef, box[0], box[1], box[2])
            : new Cartesian3(box[0], box[1], box[2]);
        }
        if (centerEcef) {
          const enuToFixed = Transforms.eastNorthUpToFixedFrame(centerEcef);
          content.cartesianModelMatrix = [
            enuToFixed[0], enuToFixed[1], enuToFixed[2], enuToFixed[3],
            enuToFixed[4], enuToFixed[5], enuToFixed[6], enuToFixed[7],
            enuToFixed[8], enuToFixed[9], enuToFixed[10], enuToFixed[11],
            enuToFixed[12], enuToFixed[13], enuToFixed[14], enuToFixed[15],
          ];
          content.rtcCenter = [0, 0, 0];
        }
      }
      if (!content.cartesianModelMatrix) {
        if (process.env.DEBUG_3DTILES) console.warn('DEBUG: tile no cartesianModelMatrix', contentUrl.slice(0, 80));
        continue;
      }
      const tris = extractTrianglesFromContent(content, originLon, originLat, originHeightM);
      if (process.env.DEBUG_3DTILES) console.warn('DEBUG: tile gltf+matrix ->', tris.length, 'triangles');
      allTriangles.push(...tris);
    } catch (err) {
      console.warn('Skip tile', contentUrl.slice(0, 80), err.message);
    }
  }

  const maxZ = options.rangeZ != null ? options.rangeZ : 500;
  const inBox = (p) =>
    p[0] >= -rangeX && p[0] <= rangeX &&
    p[1] >= -rangeY && p[1] <= rangeY &&
    p[2] >= 0 && p[2] <= maxZ;
  const filtered = allTriangles.filter(({ a, b, c }) =>
    inBox(a) || inBox(b) || inBox(c));
  if (allTriangles.length > 0 && filtered.length === 0) {
    let minX = Infinity, maxX = -Infinity, minY = Infinity, maxY = -Infinity, minZ = Infinity, maxZ_ = -Infinity;
    for (const { a, b, c } of allTriangles) {
      for (const p of [a, b, c]) {
        minX = Math.min(minX, p[0]); maxX = Math.max(maxX, p[0]);
        minY = Math.min(minY, p[1]); maxY = Math.max(maxY, p[1]);
        minZ = Math.min(minZ, p[2]); maxZ_ = Math.max(maxZ_, p[2]);
      }
    }
    console.warn('Buildings: all', allTriangles.length, 'triangles outside scan box; local range x', minX.toFixed(0), '..', maxX.toFixed(0), 'y', minY.toFixed(0), '..', maxY.toFixed(0), 'z', minZ.toFixed(0), '..', maxZ_.toFixed(0), '(scan box x ±' + rangeX + ' y ±' + rangeY + ' z 0..' + maxZ + ')');
  }
  return filtered;
}

module.exports = {
  fetchGoogle3DTilesInBbox,
  GOOGLE_3D_TILES_ASSET_ID,
  regionIntersectsBox,
  getTileRegion,
  getContentUrl,
  collectTilesInRegion,
  GOOGLE_3DTILES_ROOT,
};
