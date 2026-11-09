/**
 * Web Server & Static File Security Unit Test
 * Verifies that sensitive files cannot be resolved or served.
 */

const assert = require('assert');
const fs = require('fs');
const path = require('path');

const ROOT_DIR = path.resolve(__dirname, '../..');
const FRONTEND_DIR = path.resolve(ROOT_DIR, 'frontend');
const ALLOWED_ROOT_FILES = new Set(['/favicon.ico', '/robots.txt']);

const MIME_TYPES = {
  '.html': 'text/html; charset=utf-8',
  '.css': 'text/css; charset=utf-8',
  '.js': 'application/javascript; charset=utf-8',
  '.json': 'application/json; charset=utf-8',
  '.svg': 'image/svg+xml',
  '.png': 'image/png',
  '.jpg': 'image/jpeg',
  '.ico': 'image/x-icon',
  '.woff': 'font/woff',
  '.woff2': 'font/woff2',
  '.ttf': 'font/ttf'
};

const FORBIDDEN_EXTENSIONS = [
  '.map', '.env', '.py', '.pyc', '.pyo', '.sqlite3', '.db', '.sql', '.bak', '.log',
  '.sh', '.bash', '.yml', '.yaml', '.toml', '.ini', '.conf', '.md', '.txt'
];

function isSafeStaticPath(reqUrl) {
  // 1. Path traversal check
  if (reqUrl.includes('\0') || reqUrl.includes('..') || /[\/\\]\./.test(reqUrl)) {
    return { allowed: false, reason: 'PATH_TRAVERSAL' };
  }

  const lowerUrlPath = reqUrl.toLowerCase();

  // 2. Forbidden extension check
  if (FORBIDDEN_EXTENSIONS.some(ext => lowerUrlPath.endsWith(ext)) && !ALLOWED_ROOT_FILES.has(lowerUrlPath)) {
    return { allowed: false, reason: 'FORBIDDEN_EXTENSION' };
  }

  // 3. Allowed mime check
  const ext = path.extname(reqUrl).toLowerCase();
  if (ext && !MIME_TYPES[ext]) {
    return { allowed: false, reason: 'DISALLOWED_MIME' };
  }

  // 4. Candidate path jail check
  // The web server only checks FRONTEND_DIR and ALLOWED_ROOT_FILES
  let targetFile = null;
  if (ALLOWED_ROOT_FILES.has(lowerUrlPath)) {
    targetFile = path.join(ROOT_DIR, lowerUrlPath.slice(1));
  } else {
    const cleanReq = reqUrl.startsWith('/frontend/')
      ? reqUrl.substring('/frontend/'.length)
      : reqUrl.replace(/^\/+/, '');
    targetFile = path.join(FRONTEND_DIR, cleanReq);
  }

  const resolved = path.resolve(targetFile);
  const isAllowedRoot = ALLOWED_ROOT_FILES.has(lowerUrlPath) && resolved === path.resolve(ROOT_DIR, lowerUrlPath.slice(1));
  const isInsideFrontend = resolved.startsWith(FRONTEND_DIR + path.sep);

  if (!isAllowedRoot && !isInsideFrontend) {
    return { allowed: false, reason: 'OUTSIDE_FRONTEND_JAIL' };
  }

  // Also verify that root-level sensitive files cannot be resolved from FRONTEND_DIR
  if (!fs.existsSync(resolved)) {
    return { allowed: false, reason: 'NOT_FOUND_IN_JAIL' };
  }

  return { allowed: true, resolved };
}

console.log('=' .repeat(60));
console.log('RUNNING WEB GATEWAY STATIC FILE LEAK PREVENTION TESTS');
console.log('=' .repeat(60));

const tests = [
  { url: '/.env', expectAllowed: false, name: 'Block root .env file' },
  { url: '/.env.production', expectAllowed: false, name: 'Block .env variants' },
  { url: '/manage.py', expectAllowed: false, name: 'Block manage.py backend entrypoint' },
  { url: '/backend/core/settings.py', expectAllowed: false, name: 'Block Django settings.py' },
  { url: '/database/vnoi_db.sqlite3', expectAllowed: false, name: 'Block SQLite database file' },
  { url: '/package.json', expectAllowed: false, name: 'Block package.json at root' },
  { url: '/judge-system/judge-server/main.py', expectAllowed: false, name: 'Block Judge server code' },
  { url: '/storage/testcases/01.out', expectAllowed: false, name: 'Block competition secret testcases' },
  { url: '/frontend/../backend/core/settings.py', expectAllowed: false, name: 'Block path traversal ../' },
  { url: '/frontend/html/home/index.html', expectAllowed: true, name: 'Allow valid frontend HTML' },
  { url: '/frontend/css/global/theme.css', expectAllowed: true, name: 'Allow valid frontend CSS' },
  { url: '/frontend/js/core/theme.js', expectAllowed: true, name: 'Allow valid frontend JS' },
  { url: '/frontend/js/core/theme.js.map', expectAllowed: false, name: 'Block sourcemaps (.map)' },
  { url: '/favicon.ico', expectAllowed: true, name: 'Allow favicon.ico' },
];

let passed = 0;
for (const t of tests) {
  const res = isSafeStaticPath(t.url);
  try {
    assert.strictEqual(res.allowed, t.expectAllowed, `Failed test: ${t.name} for URL ${t.url}`);
    console.log(`[PASS] ${t.name} -> ${res.allowed ? 'ALLOWED' : 'BLOCKED (' + res.reason + ')'}`);
    passed++;
  } catch (err) {
    console.error(`[FAIL] ${t.name}:`, err.message);
  }
}

console.log('='.repeat(60));
console.log(`Summary: ${passed}/${tests.length} tests passed successfully.`);
console.log('='.repeat(60));
if (passed !== tests.length) process.exit(1);
