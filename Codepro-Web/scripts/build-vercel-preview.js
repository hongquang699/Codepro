const fs = require('node:fs');
const path = require('node:path');

const root = path.resolve(__dirname, '..');
const output = path.join(root, 'dist-vercel');
const frontend = path.join(root, 'frontend');
const gatewaySource = fs.readFileSync(path.join(root, 'apps', 'web', 'server.js'), 'utf8');
const aliasBlock = gatewaySource.match(/const ROUTE_ALIASES = \{([\s\S]*?)\n\};/);
if (!aliasBlock) throw new Error('Không tìm thấy bảng tuyến trang web trong gateway.');

// The preview contains no backend, judge, private uploads, or local installer.
if (path.dirname(output) !== root || path.basename(output) !== 'dist-vercel') {
  throw new Error('Thư mục build không hợp lệ.');
}
fs.rmSync(output, { recursive: true, force: true });
fs.cpSync(frontend, path.join(output, 'frontend'), {
  recursive: true,
  filter: source => !source.startsWith(path.join(frontend, 'downloads') + path.sep)
    && source !== path.join(frontend, 'downloads'),
});

const notice = '<div role="status" style="position:relative;z-index:10000;padding:10px 18px;background:#203865;color:#fff;text-align:center;font:600 13px/1.5 system-ui,sans-serif">Bản xem trước trên Vercel: CodeProOJ chưa có API và máy chấm công khai. Đăng nhập, dữ liệu và nộp bài chưa hoạt động.</div>';
const htmlRoot = path.join(output, 'frontend', 'html');
function addNotice(folder) {
  for (const item of fs.readdirSync(folder, { withFileTypes: true })) {
    const file = path.join(folder, item.name);
    if (item.isDirectory()) addNotice(file);
    else if (item.isFile() && item.name.endsWith('.html')) {
      const html = fs.readFileSync(file, 'utf8');
      fs.writeFileSync(file, html.replace(/(<body\b[^>]*>)/i, `$1\n${notice}`));
    }
  }
}
addNotice(htmlRoot);

const aliases = [...aliasBlock[1].matchAll(/^\s*'([^']+)':\s*'([^']+)'/gm)];
if (aliases.length < 50) throw new Error('Bảng tuyến trang web không đầy đủ.');
let copied = 0;
let missing = 0;
for (const [, route, destination] of aliases) {
  if (!/^\/[a-z0-9/-]*$/i.test(route) || !destination.startsWith('/frontend/html/')) {
    throw new Error(`Tuyến không hợp lệ: ${route}`);
  }
  const source = path.join(output, destination.slice(1));
  if (!fs.existsSync(source)) { missing++; continue; }
  const name = route.replace(/^\/|\/$/g, '');
  const target = path.join(output, name ? `${name}.html` : 'index.html');
  fs.mkdirSync(path.dirname(target), { recursive: true });
  fs.copyFileSync(source, target);
  copied++;
}
fs.copyFileSync(path.join(root, 'favicon.ico'), path.join(output, 'favicon.ico'));
console.log(`Vercel preview: ${copied} tuyến, ${missing} tuyến chưa có trang nguồn.`);
