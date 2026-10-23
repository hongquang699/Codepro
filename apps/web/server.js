const http = require('http');
const fs = require('fs');
const path = require('path');
const { securityDefense } = require('./security');
const { createLiveSync } = require('./live-sync');

const PORT = process.env.PORT || 8888;
const BACKEND_HOST = process.env.DJANGO_BACKEND_HOST || '127.0.0.1';
const BACKEND_PORT = Number(process.env.DJANGO_BACKEND_PORT || 8000);
const BACKEND_PROXY_SCHEME = process.env.DJANGO_PROXY_SCHEME === 'https' ? 'https' : null;
const ROOT_DIR = path.resolve(__dirname, '../../');
const ADMIN_SECURITY_PATHS = new Set([
  '/api/v2/admin/security/stats',
  '/api/v2/admin/security/config'
]);

const MIME_TYPES = {
  '.html': 'text/html; charset=utf-8',
  '.css': 'text/css; charset=utf-8',
  '.js': 'application/javascript; charset=utf-8',
  '.json': 'application/json; charset=utf-8',
  '.svg': 'image/svg+xml',
  '.png': 'image/png',
  '.jpg': 'image/jpeg',
  '.ico': 'image/x-icon',
  '.woff': 'font/woff',
  '.woff2': 'font/woff2',
  '.ttf': 'font/ttf'
};

function getClientIp(req) {
  return securityDefense.resolveClientIp(req);
}

function escapeHtml(value) {
  return String(value).replace(/[&<>"']/g, char => ({
    '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;'
  })[char]);
}

function isAdminIpAllowed(req) {
  const clientIp = getClientIp(req);
  if (!clientIp) return false;
  const normalize = ip => ip.startsWith('::ffff:') ? ip.substring(7) : (ip === '::1' ? '127.0.0.1' : ip);
  try {
    const configPath = path.join(ROOT_DIR, 'config', 'admin_ip_whitelist.json');
    if (fs.existsSync(configPath)) {
      const cfg = JSON.parse(fs.readFileSync(configPath, 'utf8'));
      // A disabled or malformed whitelist must fail closed for admin routes.
      if (cfg.enabled === false) return false;
      const allowed = cfg.allowed_ips || [];
      if (!Array.isArray(allowed)) return false;
      const cleanClient = normalize(clientIp);
      return allowed.some(a => {
        return typeof a === 'string' && normalize(a) === cleanClient;
      });
    }
  } catch (e) {
    console.error('[IP WHITELIST CHECK ERROR]', e.message);
  }
  return false;
}

function hasVerifiedAdminSession(req) {
  return new Promise(resolve => {
    const authReq = http.request({
      hostname: BACKEND_HOST,
      port: BACKEND_PORT,
      path: '/api/v1/auth/me',
      method: 'GET',
      headers: {
        cookie: req.headers.cookie || '', host: `${BACKEND_HOST}:${BACKEND_PORT}`,
        ...(BACKEND_PROXY_SCHEME ? { 'x-forwarded-proto': BACKEND_PROXY_SCHEME } : {})
      },
      timeout: 3000
    }, authRes => {
      let body = '';
      authRes.on('data', chunk => {
        body += chunk;
        if (body.length > 8192) authRes.destroy();
      });
      authRes.on('end', () => {
        try {
          const result = JSON.parse(body);
          resolve(authRes.statusCode === 200 && result.authenticated === true &&
            (result.user?.is_staff === true || result.user?.is_superuser === true));
        } catch (_) { resolve(false); }
      });
      authRes.on('error', () => resolve(false));
    });
    authReq.on('timeout', () => authReq.destroy());
    authReq.on('error', () => resolve(false));
    authReq.end();
  });
}

// Friendly route aliases
const ROUTE_ALIASES = {
  '/': '/frontend/html/home/index.html',
  '/home': '/frontend/html/home/index.html',
  '/client': '/frontend/html/client/index.html',
  '/problems': '/frontend/html/problems/index.html',
  '/problem': '/frontend/html/problems/problem.html',
  '/submit': '/frontend/html/problem/submit.html',
  '/contests': '/frontend/html/contest/index.html',
  '/contest': '/frontend/html/contest/index.html',
  '/scoreboard': '/frontend/html/contest/scoreboard.html',
  '/submissions': '/frontend/html/submissions/index.html',
  '/submissions/': '/frontend/html/submissions/index.html',
  '/submissions/my': '/frontend/html/submissions/my-submissions.html',
  '/submission': '/frontend/html/submissions/index.html',
  '/ranking': '/frontend/html/ranking/index.html',
  '/ranking/': '/frontend/html/ranking/index.html',
  '/rankings': '/frontend/html/ranking/index.html',
  '/rankings/': '/frontend/html/ranking/index.html',
  '/ranking/global': '/frontend/html/ranking/index.html',
  '/ranking/rating': '/frontend/html/ranking/rating.html',
  '/ranking/contest': '/frontend/html/ranking/index.html',
  '/ranking/country': '/frontend/html/ranking/country.html',
  '/ranking/school': '/frontend/html/ranking/school.html',
  '/ranking/organization': '/frontend/html/ranking/organization.html',
  '/ranking/history': '/frontend/html/ranking/rating-history.html',
  '/ranking/user': '/frontend/html/ranking/user-ranking.html',
  '/courses': '/frontend/html/courses/index.html',
  '/course': '/frontend/html/courses/index.html',
  '/learning': '/frontend/html/learning/index.html',
  '/learning/': '/frontend/html/learning/index.html',
  '/wiki': '/frontend/html/learning/index.html',
  '/wiki/': '/frontend/html/learning/index.html',
  '/community': '/frontend/html/community/home/index.html',
  '/blog': '/frontend/html/blog/index.html',
  '/forum': '/frontend/html/community/forum/index.html',
  '/login': '/frontend/html/auth/login.html',
  '/register': '/frontend/html/auth/register.html',
  '/verify-email': '/frontend/html/auth/verify-email.html',
  '/forgot-password': '/frontend/html/auth/forgot-password.html',
  '/reset-password': '/frontend/html/auth/reset-password.html',
  '/change-password': '/frontend/html/auth/change-password.html',
  '/two-factor': '/frontend/html/auth/two-factor.html',
  '/logout': '/frontend/html/auth/logout.html',
  '/profile': '/frontend/html/profile/index.html',
  '/settings': '/frontend/html/profile/settings.html',
  '/my/appeals': '/frontend/html/user/appeals.html',
  '/admin': '/frontend/html/admin/dashboard.html',
  '/admin/': '/frontend/html/admin/dashboard.html',
  '/admin/dashboard': '/frontend/html/admin/dashboard.html',
  '/admin/menu': '/frontend/html/admin/menu.html',
  '/admin/menu/': '/frontend/html/admin/menu.html',
  '/admin-menu': '/frontend/html/admin/menu.html',
  '/admin/login': '/frontend/html/admin/login.html',
  '/admin/problems': '/frontend/html/admin/problems/index.html',
  '/admin/problems/': '/frontend/html/admin/problems/index.html',
  '/admin/problems/create': '/frontend/html/admin/problems/create.html',
  '/admin/problems/edit': '/frontend/html/admin/problems/create.html',
  '/admin/contests': '/frontend/html/admin/contests/index.html',
  '/admin/contests/': '/frontend/html/admin/contests/index.html',
  '/admin/contests/create': '/frontend/html/admin/contests/create.html',
  '/admin/anti-cheat': '/frontend/html/admin/reports/index.html',
  '/admin/anti-cheat/': '/frontend/html/admin/reports/index.html',
  '/admin/judge': '/frontend/html/admin/judge/index.html',
  '/admin/judge/': '/frontend/html/admin/judge/index.html',
  '/admin/users': '/frontend/html/admin/users/index.html',
  '/admin/users/': '/frontend/html/admin/users/index.html',
  '/admin/organizations': '/frontend/html/admin/organizations/index.html',
  '/admin/organizations/': '/frontend/html/admin/organizations/index.html',
  '/admin/blogs': '/frontend/html/admin/blogs/index.html',
  '/admin/blogs/': '/frontend/html/admin/blogs/index.html',
  '/admin/submissions': '/frontend/html/admin/submissions/index.html',
  '/admin/submissions/': '/frontend/html/admin/submissions/index.html',
  '/admin/settings': '/frontend/html/admin/settings/general.html',
  '/admin/settings/': '/frontend/html/admin/settings/general.html',
  '/admin/security': '/frontend/html/admin/settings/security.html',
  '/admin/settings/security': '/frontend/html/admin/settings/security.html',
  '/admin/contests/manage': '/frontend/html/admin/contests/manage.html',
  '/admin/contests/edit': '/frontend/html/admin/contests/edit.html',
  '/admin/contests/participants': '/frontend/html/admin/contests/participants.html',
  '/admin/contests/scoreboard': '/frontend/html/admin/contests/scoreboard.html',
  '/admin/contests/rejudge': '/frontend/html/admin/contests/rejudge.html',
  '/admin/judge/workers': '/frontend/html/admin/judge/workers.html',
  '/admin/judge/queue': '/frontend/html/admin/judge/queue.html',
  '/admin/judge/logs': '/frontend/html/admin/judge/logs.html',
  '/admin/judge/rejudge': '/frontend/html/admin/judge/rejudge.html',
  '/admin/system/status': '/frontend/html/admin/system/status.html',
  '/admin/system/database': '/frontend/html/admin/system/database.html',
  '/admin/system/cache': '/frontend/html/admin/system/cache.html',
  '/admin/system/logs': '/frontend/html/admin/system/logs.html',
  '/admin/users/detail': '/frontend/html/admin/users/detail.html',
  '/admin/users/edit': '/frontend/html/admin/users/edit.html',
  '/admin/users/roles': '/frontend/html/admin/users/roles.html',
  '/admin/users/ban': '/frontend/html/admin/users/ban.html',
  '/admin/submissions/detail': '/frontend/html/admin/submissions/detail.html',
  '/admin/submissions/rejudge': '/frontend/html/admin/submissions/rejudge.html',
  '/admin/announcements': '/frontend/html/admin/announcements/index.html',
  '/admin/reports': '/frontend/html/admin/reports/index.html',
  '/admin/problems/export': '/frontend/html/admin/problems/export.html',
  '/admin/problems/import': '/frontend/html/admin/problems/import.html',
  '/admin/problems/checker': '/frontend/html/admin/problems/checker.html',
  '/admin/problems/validator': '/frontend/html/admin/problems/validator.html',
  '/organizations': '/frontend/html/organization/index.html',
  '/organizations/': '/frontend/html/organization/index.html',
  '/search': '/frontend/html/search/index.html'
};

