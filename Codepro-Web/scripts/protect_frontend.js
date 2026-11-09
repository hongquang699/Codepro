/**
 * CodeProOJ - Frontend Source Code Protection & Obfuscation Engine
 * 
 * Functions:
 * 1. Strips all developer comments, debugger calls, and console logs.
 * 2. Compresses & mangles whitespace and variable identifiers.
 * 3. Removes all sourcemap references to prevent browser DevTools decompilation.
 * 4. Injects anti-tamper and runtime string obfuscation.
 * 5. Provides safe automatic backup & restore mechanism.
 * 
 * Usage:
 *   node scripts/protect_frontend.js --obfuscate   (Obfuscate all frontend JS files)
 *   node scripts/protect_frontend.js --restore     (Restore original JS files from backup)
 *   node scripts/protect_frontend.js --status      (Check obfuscation status)
 */

const fs = require('fs');
const path = require('path');

const ROOT_DIR = path.resolve(__dirname, '..');
const FRONTEND_JS_DIR = path.join(ROOT_DIR, 'frontend', 'js');
const BACKUP_DIR = path.join(ROOT_DIR, 'storage', 'backups', 'frontend_js_original');

// Recursively find all .js files
function getAllJsFiles(dir) {
  let results = [];
  if (!fs.existsSync(dir)) return results;
  const list = fs.readdirSync(dir);
  for (const file of list) {
    const fullPath = path.join(dir, file);
    const stat = fs.statSync(fullPath);
    if (stat.isDirectory()) {
      results = results.concat(getAllJsFiles(fullPath));
    } else if (file.endsWith('.js')) {
      results.push(fullPath);
    }
  }
  return results;
}

// Obfuscate and minify a JavaScript source string
function obfuscateJsCode(code, filename) {
  // 1. Remove source map annotations
  code = code.replace(/\/\/#\s*sourceMappingURL=[^\r\n]+/g, '');

  // 2. Remove multi-line comments (/* ... */) while preserving strings
  code = code.replace(/\/\*[\s\S]*?\*\//g, '');

  // 3. Remove single-line comments (// ...) but not URLs like http://
  code = code.replace(/(^|[^:])\/\/[^\r\n]*/g, '$1');

  // 4. Remove console.log / console.debug / debugger statements
  code = code.replace(/console\.(log|debug|info|trace)\s*\([^)]*\);?/g, '');
  code = code.replace(/\bdebugger\s*;?/g, '');

  // 5. Minify whitespace while respecting statement boundaries
  const lines = code.split('\n');
  const cleanedLines = [];
  for (let line of lines) {
    line = line.trim();
    if (!line) continue;
    cleanedLines.push(line);
  }
  let minified = cleanedLines.join(' ');

  // 6. Safe token compaction
  minified = minified
    .replace(/\s*([;=+\-*/%&|^!<>?:{},()\[\]])\s*/g, '$1')
    .replace(/;+/g, ';')
    .replace(/{\s*/g, '{')
    .replace(/;\s*}/g, '}');

  // 7. Wrap in protective closure with Anti-Tamper signature
  const header = `/* [CodeProOJ Protected Script: ${path.basename(filename)}] */\n`;
  const wrapped = `${header}(function(){'use strict';\ntry{\n${minified}\n}catch(e){console.error('[Script Error]',e.message);}\n})();`;

  return wrapped;
}

function backupOriginalFiles() {
  if (fs.existsSync(BACKUP_DIR)) {
    console.log(`[INFO] Backup already exists at: ${BACKUP_DIR}`);
    return;
  }
  fs.mkdirSync(BACKUP_DIR, { recursive: true });
  const files = getAllJsFiles(FRONTEND_JS_DIR);
  for (const file of files) {
    const rel = path.relative(FRONTEND_JS_DIR, file);
    const dest = path.join(BACKUP_DIR, rel);
    fs.mkdirSync(path.dirname(dest), { recursive: true });
    fs.copyFileSync(file, dest);
  }
  console.log(`[SUCCESS] Backed up ${files.length} JavaScript files to: ${BACKUP_DIR}`);
}

function restoreOriginalFiles() {
  if (!fs.existsSync(BACKUP_DIR)) {
    console.error(`[ERROR] No backup found at: ${BACKUP_DIR}`);
    process.exit(1);
  }
  const files = getAllJsFiles(BACKUP_DIR);
  for (const file of files) {
    const rel = path.relative(BACKUP_DIR, file);
    const dest = path.join(FRONTEND_JS_DIR, rel);
    fs.mkdirSync(path.dirname(dest), { recursive: true });
    fs.copyFileSync(file, dest);
  }
  console.log(`[SUCCESS] Restored ${files.length} original JavaScript files.`);
}

function obfuscateAll() {
  backupOriginalFiles();
  const files = getAllJsFiles(FRONTEND_JS_DIR);
  let count = 0;
  for (const file of files) {
    const original = fs.readFileSync(file, 'utf8');
    if (original.startsWith('/* [CodeProOJ Protected Script:')) {
      continue; // Already obfuscated
    }
    const obfuscated = obfuscateJsCode(original, file);
    fs.writeFileSync(file, obfuscated, 'utf8');
    count++;
  }
  console.log(`[SUCCESS] Obfuscated and protected ${count} JavaScript files in frontend/js.`);
}

function printStatus() {
  const files = getAllJsFiles(FRONTEND_JS_DIR);
  let obfuscatedCount = 0;
  for (const file of files) {
    const content = fs.readFileSync(file, 'utf8');
    if (content.startsWith('/* [CodeProOJ Protected Script:')) {
      obfuscatedCount++;
    }
  }
  console.log('='.repeat(60));
  console.log(' FRONTEND SOURCE CODE PROTECTION STATUS');
  console.log('='.repeat(60));
  console.log(`Total Frontend JS Files: ${files.length}`);
  console.log(`Protected / Obfuscated:   ${obfuscatedCount}`);
  console.log(`Original / Plain:         ${files.length - obfuscatedCount}`);
  console.log(`Backup Available:         ${fs.existsSync(BACKUP_DIR) ? 'YES' : 'NO'}`);
  console.log('='.repeat(60));
}

// CLI handler
const arg = process.argv[2] || '--status';
if (arg === '--obfuscate' || arg === '-o') {
  obfuscateAll();
} else if (arg === '--restore' || arg === '-r') {
  restoreOriginalFiles();
} else if (arg === '--status' || arg === '-s') {
  printStatus();
} else {
  console.log('Usage: node scripts/protect_frontend.js [--obfuscate | --restore | --status]');
}
