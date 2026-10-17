const { WebSocketServer, WebSocket } = require('ws');

const LIVE_PATH = '/ws/live';
const MAX_CLIENTS = 1000;
const MAX_CLIENTS_PER_IP = 100;

function topicsForMutation(method, pathname, statusCode) {
  if (!['POST', 'PUT', 'PATCH', 'DELETE'].includes(method) || statusCode < 200 || statusCode >= 300) return [];
  if (!pathname.startsWith('/api/')) return [];
  const topics = new Set();
  if (/\bcontests?\b|contest-admin/.test(pathname)) topics.add('contests');
  if (/\bproblems?\b/.test(pathname)) topics.add('problems');
  if (/\bsubmissions?\b|\/submit\b|rejudge/.test(pathname)) topics.add('submissions');
  if (/\busers?\b|\/profile\b/.test(pathname)) topics.add('account');
  return [...topics];
}

function createLiveSync(server, getClientIp = request => request.socket.remoteAddress) {
  const wss = new WebSocketServer({ noServer: true, maxPayload: 1024, perMessageDeflate: false });
  const ipCounts = new Map();

  server.on('upgrade', (request, socket, head) => {
    let url;
    try { url = new URL(request.url, 'http://localhost'); } catch { socket.destroy(); return; }
    if (url.pathname !== LIVE_PATH || url.search) { socket.destroy(); return; }
    const origin = request.headers.origin;
    if (origin) {
      try {
        if (new URL(origin).host !== request.headers.host) { socket.destroy(); return; }
      } catch { socket.destroy(); return; }
    }
    const ip = getClientIp(request) || request.socket.remoteAddress;
    if (wss.clients.size >= MAX_CLIENTS || (ipCounts.get(ip) || 0) >= MAX_CLIENTS_PER_IP) { socket.destroy(); return; }
    wss.handleUpgrade(request, socket, head, ws => wss.emit('connection', ws, ip));
  });

  wss.on('connection', (ws, ip) => {
    ipCounts.set(ip, (ipCounts.get(ip) || 0) + 1);
    ws.on('close', () => {
      const count = (ipCounts.get(ip) || 1) - 1;
      if (count) ipCounts.set(ip, count); else ipCounts.delete(ip);
    });
    ws.isAlive = true;
    ws.on('pong', () => { ws.isAlive = true; });
    // The stream is read-only. Mutations must go through the authenticated API.
    ws.on('message', () => ws.close(1008, 'Read-only stream'));
    ws.send(JSON.stringify({ type: 'ready' }));
  });

  const heartbeat = setInterval(() => {
    for (const ws of wss.clients) {
      if (!ws.isAlive) { ws.terminate(); continue; }
      ws.isAlive = false;
      ws.ping();
    }
  }, 30000);
  heartbeat.unref();
  wss.on('close', () => clearInterval(heartbeat));

  function publish(method, pathname, statusCode) {
    const topics = topicsForMutation(method, pathname, statusCode);
    if (!topics.length) return;
    const message = JSON.stringify({ type: 'invalidate', topics });
    for (const ws of wss.clients) {
      if (ws.readyState === WebSocket.OPEN && ws.bufferedAmount < 65536) ws.send(message);
    }
  }

  return { wss, publish };
}

module.exports = { createLiveSync, topicsForMutation };
