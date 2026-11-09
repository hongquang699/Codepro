const http = require('http');
const path = require('path');
const { spawn } = require('child_process');

const serverPath = path.resolve(__dirname, '../../apps/web/server.js');
const port = 20000 + Math.floor(Math.random() * 30000);
let server;

function fetchPath(requestPath) {
  return new Promise((resolve, reject) => {
    http.get({ hostname: '127.0.0.1', port, path: requestPath }, response => {
      let body = '';
      response.setEncoding('utf8');
      response.on('data', chunk => { body += chunk; });
      response.on('end', () => resolve({ status: response.statusCode, body }));
    }).on('error', reject);
  });
}

beforeAll(async () => {
  server = spawn(process.execPath, [serverPath], {
    env: { ...process.env, PORT: String(port) },
    stdio: ['ignore', 'pipe', 'pipe'],
    windowsHide: true
  });
  await new Promise((resolve, reject) => {
    const timeout = setTimeout(() => reject(new Error('Gateway did not start')), 5000);
    server.once('exit', code => {
      clearTimeout(timeout);
      reject(new Error(`Gateway exited with code ${code}`));
    });
    server.stdout.on('data', chunk => {
      if (chunk.toString().includes('[FRONTEND SERVER] Active')) {
        clearTimeout(timeout);
        resolve();
      }
    });
  });
});

afterAll(() => {
  if (server) server.kill();
});

test('unknown path is escaped in the HTML 404 response', async () => {
  const response = await fetchPath('/%3Cimg%20src=x%20onerror=alert(1)%3E');
  expect(response.status).toBe(404);
  expect(response.body).toContain('&lt;img src=x onerror=alert(1)&gt;');
  expect(response.body).not.toContain('<img src=x onerror=alert(1)>');
});

test('malformed URL returns 400 without crashing the gateway', async () => {
  const response = await fetchPath('/%ZZ');
  expect(response.status).toBe(400);
  expect(response.body).toBe('Invalid URL');
});
