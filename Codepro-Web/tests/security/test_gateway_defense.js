const assert = require('node:assert/strict');
const http = require('node:http');
const { securityDefense } = require('../../apps/web/security');

function request(port, path, headers = {}) {
  return new Promise((resolve, reject) => {
    const req = http.request({ hostname: '127.0.0.1', port, path, headers }, res => {
      res.resume();
      res.on('end', () => resolve(res.statusCode));
    });
    req.on('error', reject);
    req.end();
  });
}

async function main() {
  const ip = '198.51.100.213';
  for (let attempt = 0; attempt < 5; attempt++) {
    const result = securityDefense.inspect({
      socket: { remoteAddress: '127.0.0.1' },
      headers: { 'x-forwarded-for': ip, 'user-agent': 'test-client' },
      method: 'POST',
      url: '/api/v1/auth/login'
    });
    assert.equal(result.allowed, true);
  }
  const blocked = securityDefense.inspect({
    socket: { remoteAddress: '127.0.0.1' },
    headers: { 'x-forwarded-for': ip, 'user-agent': 'test-client' },
    method: 'POST',
    url: '/api/v1/auth/login'
  });
  assert.equal(blocked.status, 429);

  process.env.PORT = '0';
  process.env.DJANGO_BACKEND_PORT = '9';
  const { server } = require('../../apps/web/server');
  await new Promise(resolve => server.once('listening', resolve));
  try {
    const port = server.address().port;
    assert.equal(await request(port, '/frontend/css/global/theme.css', {
      'x-forwarded-for': '198.51.100.214', accept: 'text/css'
    }), 200);
    assert.equal(await request(port, '/backend/core/settings.py', {
      'x-forwarded-for': '198.51.100.215', accept: 'text/html'
    }), 403);
    assert.equal(await request(port, '/api/v1/auth/login', {
      'x-forwarded-for': '198.51.100.216',
      'content-length': String(2 * 1024 * 1024 + 1)
    }), 413);
  } finally {
    await new Promise(resolve => server.close(resolve));
  }
}

main().catch(error => { console.error(error); process.exitCode = 1; });