const server = http.createServer(async (req, res) => {
  // Apply Enterprise Security Headers
  securityDefense.applySecurityHeaders(res);

  const urlParts = req.url.split('?');
  let reqUrl;
  try {
    reqUrl = decodeURI(urlParts[0]);
  } catch (error) {
    res.writeHead(400, { 'Content-Type': 'text/plain; charset=utf-8' });
    return res.end('Invalid URL');
  }
  const queryString = urlParts.length > 1 ? `?${urlParts[1]}` : '';

  // Apply the same WAF and rate limits to gateway-owned admin endpoints.
  const secCheck = securityDefense.inspect(req);
  if (!secCheck.allowed) {
    res.writeHead(secCheck.status, {
      'Content-Type': 'application/json',
      ...(secCheck.headers || {})
    });
    return res.end(JSON.stringify({
      error: 'SECURITY_BLOCKED',
      status: secCheck.status,
      message: secCheck.message,
      client_ip: secCheck.ip
    }));
  }

  if (reqUrl === '/client/download/windows') {
    if (req.method !== 'GET' && req.method !== 'HEAD') {
      res.writeHead(405, { Allow: 'GET, HEAD' });
      return res.end();
    }
    const downloadsDir = path.join(ROOT_DIR, 'frontend', 'downloads');
    try {
      const manifest = JSON.parse(await fs.promises.readFile(path.join(downloadsDir, 'client-manifest.json'), 'utf8'));
      if (!/^CodeProOJ-Client-\d+\.\d+\.\d+\.exe$/.test(manifest.file)) throw new Error('Invalid installer name');
      const installer = path.join(downloadsDir, manifest.file);
      const stat = await fs.promises.stat(installer);
      if (!stat.isFile() || stat.size !== manifest.bytes) throw new Error('Installer unavailable');
      res.writeHead(200, {
        'Content-Type': 'application/octet-stream',
        'Content-Disposition': `attachment; filename="${manifest.file}"`,
        'Content-Length': stat.size,
        'Cache-Control': 'public, max-age=3600',
        'X-Content-Type-Options': 'nosniff'
      });
      if (req.method === 'HEAD') return res.end();
      return fs.createReadStream(installer).pipe(res);
    } catch {
      res.writeHead(404, { 'Content-Type': 'text/plain; charset=utf-8' });
      return res.end('Bản cài chưa được phát hành trên máy chủ.');
    }
  }

  // The administrative security controls live on the gateway and never pass
  // through the application backend. Protect them before any handler runs.
  if (ADMIN_SECURITY_PATHS.has(reqUrl)) {
    if (!isAdminIpAllowed(req)) {
      res.writeHead(403, { 'Content-Type': 'application/json; charset=utf-8' });
      return res.end(JSON.stringify({ error: 'ADMIN_IP_RESTRICTED' }));
    }

    if (!await hasVerifiedAdminSession(req)) {
      res.writeHead(403, { 'Content-Type': 'application/json; charset=utf-8' });
      return res.end(JSON.stringify({ error: 'ADMIN_SESSION_REQUIRED' }));
    }

    if (req.method === 'POST') {
      const origin = req.headers.origin;
      const host = req.headers.host;
      let sameOrigin = false;
      try { sameOrigin = Boolean(origin && host && new URL(origin).host === host); } catch (_) {}
      if (!sameOrigin) {
        res.writeHead(403, { 'Content-Type': 'application/json; charset=utf-8' });
        return res.end(JSON.stringify({ error: 'ORIGIN_RESTRICTED' }));
      }
    }

    if (reqUrl.endsWith('/config') && req.method !== 'POST') {
      res.writeHead(405, { 'Allow': 'POST', 'Content-Type': 'application/json; charset=utf-8' });
      return res.end(JSON.stringify({ error: 'METHOD_NOT_ALLOWED' }));
    }

    if (reqUrl.endsWith('/stats') && req.method !== 'GET') {
      res.writeHead(405, { 'Allow': 'GET', 'Content-Type': 'application/json; charset=utf-8' });
      return res.end(JSON.stringify({ error: 'METHOD_NOT_ALLOWED' }));
    }

    if (reqUrl.endsWith('/stats')) {
      res.writeHead(200, { 'Content-Type': 'application/json; charset=utf-8' });
      return res.end(JSON.stringify({ status: 200, data: securityDefense.getSecurityReport() }));
    }

    if (req.method === 'POST') {
      let body = '';
      req.on('data', chunk => {
        body += chunk;
        if (body.length > 16 * 1024) req.destroy();
      });
      req.on('end', () => {
        try {
          const payload = JSON.parse(body || '{}');
          const validModes = new Set(['normal', 'high', 'under_attack']);
          const validActions = new Set([
            'set_mode', 'ban_ip', 'blacklist_ip', 'unban_ip', 'unblacklist_ip',
            'jail_ip', 'unjail_ip', 'whitelist_ip', 'unwhitelist_ip', 'clear_jails'
          ]);
          if (payload.mode !== undefined && !validModes.has(payload.mode)) throw new Error('Invalid mode');
          if (payload.action !== undefined && !validActions.has(payload.action)) throw new Error('Invalid action');
          if (!payload.action) throw new Error('Action is required');
          if (payload.ip !== undefined && (typeof payload.ip !== 'string' || !require('net').isIP(payload.ip))) {
            throw new Error('Invalid IP address');
          }
          if (payload.action === 'set_mode' && !payload.mode) throw new Error('Mode is required');
          if (payload.action.includes('_ip') && !payload.ip) throw new Error('IP address is required');
          if (payload.durationMs !== undefined && (!Number.isSafeInteger(payload.durationMs) || payload.durationMs < 1000 || payload.durationMs > 30 * 24 * 3600 * 1000)) {
            throw new Error('Invalid jail duration');
          }

          if (payload.action === 'set_mode') securityDefense.mode = payload.mode;
          if (payload.action === 'ban_ip' || payload.action === 'blacklist_ip') {
            securityDefense.blacklist.add(payload.ip);
            securityDefense.jailIp(payload.ip, payload.reason || 'MANUAL_ADMIN_BLACKLIST', 365 * 24 * 3600 * 1000);
          }
          if (payload.action === 'unban_ip' || payload.action === 'unblacklist_ip') {
            securityDefense.blacklist.delete(payload.ip);
            securityDefense.jailedIps.delete(payload.ip);
          }
          if (payload.action === 'jail_ip') securityDefense.jailIp(payload.ip, payload.reason || 'MANUAL_ADMIN_JAIL', payload.durationMs || 30 * 60 * 1000);
          if (payload.action === 'unjail_ip') securityDefense.jailedIps.delete(payload.ip);
          if (payload.action === 'whitelist_ip') {
            securityDefense.whitelist.add(payload.ip);
            securityDefense.jailedIps.delete(payload.ip);
            securityDefense.blacklist.delete(payload.ip);
          }
          if (payload.action === 'unwhitelist_ip') securityDefense.whitelist.delete(payload.ip);
          if (payload.action === 'clear_jails') securityDefense.jailedIps.clear();

          res.writeHead(200, { 'Content-Type': 'application/json; charset=utf-8' });
          return res.end(JSON.stringify({ status: 200, message: 'Đã cập nhật cấu hình bảo mật thành công', data: securityDefense.getSecurityReport() }));
        } catch (err) {
          res.writeHead(400, { 'Content-Type': 'application/json; charset=utf-8' });
          return res.end(JSON.stringify({ error: err.message }));
        }
      });
      return;
    }

    res.writeHead(405, { 'Allow': reqUrl.endsWith('/stats') ? 'GET' : 'POST', 'Content-Type': 'application/json; charset=utf-8' });
    return res.end(JSON.stringify({ error: 'METHOD_NOT_ALLOWED' }));
  }

  // Handle legacy ranking pages redirects
  if (reqUrl.startsWith('/ranking/pages/')) {
    const page = reqUrl.replace('/ranking/pages/', '');
    res.writeHead(301, { 'Location': `/frontend/html/ranking/${page}${queryString}` });
    return res.end();
  }

  // Server-side Admin Route Protection: Only role 'admin' can access admin portal
  const lowerUrl = reqUrl.toLowerCase();
  const isJudgeRoute = lowerUrl === '/admin/judge' || lowerUrl.startsWith('/admin/judge/');
  const isAdminRoute = (lowerUrl.startsWith('/admin') && !lowerUrl.startsWith('/admin/login') && !isJudgeRoute) ||
                       (lowerUrl.startsWith('/frontend/html/admin/') && !lowerUrl.includes('login.html'));

  if (isAdminRoute) {
    // 1. Enforce Admin IP Whitelist
    if (!isAdminIpAllowed(req)) {
      const clientIp = getClientIp(req);
      console.warn(`[SECURITY ALERT] Admin access blocked for non-whitelisted IP: ${clientIp} on path: ${reqUrl}`);
      if (req.headers.accept && req.headers.accept.includes('application/json')) {
        res.writeHead(403, { 'Content-Type': 'application/json; charset=utf-8' });
        return res.end(JSON.stringify({ 
          error: 'Từ chối truy cập: Địa chỉ IP không được ủy quyền cho Quản trị viên.', 
          code: 'ADMIN_IP_RESTRICTED',
          client_ip: clientIp 
        }));
      }
      res.writeHead(403, { 'Content-Type': 'text/html; charset=utf-8' });
      return res.end(`
        <!DOCTYPE html>
        <html lang="vi">
        <head>
          <meta charset="utf-8">
          <title>403 - IP Không Được Ủy Quyền | CodeProOJ Admin</title>
          <style>
            body { font-family: system-ui, -apple-system, sans-serif; background: #0b1120; color: #f8fafc; display: flex; align-items: center; justify-content: center; height: 100vh; margin: 0; padding: 1.5rem; box-sizing: border-box; }
            .card { background: #0f172a; border: 1px solid rgba(239, 68, 68, 0.3); border-radius: 16px; padding: 2.5rem; max-width: 520px; width: 100%; text-align: center; box-shadow: 0 20px 40px rgba(0,0,0,0.5); }
            .badge { display: inline-flex; align-items: center; gap: 0.5rem; background: rgba(239, 68, 68, 0.15); color: #f87171; border: 1px solid rgba(239, 68, 68, 0.3); padding: 0.35rem 0.85rem; border-radius: 9999px; font-weight: 700; font-size: 0.85rem; margin-bottom: 1.25rem; }
            h1 { font-size: 1.45rem; font-weight: 800; margin: 0 0 1rem 0; color: #f8fafc; }
            p { color: #94a3b8; font-size: 0.95rem; line-height: 1.6; margin: 0 0 1.5rem 0; }
            .ip-box { background: rgba(15, 23, 42, 0.8); border: 1px dashed rgba(239, 68, 68, 0.4); padding: 0.75rem 1rem; border-radius: 8px; font-family: monospace; color: #fca5a5; font-size: 1rem; margin-bottom: 1.5rem; }
            .btn { display: inline-block; background: #2563eb; color: #fff; text-decoration: none; padding: 0.75rem 1.5rem; border-radius: 8px; font-weight: 600; font-size: 0.9rem; transition: background 0.15s; }
            .btn:hover { background: #1d4ed8; }
          </style>
        </head>
        <body>
          <div class="card">
            <div class="badge">TRUY CẬP BỊ TỪ CHỐI (403)</div>
            <h1>Bảo Vệ Quản Trị Viên: IP Không Được Ủy Quyền</h1>
            <p>Tài khoản Quản trị viên chỉ cho phép truy cập từ địa chỉ IP được cấp phép riêng. Địa chỉ IP hiện tại của bạn không nằm trong danh sách trắng:</p>
            <div class="ip-box">IP HIỆN TẠI: ${escapeHtml(clientIp)}</div>
            <p style="font-size: 0.82rem; color: #64748b;">Dù tên tài khoản và mật khẩu quản trị chính xác, hệ thống vẫn từ chối mọi yêu cầu quản trị từ IP này.</p>
            <a href="/" class="btn">Quay về Trang chủ</a>
          </div>
        </body>
        </html>
      `);
    }

    if (!await hasVerifiedAdminSession(req)) {
      if (req.headers.accept && req.headers.accept.includes('application/json')) {
        res.writeHead(403, { 'Content-Type': 'application/json' });
        return res.end(JSON.stringify({ error: 'Từ chối truy cập: Quyền Quản trị viên (Role Admin/Teacher/Setter) là bắt buộc.' }));
      }
      res.writeHead(302, { 'Location': `/login?error=unauthorized&next=${encodeURIComponent(reqUrl)}` });
      return res.end();
    }
  }

  if (reqUrl === '/frontend/html/admin/judge/portal.html') {
    res.writeHead(302, { Location: '/admin/judge' });
    return res.end();
  }

  if (isJudgeRoute) {
    if (!isAdminIpAllowed(req)) {
      res.writeHead(403, { 'Content-Type': 'text/plain; charset=utf-8' });
      return res.end('Judge Admin IP restricted');
    }
    const pageReq = http.request({
      hostname: BACKEND_HOST, port: BACKEND_PORT, path: '/internal/judge-admin-page', method: 'GET',
      headers: {
        cookie: req.headers.cookie || '', host: `${BACKEND_HOST}:${BACKEND_PORT}`, accept: 'text/html',
        ...(BACKEND_PROXY_SCHEME ? { 'x-forwarded-proto': BACKEND_PROXY_SCHEME } : {})
      }
    }, pageRes => {
      res.writeHead(pageRes.statusCode, pageRes.headers);
      pageRes.pipe(res);
    });
    pageReq.on('error', () => {
      res.writeHead(502, { 'Content-Type': 'text/plain; charset=utf-8' });
      res.end('Judge Admin backend unavailable');
    });
    pageReq.end();
    return;
  }

  // Redirect legacy /admin/login to admin or main login
  if (lowerUrl === '/admin/login' || lowerUrl === '/frontend/html/admin/login.html') {
    if (await hasVerifiedAdminSession(req)) {
      res.writeHead(302, { 'Location': '/admin' });
      return res.end();
    }
    res.writeHead(302, { 'Location': '/login?next=%2Fadmin' });
    return res.end();
  }

  // Reverse proxy for Django backend API calls
  if (reqUrl.startsWith('/api/')) {
    const isV2Upload = /^\/api\/v2\/problem\/[^/]+\/testcases\/upload$/.test(reqUrl);
    const isV1Upload = /^\/api\/v1\/problems\/[^/]+\/testcases\/upload$/.test(reqUrl);
    const maxRequestBytes = isV2Upload ? 110 * 1024 * 1024 :
      isV1Upload ? 25 * 1024 * 1024 : 2 * 1024 * 1024;
    const declaredLength = Number(req.headers['content-length'] || 0);
    if (declaredLength > maxRequestBytes) {
      res.writeHead(413, { 'Content-Type': 'application/json', 'Connection': 'close' });
      return res.end(JSON.stringify({ error: 'REQUEST_TOO_LARGE' }));
    }
    const clientIp = getClientIp(req);
    // The gateway has already resolved the trusted client IP. Do not pass
    // caller supplied forwarding headers to Django's authentication endpoints.
    const forwardedFor = clientIp;

    const proxyHeaders = { ...req.headers };
    delete proxyHeaders['x-forwarded-proto'];
    const proxyReq = http.request({
      hostname: BACKEND_HOST,
      port: BACKEND_PORT,
      path: req.url,
      method: req.method,
      headers: { 
        ...proxyHeaders,
        'x-forwarded-for': forwardedFor,
        'x-real-ip': clientIp,
        host: `${BACKEND_HOST}:${BACKEND_PORT}`,
        ...(BACKEND_PROXY_SCHEME ? { 'x-forwarded-proto': BACKEND_PROXY_SCHEME } : {})
      }
    }, (proxyRes) => {
      proxyRes.on('end', () => liveSync.publish(req.method, reqUrl, proxyRes.statusCode));
      res.writeHead(proxyRes.statusCode, proxyRes.headers);
      proxyRes.pipe(res);
    });

    proxyReq.on('error', (err) => {
      console.error(`[API GATEWAY] Backend request failed (${req.method} ${reqUrl}): ${err.code || 'UPSTREAM_ERROR'}`);
      if (res.headersSent) return res.destroy();
      res.writeHead(502, {
        'Content-Type': 'application/json; charset=utf-8',
        'Cache-Control': 'no-store'
      });
      res.end(JSON.stringify({ error: 'API temporarily unavailable', code: 'UPSTREAM_UNAVAILABLE' }));
    });

    let receivedBytes = 0;
    req.on('data', chunk => {
      receivedBytes += chunk.length;
      if (receivedBytes > maxRequestBytes) {
        req.unpipe(proxyReq);
        proxyReq.destroy();
        if (!res.headersSent) {
          res.writeHead(413, { 'Content-Type': 'application/json', 'Connection': 'close' });
          res.end(JSON.stringify({ error: 'REQUEST_TOO_LARGE' }), () => req.destroy());
        }
      }
    });

    if (req.method === 'GET' || req.method === 'HEAD') {
      proxyReq.end();
    } else {
      req.pipe(proxyReq);
    }
    return;
  }

  // ─── Contest Admin dynamic routes (/admin/contests/:key/...) ─────────────
  const mCA_Dashboard      = reqUrl.match(/^\/admin\/contests\/([^\/]+)\/dashboard\/?$/);
  const mCA_Settings       = reqUrl.match(/^\/admin\/contests\/([^\/]+)\/settings\/?$/);
  const mCA_Problems       = reqUrl.match(/^\/admin\/contests\/([^\/]+)\/problems\/?$/);
  const mCA_Participants   = reqUrl.match(/^\/admin\/contests\/([^\/]+)\/participants\/?$/);
  const mCA_Submissions    = reqUrl.match(/^\/admin\/contests\/([^\/]+)\/submissions\/?$/);
  const mCA_Ranking        = reqUrl.match(/^\/admin\/contests\/([^\/]+)\/ranking\/?$/);
  const mCA_Announcements  = reqUrl.match(/^\/admin\/contests\/([^\/]+)\/announcements\/?$/);
  const mCA_Clarifications = reqUrl.match(/^\/admin\/contests\/([^\/]+)\/clarifications\/?$/);
  const mCA_Jury           = reqUrl.match(/^\/admin\/contests\/([^\/]+)\/jury\/?$/);
  const mCA_Reports        = reqUrl.match(/^\/admin\/contests\/([^\/]+)\/reports\/?$/);
  const mCA_AntiCheat      = reqUrl.match(/^\/admin\/contests\/([^\/]+)\/anti-cheat\/?$/);
  const mCA_Audit          = reqUrl.match(/^\/admin\/contests\/([^\/]+)\/audit\/?$/);
  const mCA_Base           = reqUrl.match(/^\/admin\/contests\/([^\/]+)\/?$/);
  const mCA_Portal         = reqUrl.match(/^\/admin\/contests\/?$/);

  if (mCA_Dashboard) {
    const [, key] = mCA_Dashboard;
    res.writeHead(302, { Location: `/frontend/html/contest-admin/dashboard/index.html?contest=${key}` });
    return res.end();
  } else if (mCA_Settings) {
    const [, key] = mCA_Settings;
    res.writeHead(302, { Location: `/frontend/html/contest-admin/settings/index.html?contest=${key}` });
    return res.end();
  } else if (mCA_Problems) {
    const [, key] = mCA_Problems;
    res.writeHead(302, { Location: `/frontend/html/contest-admin/problems/index.html?contest=${key}` });
    return res.end();
  } else if (mCA_Participants) {
    const [, key] = mCA_Participants;
    res.writeHead(302, { Location: `/frontend/html/contest-admin/participants/index.html?contest=${key}` });
    return res.end();
  } else if (mCA_Submissions) {
    const [, key] = mCA_Submissions;
    res.writeHead(302, { Location: `/frontend/html/contest-admin/submissions/index.html?contest=${key}` });
    return res.end();
  } else if (mCA_Ranking) {
    const [, key] = mCA_Ranking;
    res.writeHead(302, { Location: `/frontend/html/contest-admin/ranking/index.html?contest=${key}` });
    return res.end();
  } else if (mCA_Announcements) {
    const [, key] = mCA_Announcements;
    res.writeHead(302, { Location: `/frontend/html/contest-admin/announcements/index.html?contest=${key}` });
    return res.end();
  } else if (mCA_Clarifications) {
    const [, key] = mCA_Clarifications;
    res.writeHead(302, { Location: `/frontend/html/contest-admin/clarifications/index.html?contest=${key}` });
    return res.end();
  } else if (mCA_Jury) {
    const [, key] = mCA_Jury;
    res.writeHead(302, { Location: `/frontend/html/contest-admin/jury/index.html?contest=${key}` });
    return res.end();
  } else if (mCA_Reports) {
    const [, key] = mCA_Reports;
    res.writeHead(302, { Location: `/frontend/html/contest-admin/reports/index.html?contest=${key}` });
    return res.end();
  } else if (mCA_AntiCheat) {
    const [, key] = mCA_AntiCheat;
    // The create form is not a contest. Send this stale/mistyped URL to the
    // contest picker instead of treating "create" as a contest key.
    if (key.toLowerCase() === 'create') {
      res.writeHead(302, { Location: '/admin/anti-cheat' });
      return res.end();
    }
    res.writeHead(302, { Location: `/frontend/html/contest-admin/anti-cheat/index.html?contest=${key}` });
    return res.end();
  } else if (mCA_Audit) {
    const [, key] = mCA_Audit;
    res.writeHead(302, { Location: `/frontend/html/contest-admin/audit/index.html?contest=${key}` });
    return res.end();
  } else if (mCA_Base) {
    const [, key] = mCA_Base;
    res.writeHead(302, { Location: `/frontend/html/contest-admin/dashboard/index.html?contest=${key}` });
    return res.end();
  } else if (mCA_Portal) {
    res.writeHead(302, { Location: `/frontend/html/contest-admin/index.html` });
    return res.end();
  }

  // ─── Contest dynamic routes ───────────────────────────────────────────────
  // /contests/{slug}/problems/{letter}/submit
  const mContestProbSubmit = reqUrl.match(/^\/contests\/([^\/]+)\/problems\/([^\/]+)\/submit$/);
  // /contests/{slug}/problems/{letter}
  const mContestProb       = reqUrl.match(/^\/contests\/([^\/]+)\/problems\/([^\/]+)$/);
  // /contests/{slug}/problems
  const mContestProbs      = reqUrl.match(/^\/contests\/([^\/]+)\/problems$/);
  // /contests/{slug}/submissions/{id}
  const mContestSub        = reqUrl.match(/^\/contests\/([^\/]+)\/submissions\/(\d+)$/);
  // /contests/{slug}/submissions
  const mContestSubs       = reqUrl.match(/^\/contests\/([^\/]+)\/submissions$/);
  // /contests/{slug}/ranking
  const mContestRanking    = reqUrl.match(/^\/contests\/([^\/]+)\/ranking$/);
  // /contests/{slug}/announcements
  const mContestAnnounce   = reqUrl.match(/^\/contests\/([^\/]+)\/announcements$/);
  // /contests/{slug}/clarifications
  const mContestClarif     = reqUrl.match(/^\/contests\/([^\/]+)\/clarifications$/);
  // /contests/{slug}/submissions/{id}/code
  const mContestSubCode    = reqUrl.match(/^\/contests\/([^\/]+)\/submissions\/(\d+)\/code$/);
  // /contests/{slug}  (dashboard)
  const mContestDash       = reqUrl.match(/^\/contests\/([^\/]+)$/);

  if (mContestProbSubmit) {
    const [, slug, letter] = mContestProbSubmit;
    res.writeHead(302, { Location: `/frontend/html/contest/problem/submit.html?contest=${slug}&problem=${letter}` });
    return res.end();
  } else if (mContestProb) {
    const [, slug, letter] = mContestProb;
    res.writeHead(302, { Location: `/frontend/html/contest/problem/index.html?contest=${slug}&problem=${letter}` });
    return res.end();
  } else if (mContestProbs) {
    const [, slug] = mContestProbs;
    res.writeHead(302, { Location: `/frontend/html/contest/dashboard/problems.html?contest=${slug}` });
    return res.end();
  } else if (mContestSubCode) {
    const [, slug, id] = mContestSubCode;
    res.writeHead(302, { Location: `/frontend/html/contest/submission/code.html?contest=${slug}&id=${id}` });
    return res.end();
  } else if (mContestSub) {
    const [, slug, id] = mContestSub;
    res.writeHead(302, { Location: `/frontend/html/contest/submission/result.html?contest=${slug}&id=${id}` });
    return res.end();
  } else if (mContestSubs) {
    const [, slug] = mContestSubs;
    res.writeHead(302, { Location: `/frontend/html/contest/dashboard/submissions.html?contest=${slug}` });
    return res.end();
  } else if (mContestRanking) {
    const [, slug] = mContestRanking;
    res.writeHead(302, { Location: `/frontend/html/contest/dashboard/ranking.html?contest=${slug}` });
    return res.end();
  } else if (mContestAnnounce) {
    const [, slug] = mContestAnnounce;
    res.writeHead(302, { Location: `/frontend/html/contest/dashboard/announcements.html?contest=${slug}` });
    return res.end();
  } else if (mContestClarif) {
    const [, slug] = mContestClarif;
    res.writeHead(302, { Location: `/frontend/html/contest/dashboard/clarifications.html?contest=${slug}` });
    return res.end();
  } else if (mContestDash) {
    const [, slug] = mContestDash;
    res.writeHead(302, { Location: `/frontend/html/contest/dashboard/index.html?contest=${slug}` });
    return res.end();
  }
  // ─────────────────────────────────────────────────────────────────────────

  // ─── Profile dynamic routes ────────────────────────────────────────────────
  const mProfileSubmissions = reqUrl.match(/^\/profile\/([^\/]+)\/submissions$/);
  const mProfileContests    = reqUrl.match(/^\/profile\/([^\/]+)\/contests$/);
  const mProfileProblems    = reqUrl.match(/^\/profile\/([^\/]+)\/problems$/);
  const mProfileRating      = reqUrl.match(/^\/profile\/([^\/]+)\/rating$/);
  const mProfileOrgs        = reqUrl.match(/^\/profile\/([^\/]+)\/organizations$/);
  const mProfileAchieve     = reqUrl.match(/^\/profile\/([^\/]+)\/achievements$/);
  const mProfileActivity    = reqUrl.match(/^\/profile\/([^\/]+)\/activity$/);
  const mProfileBlog        = reqUrl.match(/^\/profile\/([^\/]+)\/blog$/);
  const mProfileSettings    = reqUrl.match(/^\/profile\/([^\/]+)\/settings$/);
  const mProfileOverview    = reqUrl.match(/^\/profile\/([^\/]+)\/overview$/);
  const mProfileBase        = reqUrl.match(/^\/profile\/([^\/]+)$/);

  if (mProfileSubmissions) {
    const [, username] = mProfileSubmissions;
    res.writeHead(302, { Location: `/frontend/html/profile/submissions.html?username=${username}` });
    return res.end();
  } else if (mProfileContests) {
    const [, username] = mProfileContests;
    res.writeHead(302, { Location: `/frontend/html/profile/contests.html?username=${username}` });
    return res.end();
  } else if (mProfileProblems) {
    const [, username] = mProfileProblems;
    res.writeHead(302, { Location: `/frontend/html/profile/problems.html?username=${username}` });
    return res.end();
  } else if (mProfileRating) {
    const [, username] = mProfileRating;
    res.writeHead(302, { Location: `/frontend/html/profile/rating.html?username=${username}` });
    return res.end();
  } else if (mProfileOrgs) {
    const [, username] = mProfileOrgs;
    res.writeHead(302, { Location: `/frontend/html/profile/organizations.html?username=${username}` });
    return res.end();
  } else if (mProfileAchieve) {
    const [, username] = mProfileAchieve;
    res.writeHead(302, { Location: `/frontend/html/profile/achievements.html?username=${username}` });
    return res.end();
  } else if (mProfileActivity) {
    const [, username] = mProfileActivity;
    res.writeHead(302, { Location: `/frontend/html/profile/activity.html?username=${username}` });
    return res.end();
  } else if (mProfileBlog) {
    const [, username] = mProfileBlog;
    res.writeHead(302, { Location: `/frontend/html/profile/blog.html?username=${username}` });
    return res.end();
  } else if (mProfileSettings) {
    const [, username] = mProfileSettings;
    res.writeHead(302, { Location: `/frontend/html/profile/settings.html?username=${username}` });
    return res.end();
  } else if (mProfileOverview || mProfileBase) {
    const username = (mProfileOverview || mProfileBase)[1];
    res.writeHead(302, { Location: `/frontend/html/profile/index.html?username=${username}` });
    return res.end();
  }

  // ─── Organization dynamic routes ───────────────────────────────────────────
  // Admin Routes:
  const mOrgAdminSettings     = reqUrl.match(/^\/organizations\/([^\/]+)\/admin\/settings\/?$/);
  const mOrgAdminMembers      = reqUrl.match(/^\/organizations\/([^\/]+)\/admin\/members\/?$/);
  const mOrgAdminRoles        = reqUrl.match(/^\/organizations\/([^\/]+)\/admin\/roles\/?$/);
  const mOrgAdminPermissions  = reqUrl.match(/^\/organizations\/([^\/]+)\/admin\/permissions\/?$/);
  const mOrgAdminContests     = reqUrl.match(/^\/organizations\/([^\/]+)\/admin\/contests\/?$/);
  const mOrgAdminProblems     = reqUrl.match(/^\/organizations\/([^\/]+)\/admin\/problems\/?$/);
  const mOrgAdminBlog         = reqUrl.match(/^\/organizations\/([^\/]+)\/admin\/blog\/?$/);
  const mOrgAdminAnnounce     = reqUrl.match(/^\/organizations\/([^\/]+)\/admin\/announcements\/?$/);
  const mOrgAdminInvitations  = reqUrl.match(/^\/organizations\/([^\/]+)\/admin\/invitations\/?$/);
  const mOrgAdminAuditLog     = reqUrl.match(/^\/organizations\/([^\/]+)\/admin\/audit-log\/?$/);
  const mOrgAdminBase         = reqUrl.match(/^\/organizations\/([^\/]+)\/admin\/?$/);

  // Public Routes:
  const mOrgOverview          = reqUrl.match(/^\/organizations\/([^\/]+)\/overview\/?$/);
  const mOrgMembers           = reqUrl.match(/^\/organizations\/([^\/]+)\/members\/?$/);
  const mOrgContestDetail     = reqUrl.match(/^\/organizations\/([^\/]+)\/contests\/([^\/]+)\/?$/);
  const mOrgContests          = reqUrl.match(/^\/organizations\/([^\/]+)\/contests\/?$/);
  const mOrgProblemDetail     = reqUrl.match(/^\/organizations\/([^\/]+)\/problems\/([^\/]+)\/?$/);
  const mOrgProblems          = reqUrl.match(/^\/organizations\/([^\/]+)\/problems\/?$/);
  const mOrgRanking           = reqUrl.match(/^\/organizations\/([^\/]+)\/ranking\/?$/);
  const mOrgBlogDetail        = reqUrl.match(/^\/organizations\/([^\/]+)\/blog\/(\d+)\/?$/);
  const mOrgBlog              = reqUrl.match(/^\/organizations\/([^\/]+)\/blog\/?$/);
  const mOrgAnnouncements     = reqUrl.match(/^\/organizations\/([^\/]+)\/announcements\/?$/);
  const mOrgActivity          = reqUrl.match(/^\/organizations\/([^\/]+)\/activity\/?$/);
  const mOrgBase              = reqUrl.match(/^\/organizations\/([^\/]+)\/?$/);

  if (mOrgAdminSettings) {
    const [, slug] = mOrgAdminSettings;
    res.writeHead(302, { Location: `/frontend/html/organization/admin/settings.html?org=${slug}` });
    return res.end();
  } else if (mOrgAdminMembers) {
    const [, slug] = mOrgAdminMembers;
    res.writeHead(302, { Location: `/frontend/html/organization/admin/members.html?org=${slug}` });
    return res.end();
  } else if (mOrgAdminRoles) {
    const [, slug] = mOrgAdminRoles;
    res.writeHead(302, { Location: `/frontend/html/organization/admin/roles.html?org=${slug}` });
    return res.end();
  } else if (mOrgAdminPermissions) {
    const [, slug] = mOrgAdminPermissions;
    res.writeHead(302, { Location: `/frontend/html/organization/admin/permissions.html?org=${slug}` });
    return res.end();
  } else if (mOrgAdminContests) {
    const [, slug] = mOrgAdminContests;
    res.writeHead(302, { Location: `/frontend/html/organization/admin/contests.html?org=${slug}` });
    return res.end();
  } else if (mOrgAdminProblems) {
    const [, slug] = mOrgAdminProblems;
    res.writeHead(302, { Location: `/frontend/html/organization/admin/problems.html?org=${slug}` });
    return res.end();
  } else if (mOrgAdminBlog) {
    const [, slug] = mOrgAdminBlog;
    res.writeHead(302, { Location: `/frontend/html/organization/admin/blog.html?org=${slug}` });
    return res.end();
  } else if (mOrgAdminAnnounce) {
    const [, slug] = mOrgAdminAnnounce;
    res.writeHead(302, { Location: `/frontend/html/organization/admin/announcements.html?org=${slug}` });
    return res.end();
  } else if (mOrgAdminInvitations) {
    const [, slug] = mOrgAdminInvitations;
    res.writeHead(302, { Location: `/frontend/html/organization/admin/invitations.html?org=${slug}` });
    return res.end();
  } else if (mOrgAdminAuditLog) {
    const [, slug] = mOrgAdminAuditLog;
    res.writeHead(302, { Location: `/frontend/html/organization/admin/audit-log.html?org=${slug}` });
    return res.end();
  } else if (mOrgAdminBase) {
    const [, slug] = mOrgAdminBase;
    res.writeHead(302, { Location: `/frontend/html/organization/admin/index.html?org=${slug}` });
    return res.end();
  } else if (mOrgContestDetail) {
    const [, slug, contest] = mOrgContestDetail;
    res.writeHead(302, { Location: `/contests/${contest}` });
    return res.end();
  } else if (mOrgProblemDetail) {
    const [, slug, problem] = mOrgProblemDetail;
    res.writeHead(302, { Location: `/problem?code=${problem}` });
    return res.end();
  } else if (mOrgBlogDetail) {
    const [, slug, id] = mOrgBlogDetail;
    res.writeHead(302, { Location: `/frontend/html/organization/blog-detail.html?org=${slug}&id=${id}` });
    return res.end();
  } else if (mOrgMembers) {
    const [, slug] = mOrgMembers;
    res.writeHead(302, { Location: `/frontend/html/organization/members.html?org=${slug}` });
    return res.end();
  } else if (mOrgContests) {
    const [, slug] = mOrgContests;
    res.writeHead(302, { Location: `/frontend/html/organization/contests.html?org=${slug}` });
    return res.end();
  } else if (mOrgProblems) {
    const [, slug] = mOrgProblems;
    res.writeHead(302, { Location: `/frontend/html/organization/problems.html?org=${slug}` });
    return res.end();
  } else if (mOrgRanking) {
    const [, slug] = mOrgRanking;
    res.writeHead(302, { Location: `/frontend/html/organization/ranking.html?org=${slug}` });
    return res.end();
  } else if (mOrgBlog) {
    const [, slug] = mOrgBlog;
    res.writeHead(302, { Location: `/frontend/html/organization/blog.html?org=${slug}` });
    return res.end();
  } else if (mOrgAnnouncements) {
    const [, slug] = mOrgAnnouncements;
    res.writeHead(302, { Location: `/frontend/html/organization/announcements.html?org=${slug}` });
    return res.end();
  } else if (mOrgActivity) {
    const [, slug] = mOrgActivity;
    res.writeHead(302, { Location: `/frontend/html/organization/activity.html?org=${slug}` });
    return res.end();
  } else if (mOrgOverview || mOrgBase) {
    const [, slug] = (mOrgOverview || mOrgBase);
    res.writeHead(302, { Location: `/frontend/html/organization/overview.html?org=${slug}` });
    return res.end();
  }


  // Redirect legacy profile link
  if (reqUrl === '/frontend/html/user/profile.html') {
    const u = new URLSearchParams(queryString).get('user') || '';
    res.writeHead(302, { Location: u ? `/profile/${u}` : '/profile' });
    return res.end();
  }

  // Redirect legacy ranking user link to main profile
  if (reqUrl === '/frontend/html/ranking/user-ranking.html' || reqUrl === '/ranking/user') {
    const u = new URLSearchParams(queryString).get('user') || new URLSearchParams(queryString).get('username') || '';
    res.writeHead(302, { Location: u ? `/profile/${u}` : '/ranking' });
    return res.end();
  }

  // Redirect removed ranking contest page to main ranking
  if (reqUrl === '/frontend/html/ranking/contest.html') {
    res.writeHead(302, { Location: '/ranking' });
    return res.end();
  }

  // Dynamic user link /users/:username or /user/:username -> /profile/:username
  const mUserRoute = reqUrl.match(/^\/(?:users|user)\/([^\/]+)$/);
  if (mUserRoute) {
    const username = mUserRoute[1];
    res.writeHead(302, { Location: `/profile/${username}` });
    return res.end();
  }
  // ─────────────────────────────────────────────────────────────────────────

  // Check aliases
  let mappedPath = ROUTE_ALIASES[reqUrl] || reqUrl;
  if (/^\/spectate\/[A-Za-z0-9_-]{20,64}$/.test(reqUrl)) {
    mappedPath = '/frontend/html/spectate/index.html';
  }

  // Dynamic route patterns
  const mSubDetail = reqUrl.match(/^\/(?:submissions|submission)\/(\d+)$/);
  if (mSubDetail) {
    const [, subId] = mSubDetail;
    res.writeHead(302, { Location: `/frontend/html/submissions/detail.html?id=${subId}` });
    return res.end();
  }

  // Problem Submit: /problem/{code}/submit or /problems/{code}/submit
  const mProbSubmit = reqUrl.match(/^\/(?:problem|problems)\/([a-zA-Z0-9_\-]+)\/submit$/);
  if (mProbSubmit) {
    const [, code] = mProbSubmit;
    res.writeHead(302, { Location: `/frontend/html/problem/submit.html?code=${code}` });
    return res.end();
  }

  // Problem Submissions: /problem/{code}/submissions or /problems/{code}/submissions
  const mProbSubs = reqUrl.match(/^\/(?:problem|problems)\/([a-zA-Z0-9_\-]+)\/submissions$/);
  if (mProbSubs) {
    const [, code] = mProbSubs;
    res.writeHead(302, { Location: `/frontend/html/submissions/index.html?problem=${code}` });
    return res.end();
  }

  // Problem Detail: /problem/{code} or /problems/{code}
  const mProbDetail = reqUrl.match(/^\/(?:problem|problems)\/([a-zA-Z0-9_\-]+)$/);
  if (mProbDetail) {
    const [, code] = mProbDetail;
    res.writeHead(302, { Location: `/frontend/html/problems/problem.html?code=${code}` });
    return res.end();
  }

  // Blog Detail: /blog/{slug}
  const mBlogDetail = reqUrl.match(/^\/blog\/([a-zA-Z0-9_\-]+)$/);
  if (mBlogDetail) {
    const [, slug] = mBlogDetail;
    res.writeHead(302, { Location: `/frontend/html/blog/detail.html?slug=${slug}` });
    return res.end();
  }

  if (/^\/submissions\/contest\/[^\/]+$/.test(reqUrl)) {
    mappedPath = '/frontend/html/submissions/contest-submissions.html';
  } else if (/^\/submit\/[^\/]+$/.test(reqUrl)) {
    const code = reqUrl.replace('/submit/', '');
    res.writeHead(302, { Location: `/frontend/html/problem/submit.html?code=${code}` });
    return res.end();
  }

  const FRONTEND_DIR = path.resolve(ROOT_DIR, 'frontend');
  const ALLOWED_ROOT_FILES = new Set(['/favicon.ico', '/robots.txt']);
  const lowerUrlPath = reqUrl.toLowerCase();

  // 1. Strict Path Traversal & Hidden File Protection (Defense against arbitrary file read / source leak)
  if (reqUrl.includes('\0') || reqUrl.includes('..') || /[\/\\]\./.test(reqUrl)) {
    res.writeHead(403, { 'Content-Type': 'text/plain; charset=utf-8' });
    return res.end('403 Forbidden: Invalid or restricted path.');
  }

  // 2. Prohibit source code, environment, database, log, config, and script extensions
  const FORBIDDEN_EXTENSIONS = [
    '.map', '.env', '.py', '.pyc', '.pyo', '.sqlite3', '.db', '.sql', '.bak', '.log',
    '.sh', '.bash', '.yml', '.yaml', '.toml', '.ini', '.conf', '.md', '.txt'
  ];
  if (FORBIDDEN_EXTENSIONS.some(ext => lowerUrlPath.endsWith(ext)) && !ALLOWED_ROOT_FILES.has(lowerUrlPath)) {
    res.writeHead(404, { 'Content-Type': 'text/plain; charset=utf-8' });
    return res.end('404 Not Found');
  }

  // 3. Resolve candidate paths strictly within FRONTEND_DIR (or allowed root files)
  const candidatePaths = [];

  if (ALLOWED_ROOT_FILES.has(lowerUrlPath)) {
    candidatePaths.push(path.join(ROOT_DIR, lowerUrlPath.slice(1)));
  }

  const cleanMapped = mappedPath.startsWith('/frontend/')
    ? mappedPath.substring('/frontend/'.length)
    : mappedPath.replace(/^\/+/, '');

  const cleanReq = reqUrl.startsWith('/frontend/')
    ? reqUrl.substring('/frontend/'.length)
    : reqUrl.replace(/^\/+/, '');

  candidatePaths.push(path.join(FRONTEND_DIR, cleanMapped));
  candidatePaths.push(path.join(FRONTEND_DIR, cleanReq));
  candidatePaths.push(path.join(FRONTEND_DIR, 'html', cleanReq));
  candidatePaths.push(path.join(FRONTEND_DIR, 'html', 'ranking', cleanReq.replace(/^ranking\/?/, '')));

  function tryServe(index) {
    if (index >= candidatePaths.length) {
      res.writeHead(404, { 'Content-Type': 'text/html; charset=utf-8' });
      return res.end(`
        <!DOCTYPE html>
        <html lang="vi">
        <head>
          <meta charset="UTF-8">
          <title>404 - Không tìm thấy trang</title>
          <style>
            body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; background: #0f172a; color: #f8fafc; text-align: center; padding: 5rem 1rem; }
            .card { max-width: 500px; margin: 0 auto; background: #1e293b; border-radius: 12px; padding: 2.5rem; border: 1px solid #334155; }
            h1 { font-size: 3rem; margin: 0 0 1rem 0; color: #ef4444; }
            p { color: #94a3b8; font-size: 1.1rem; }
            a { display: inline-block; margin-top: 1.5rem; padding: 0.75rem 1.5rem; background: #2563eb; color: #fff; text-decoration: none; border-radius: 8px; font-weight: 600; }
          </style>
        </head>
        <body>
          <div class="card">
            <h1>404</h1>
            <h2>Không tìm thấy trang</h2>
            <p>Đường dẫn <code>${escapeHtml(reqUrl)}</code> không tồn tại trên hệ thống.</p>
            <a href="/frontend/html/home/index.html">Quay về Trang chủ</a>
          </div>
        </body>
        </html>
      `);
    }

    const currentPath = candidatePaths[index];

    fs.stat(currentPath, (err, stats) => {
      if (err) {
        return tryServe(index + 1);
      }

      let targetFile = currentPath;
      if (stats.isDirectory()) {
        const indexHtml = path.join(currentPath, 'index.html');
        const listHtml = path.join(currentPath, 'list.html');
        if (fs.existsSync(indexHtml)) {
          targetFile = indexHtml;
        } else if (fs.existsSync(listHtml)) {
          targetFile = listHtml;
        } else {
          return tryServe(index + 1);
        }
      }

      // Canonical jail validation: targetFile MUST reside strictly inside FRONTEND_DIR or be allowed root file
      const resolvedTarget = path.resolve(targetFile);
      const isAllowedRoot = ALLOWED_ROOT_FILES.has(lowerUrlPath) && resolvedTarget === path.resolve(ROOT_DIR, lowerUrlPath.slice(1));
      const isInsideFrontend = resolvedTarget.startsWith(FRONTEND_DIR + path.sep);

      if (!isAllowedRoot && !isInsideFrontend) {
        // Prevent directory traversal or outside file leaks
        return tryServe(index + 1);
      }

      const ext = path.extname(targetFile).toLowerCase();
      const contentType = MIME_TYPES[ext];
      if (!contentType) {
        // Strict: never serve unwhitelisted files
        return tryServe(index + 1);
      }

      fs.realpath(targetFile, (realErr, realTarget) => {
        if (realErr) return tryServe(index + 1);
        const realInsideFrontend = realTarget.startsWith(FRONTEND_DIR + path.sep);
        const realAllowedRoot = isAllowedRoot && realTarget === resolvedTarget;
        if (!realInsideFrontend && !realAllowedRoot) return tryServe(index + 1);
        fs.stat(realTarget, (statErr, realStats) => {
          if (statErr || !realStats.isFile() || realStats.size > 2 * 1024 * 1024) {
            return tryServe(index + 1);
          }
          if (ext !== '.html') {
            const etag = `W/"${realStats.size.toString(16)}-${Math.trunc(realStats.mtimeMs).toString(16)}"`;
            res.setHeader('Cache-Control', 'no-cache');
            res.setHeader('ETag', etag);
            if (req.headers['if-none-match'] === etag) {
              res.writeHead(304);
              return res.end();
            }
          }
          fs.readFile(realTarget, (readErr, content) => {
        if (readErr) {
          return tryServe(index + 1);
        }

        // Security headers for static files
        res.setHeader('X-Content-Type-Options', 'nosniff');
        res.setHeader('X-Frame-Options', 'SAMEORIGIN');

        if (ext === '.html') {
          res.setHeader('Cache-Control', 'no-cache, no-store, must-revalidate');
          let html = content.toString('utf8');
          const coreInjections = `
  <link rel="icon" type="image/svg+xml" href="/frontend/assets/icons/favicon.svg">
  <link rel="stylesheet" href="/frontend/css/global/theme.css">
  <link rel="stylesheet" href="/frontend/css/global/icons.css">
  <script>
    (function(){
      try {
        var m = localStorage.getItem('cp_theme') || 'auto';
        var r = m;
        if (m === 'auto') {
          r = (window.matchMedia && window.matchMedia('(prefers-color-scheme: light)').matches) ? 'light' : 'dark';
        }
        document.documentElement.setAttribute('data-theme', r);
        document.documentElement.setAttribute('data-theme-mode', m);
        var l = localStorage.getItem('cp_lang') || 'vi';
        document.documentElement.lang = l;
      } catch(e){}
    })();
  </script>
  <script src="/frontend/js/core/icons.js"></script>
  <script src="/frontend/js/core/rating.js"></script>
  <script src="/frontend/js/core/theme.js"></script>
  <script src="/frontend/js/core/i18n.js"></script>`;

          if (!html.includes('/frontend/js/core/theme.js')) {
            if (html.includes('<head>')) {
              html = html.replace('<head>', '<head>' + coreInjections);
            } else if (html.includes('<HEAD>')) {
              html = html.replace('<HEAD>', '<HEAD>' + coreInjections);
            } else {
              html = coreInjections + '\n' + html;
            }
          }
          res.writeHead(200, { 'Content-Type': contentType });
          return res.end(html);
        }
        res.writeHead(200, { 'Content-Type': contentType });
        res.end(content);
          });
        });
      });
    });
  }

  tryServe(0);
});

