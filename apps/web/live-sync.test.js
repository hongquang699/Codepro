const test = require('node:test');
const assert = require('node:assert/strict');
const http = require('node:http');
const { once } = require('node:events');
const WebSocket = require('ws');
const { createLiveSync, topicsForMutation } = require('./live-sync');

test('successful writes notify connected clients without exposing response data', async () => {
  const server = http.createServer((_req, res) => res.end('ok'));
  const hub = createLiveSync(server);
  server.listen(0, '127.0.0.1');
  await once(server, 'listening');
  const port = server.address().port;
  const client = new WebSocket(`ws://127.0.0.1:${port}/ws/live`);
  try {
    const ready = once(client, 'message');
    await once(client, 'open');
    assert.equal(JSON.parse((await ready)[0].toString()).type, 'ready');

    assert.deepEqual(topicsForMutation('POST', '/api/v2/submit', 201), ['submissions']);
    assert.deepEqual(topicsForMutation('PUT', '/api/v2/code-share/abc', 200), ['shares']);
    assert.deepEqual(topicsForMutation('PUT', '/api/v2/contest/ABC', 403), []);
    const update = once(client, 'message');
    hub.publish('PUT', '/api/v2/contest/ABC', 200);
    assert.deepEqual(JSON.parse((await update)[0].toString()), { type: 'invalidate', topics: ['contests'] });
  } finally {
    client.terminate();
    await new Promise(resolve => hub.wss.close(resolve));
    await new Promise(resolve => server.close(resolve));
  }
});
