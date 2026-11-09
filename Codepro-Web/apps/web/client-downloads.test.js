const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const os = require('node:os');
const path = require('node:path');
const { availableDownloads } = require('./client-downloads');

test('only complete, correctly named installers are listed', async () => {
  const directory = fs.mkdtempSync(path.join(os.tmpdir(), 'codepro-downloads-'));
  const windows = 'CodeProOJ-Client-1.2.6.exe';
  const mac = 'CodeProOJ-Client-1.2.7-mac-arm64.dmg';
  const linux = 'CodeProOJ-Client-1.2.7-linux-x64.deb';
  try {
    fs.writeFileSync(path.join(directory, windows), 'win');
    fs.writeFileSync(path.join(directory, mac), 'mac');
    fs.writeFileSync(path.join(directory, linux), 'linux');
    fs.writeFileSync(path.join(directory, 'client-manifest.json'), JSON.stringify({
      schemaVersion: 2,
      downloads: {
        windows: { version: '1.2.6', file: windows, bytes: 3, sha256: 'a'.repeat(64) },
        'mac-arm64': { version: '1.2.7', file: mac, bytes: 3, sha256: 'b'.repeat(64) },
        'mac-x64': { version: '1.2.7', file: '../other.dmg', bytes: 3, sha256: 'c'.repeat(64) },
        'linux-x64': { version: '1.2.7', file: linux, bytes: 99, sha256: 'd'.repeat(64) }
      }
    }));
    const found = await availableDownloads(directory);
    assert.deepEqual(Object.keys(found), ['windows', 'mac-arm64']);
    assert.equal(found['mac-arm64'].file, mac);
  } finally {
    fs.rmSync(directory, { recursive: true, force: true });
  }
});
