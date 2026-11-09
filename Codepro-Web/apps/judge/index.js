/**
 * Node.js Judge Manager & Heartbeat Service
 */
const { spawn } = require('child_process');
const path = require('path');

console.log('[APPS/JUDGE] Starting CodeProOJ Judge Worker Process...');

const workerScript = path.resolve(__dirname, '../../judge/worker/worker.py');
const pyProc = spawn('python', [workerScript], { stdio: 'inherit' });

pyProc.on('exit', (code) => {
  console.log(`[APPS/JUDGE] Worker exited with code ${code}`);
});
