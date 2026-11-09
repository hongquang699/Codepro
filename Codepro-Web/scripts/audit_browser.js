/* Sample browser navigation to catch errors that an HTTP asset crawl cannot see. */
const fs = require('fs');
const os = require('os');
const path = require('path');
const { spawn } = require('child_process');
const WebSocket = require('ws');

const chromePath = 'C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe';
const profile = fs.mkdtempSync(path.join(os.tmpdir(), 'hq-browser-audit-'));
const chrome = spawn(chromePath, [
  '--headless=new', '--disable-gpu', '--no-first-run', '--no-default-browser-check',
  '--remote-debugging-port=0', `--user-data-dir=${profile}`, 'about:blank'
], { windowsHide: true, stdio: 'ignore' });

const sleep = ms => new Promise(resolve => setTimeout(resolve, ms));

async function waitForPort() {
  const file = path.join(profile, 'DevToolsActivePort');
  for (let i = 0; i < 100; i++) {
    if (fs.existsSync(file)) return Number(fs.readFileSync(file, 'utf8').split('\n')[0]);
    if (chrome.exitCode !== null) throw new Error(`Chrome exited: ${chrome.exitCode}`);
    await sleep(100);
  }
  throw new Error('Chrome did not open a debugging port');
}

async function auditPage(port, route) {
  const tabs = await (await fetch(`http://127.0.0.1:${port}/json`)).json();
  const tab = tabs.find(item => item.type === 'page');
  if (!tab) throw new Error('No Chrome page target');
  const socket = new WebSocket(tab.webSocketDebuggerUrl);
  await new Promise((resolve, reject) => { socket.once('open', resolve); socket.once('error', reject); });
  let nextId = 0;
  const pending = new Map();
  const errors = [];
  const requests = new Map();
  const slow = [];
  let loadAt = 0;
  socket.on('message', raw => {
    const message = JSON.parse(raw.toString());
    if (message.id && pending.has(message.id)) {
      pending.get(message.id)(message);
      pending.delete(message.id);
    }
    if (message.method === 'Network.responseReceived' && message.params.response.status >= 400) {
      errors.push(`${message.params.response.status} ${message.params.response.url}`);
    }
    if (message.method === 'Network.requestWillBeSent') {
      requests.set(message.params.requestId, {
        url: message.params.request.url, started: message.params.timestamp
      });
    }
    if (message.method === 'Network.loadingFinished') {
      const request = requests.get(message.params.requestId);
      if (request) slow.push({ url: request.url, ms: Math.round((message.params.timestamp - request.started) * 1000) });
    }
    if (message.method === 'Runtime.exceptionThrown') {
      errors.push(`JS ${message.params.exceptionDetails.text}`);
    }
    if (message.method === 'Page.loadEventFired') loadAt = Date.now();
  });
  const send = (method, params = {}) => new Promise(resolve => {
    const id = ++nextId;
    pending.set(id, resolve);
    socket.send(JSON.stringify({ id, method, params }));
  });
  await send('Page.enable');
  await send('Network.enable');
  await send('Runtime.enable');
  const started = Date.now();
  await send('Page.navigate', { url: `http://127.0.0.1:8888${route}` });
  for (let i = 0; i < 100 && !loadAt; i++) await sleep(100);
  await sleep(400);
  console.log(`${route} load=${loadAt ? loadAt - started : 'timeout'}ms errors=${errors.length}`);
  for (const error of errors.slice(0, 8)) console.log(`  ${error}`);
  if (route === '/') {
    for (const item of slow.sort((a, b) => b.ms - a.ms).slice(0, 8)) {
      console.log(`  slow ${item.ms}ms ${item.url}`);
    }
  }
  socket.close();
}

(async () => {
  try {
    const port = await waitForPort();
    const routes = process.argv.slice(2);
    for (const route of routes.length ? routes : [
      '/', '/', '/problems', '/contests', '/ranking', '/submissions', '/community',
      '/blog', '/learning', '/organizations', '/login',
      '/frontend/html/profile/index.html?username=admin',
      '/frontend/html/profile/problems.html?username=admin',
      '/frontend/html/profile/contests.html?username=admin'
    ]) {
      await auditPage(port, route);
    }
  } catch (error) {
    console.error(error);
    process.exitCode = 1;
  } finally {
    chrome.kill();
  }
})();