const liveSync = createLiveSync(server, getClientIp);

server.on('upgrade', (request, socket, head) => {
  if (!/^\/ws\/submissions\/[1-9][0-9]*\/$/.test(request.url || '')) return;
  const origin = request.headers.origin;
  if (origin) {
    try {
      if (new URL(origin).host !== request.headers.host) { socket.destroy(); return; }
    } catch { socket.destroy(); return; }
  }
  const upstream = http.request({
    hostname: BACKEND_HOST,
    port: BACKEND_PORT,
    path: request.url,
    method: 'GET',
    headers: request.headers,
    timeout: 5000
  });
  upstream.on('upgrade', (response, backendSocket, backendHead) => {
    const headers = Object.entries(response.headers)
      .map(([name, value]) => `${name}: ${value}`).join('\r\n');
    socket.write(`HTTP/1.1 101 Switching Protocols\r\n${headers}\r\n\r\n`);
    if (backendHead.length) socket.write(backendHead);
    if (head.length) backendSocket.write(head);
    socket.pipe(backendSocket).pipe(socket);
    socket.on('error', () => backendSocket.destroy());
    backendSocket.on('error', () => socket.destroy());
  });
  upstream.on('response', () => socket.destroy());
  upstream.on('timeout', () => upstream.destroy());
  upstream.on('error', () => socket.destroy());
  upstream.end();
});

server.headersTimeout = 15000;
server.requestTimeout = 120000;
server.timeout = 120000;

server.on('error', (err) => {
  console.error('[FRONTEND SERVER ERROR]', err.message);
});

process.on('uncaughtException', (err) => {
  console.error('[UNCAUGHT EXCEPTION]', err && err.stack ? err.stack : err);
});

process.on('unhandledRejection', (reason, promise) => {
  console.error('[UNHANDLED REJECTION]', reason && reason.stack ? reason.stack : reason);
});

server.listen(PORT, () => {
  const listeningPort = server.address().port;
  console.log(`[FRONTEND SERVER] Active at http://localhost:${listeningPort} and http://127.0.0.1:${listeningPort}`);
  console.log(`[FRONTEND SERVER] Backend API target: http://${BACKEND_HOST}:${BACKEND_PORT}`);
});

module.exports = { server };
