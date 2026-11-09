const fs = require('node:fs/promises');
const path = require('node:path');

const filenames = {
  windows: version => `CodeProOJ-Client-${version}.exe`,
  'mac-arm64': version => `CodeProOJ-Client-${version}-mac-arm64.dmg`,
  'mac-x64': version => `CodeProOJ-Client-${version}-mac-x64.dmg`,
  'linux-x64': version => `CodeProOJ-Client-${version}-linux-x64.deb`
};

function manifestEntries(manifest) {
  if (manifest?.schemaVersion === 2 && manifest.downloads && typeof manifest.downloads === 'object') {
    return manifest.downloads;
  }
  if (manifest?.version && manifest?.file) {
    return { windows: manifest };
  }
  return {};
}

function validEntry(platform, entry) {
  return Object.hasOwn(filenames, platform) &&
    entry && typeof entry === 'object' &&
    typeof entry.version === 'string' && /^\d+\.\d+\.\d+$/.test(entry.version) &&
    entry.file === filenames[platform](entry.version) &&
    Number.isSafeInteger(entry.bytes) && entry.bytes > 0 &&
    typeof entry.sha256 === 'string' && /^[a-f0-9]{64}$/.test(entry.sha256);
}

async function availableDownloads(downloadsDir) {
  let manifest;
  try {
    manifest = JSON.parse(await fs.readFile(path.join(downloadsDir, 'client-manifest.json'), 'utf8'));
  } catch {
    return {};
  }
  const entries = manifestEntries(manifest);
  const available = {};
  for (const platform of Object.keys(filenames)) {
    const entry = entries[platform];
    if (!validEntry(platform, entry)) continue;
    try {
      const stat = await fs.stat(path.join(downloadsDir, entry.file));
      if (stat.isFile() && stat.size === entry.bytes) available[platform] = entry;
    } catch { /* Artifact is not published on this server. */ }
  }
  return available;
}

module.exports = { availableDownloads, validEntry };
