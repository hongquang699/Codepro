// API Gateway / App Entry
const app = require('../../backend/app');
const http = require('http');

const PORT = process.env.PORT || 4000;
const server = http.createServer(app);

server.listen(PORT, () => {
  console.log(`Coding Platform API listening on port ${PORT}`);
});
