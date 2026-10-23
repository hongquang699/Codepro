const test = require('node:test');
const assert = require('node:assert/strict');
const { once } = require('node:events');

test('static assets revalidate while HTML remains uncached', async () => {
  process.env.PORT = '0';
  const { server } = require('./server');
  if (!server.listening) await once(server, 'listening');
  const base = `http://127.0.0.1:${server.address().port}`;
  try {
    const asset = await fetch(`${base}/frontend/css/global/theme.css`);
    assert.equal(asset.status, 200);
    assert.equal(asset.headers.get('cache-control'), 'no-cache');
    const etag = asset.headers.get('etag');
    assert.ok(etag);
    await asset.arrayBuffer();

    const repeat = await fetch(`${base}/frontend/css/global/theme.css`, {
      headers: { 'If-None-Match': etag }
    });
    assert.equal(repeat.status, 304);
    assert.equal(await repeat.text(), '');

    const page = await fetch(`${base}/`);
    assert.equal(page.status, 200);
    assert.match(page.headers.get('cache-control'), /no-store/);
    assert.equal(page.headers.get('etag'), null);
  } finally {
    await new Promise(resolve => server.close(resolve));
  }
});
