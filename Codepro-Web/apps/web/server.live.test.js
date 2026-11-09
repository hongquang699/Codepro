const test = require('node:test');
const assert = require('node:assert/strict');
const http = require('node:http');
const { once } = require('node:events');
const WebSocket = require('ws');

test('gateway broadcasts a successful website API mutation to the desktop stream', async () => {
  const backend = http.createServer((request, response) => {
    request.resume();
    request.on('end', () => {
      response.writeHead(201, { 'Content-Type': 'application/json' });
      response.end('{"data":{"ok":true}}');
    });
  });
  backend.listen(0, '127.0.0.1');
  await once(backend, 'listening');
  process.env.PORT = '0';
  process.env.DJANGO_BACKEND_HOST = '127.0.0.1';
  process.env.DJANGO_BACKEND_PORT = String(backend.address().port);
  const { server } = require('./server');
  if (!server.listening) await once(server, 'listening');
  const port = server.address().port;
  const socket = new WebSocket(`ws://127.0.0.1:${port}/ws/live`);
  try {
    const ready = once(socket, 'message');
    await once(socket, 'open');
    await ready;
    const update = once(socket, 'message');
    const result = await fetch(`http://127.0.0.1:${port}/api/v2/problems`, {
      method: 'POST', headers: { 'Content-Type': 'application/json' }, body: '{}'
    });
    assert.equal(result.status, 201);
    assert.deepEqual(JSON.parse((await update)[0].toString()), { type: 'invalidate', topics: ['problems'] });
  } finally {
    socket.terminate();
    await new Promise(resolve => server.close(resolve));
    await new Promise(resolve => backend.close(resolve));
  }
});
