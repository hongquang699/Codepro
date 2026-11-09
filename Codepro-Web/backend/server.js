const http = require('http');
const app = require('./app');
const { initWebSocket } = require('./core/websocket');

const PORT = process.env.PORT || 4000;
const server = http.createServer(app);

// Initialize WebSocket for Real-time Submissions & Scoreboard
initWebSocket(server);

server.listen(PORT, () => {
  console.log(`[ONLINE JUDGE] Backend Server is active at http://localhost:${PORT}`);
});
