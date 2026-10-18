const test = require('node:test');
const assert = require('node:assert/strict');
const http = require('node:http');
const { once } = require('node:events');
const WebSocket = require('ws');

test('gateway forwards the submission WebSocket upgrade to Django', async () => {
  const backend = http.createServer((_request, response) => response.end());
  const upstream = new WebSocket.Server({ server: backend });
  upstream.on('connection', socket => socket.send(JSON.stringify({ status: 'FINISHED', verdict: 'AC' })));
  backend.listen(0, '127.0.0.1');
  await once(backend, 'listening');
  process.env.PORT = '0';
  process.env.DJANGO_BACKEND_HOST = '127.0.0.1';
  process.env.DJANGO_BACKEND_PORT = String(backend.address().port);
  const { server } = require('./server');
  if (!server.listening) await once(server, 'listening');
  const socket = new WebSocket(`ws://127.0.0.1:${server.address().port}/ws/submissions/42/`);
  try {
    const update = once(socket, 'message');
    await once(socket, 'open');
    assert.deepEqual(JSON.parse((await update)[0].toString()), { status: 'FINISHED', verdict: 'AC' });
  } finally {
    socket.terminate();
    for (const client of upstream.clients) client.terminate();
    await new Promise(resolve => upstream.close(resolve));
    await new Promise(resolve => server.close(resolve));
    await new Promise(resolve => backend.close(resolve));
  }
});
