const { WebSocketServer } = require('ws');

let wss = null;

function initWebSocket(server) {
  wss = new WebSocketServer({ server });
  wss.on('connection', (ws) => {
    ws.on('message', (msg) => {
      // Handle client subscriptions
    });
  });
  console.log('[WEBSOCKET] Realtime server initialized');
}

function broadcastSubmissionUpdate(submissionId, data) {
  if (!wss) return;
  const payload = JSON.stringify({ type: 'SUBMISSION_UPDATE', submissionId, data });
  wss.clients.forEach(client => {
    if (client.readyState === 1) client.send(payload);
  });
}

module.exports = { initWebSocket, broadcastSubmissionUpdate };
