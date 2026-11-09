/**
 * CodeProOJ - Enterprise Anti-DoS, Anti-DDoS, Anti-Bot & Fake IP Defense Engine (WAF)
 * Designed for Online Judge high-concurrency competitive programming platforms.
 */

const fs = require('fs');
const path = require('path');
const net = require('net');

const normalizeProxyIp = value => value.startsWith('::ffff:') ? value.substring(7) : (value === '::1' ? '127.0.0.1' : value);
const trustedProxyRules = (process.env.TRUSTED_PROXY_IPS || '127.0.0.1,::1,::ffff:127.0.0.1')
  .split(',').map(value => normalizeProxyIp(value.trim())).filter(Boolean);
function isTrustedProxy(remoteAddress) {
  const remote = normalizeProxyIp(remoteAddress || '');
  if (trustedProxyRules.includes(remote)) return true;
  if (net.isIP(remote) !== 4) return false;
  const toNumber = value => value.split('.').reduce((result, octet) => (result << 8) | Number(octet), 0) >>> 0;
  return trustedProxyRules.some(rule => {
    const [network, bitsText] = rule.split('/');
    const bits = Number(bitsText);
    if (net.isIP(network) !== 4 || !Number.isInteger(bits) || bits < 0 || bits > 32) return false;
    const mask = bits === 0 ? 0 : (0xffffffff << (32 - bits)) >>> 0;
    return (toNumber(remote) & mask) === (toNumber(network) & mask);
  });
}

// ── IP Validation & Sanitization Regex ──────────────────────────────────────
const IPV4_REGEX = /^(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$/;
const IPV6_REGEX = /^(([0-9a-fA-F]{1,4}:){7,7}[0-9a-fA-F]{1,4}|([0-9a-fA-F]{1,4}:){1,7}:|([0-9a-fA-F]{1,4}:){1,6}:[0-9a-fA-F]{1,4}|([0-9a-fA-F]{1,4}:){1,5}(:[0-9a-fA-F]{1,4}){1,2}|([0-9a-fA-F]{1,4}:){1,4}(:[0-9a-fA-F]{1,4}){1,3}|([0-9a-fA-F]{1,4}:){1,3}(:[0-9a-fA-F]{1,4}){1,4}|([0-9a-fA-F]{1,4}:){1,2}(:[0-9a-fA-F]{1,4}){1,5}|[0-9a-fA-F]{1,4}:((:[0-9a-fA-F]{1,4}){1,6})|:((:[0-9a-fA-F]{1,4}){1,7}|:)|fe80:(:[0-9a-fA-F]{0,4}){0,4}%[0-9a-zA-Z]{1,}|::(ffff(:0{1,4}){0,1}:){0,1}((25[0-5]|(2[0-4]|1{0,1}[0-9]){0,1}[0-9])\.){3,3}(25[0-5]|(2[0-4]|1{0,1}[0-9]){0,1}[0-9])|([0-9a-fA-F]{1,4}:){1,4}:((25[0-5]|(2[0-4]|1{0,1}[0-9]){0,1}[0-9])\.){3,3}(25[0-5]|(2[0-4]|1{0,1}[0-9]){0,1}[0-9]))$/;

// ── Malicious User-Agent Signatures ─────────────────────────────────────────
const BAD_USER_AGENTS = [
  'sqlmap', 'nikto', 'dirbuster', 'gobuster', 'acunetix',
  'masscan', 'nmap', 'zgrab', 'censys', 'shodan',
  'havij', 'pangolin', 'netsparker', 'w3af', 'burpsuite',
  'openvas', 'metasploit', 'qualys', 'hydra', 'medusa'
];

// ── Vulnerability Probe Paths (Triggers immediate Threat Ban) ────────────────
const PROBE_PATHS = [
  /\.env(\.|$)/i,
  /\.git(\/|$)/i,
  /\.aws(\/|$)/i,
  /wp-config\.php/i,
  /wp-login\.php/i,
  /xmlrpc\.php/i,
  /phpmyadmin/i,
  /pma/i,
  /adminer/i,
  /shell\.php/i,
  /eval-stdin/i,
  /etc\/passwd/i,
  /proc\/self/i,
  /actuator\/heapdump/i,
  /\.DS_Store$/i,
  /\.py[cod]?(\?|$)/i,
  /\.sqlite3?(\?|$)/i,
  /\.db(\?|$)/i,
  /\.sql(\?|$)/i,
  /\.bak(\?|$)/i,
  /package\.json(\?|$)/i,
  /package-lock\.json(\?|$)/i,
  /requirements\.txt(\?|$)/i,
  /docker-compose.*(\?|$)/i,
  /Dockerfile(\?|$)/i,
  /manage\.py(\?|$)/i,
  /\.map(\?|$)/i,
  /\/\.\./
];

class SecurityDefenseSystem {
  constructor() {
    this.mode = 'normal'; // 'normal' | 'high' | 'under_attack'
    this.ipHistory = new Map(); // ip -> { requests: [], violations: 0, lastSubmission: 0, lastAuth: 0 }
    this.jailedIps = new Map(); // ip -> { until: timestamp, reason: string, count: number }
    this.whitelist = new Set(['127.0.0.1', '::1', 'localhost', '::ffff:127.0.0.1']);
    this.blacklist = new Set();
    this.attackLogs = [];
    this.stats = {
      totalInspected: 0,
      blockedDDoS: 0,
      blockedBots: 0,
      blockedProbes: 0,
      blockedSpoofedIps: 0,
      activeJailedCount: 0
    };

    // Garbage collection of old sliding windows every 30s
    setInterval(() => this.cleanup(), 30000).unref();
  }

  /**
   * Determine and verify client IP with Anti-Spoofing checks.
   */
  resolveClientIp(req) {
    let rawIp = (req.socket?.remoteAddress || '').trim();
    if (rawIp.startsWith('::ffff:')) {
      rawIp = rawIp.substring(7);
    }

    // Only the local gateway/backend hop is trusted by default. Private network
    // addresses are not inherently proxies and must not be able to spoof headers.
    const isSocketTrusted = isTrustedProxy(req.socket?.remoteAddress);

    let candidateIp = rawIp;

    if (isSocketTrusted) {
      // CF-Connecting-IP is ignored: the reverse proxy forwards it untouched, so any client could
      // spoof 127.0.0.1 and pass the admin IP whitelist. Behind Cloudflare, have nginx set X-Real-IP.
      const xRealIp = req.headers['x-real-ip'];
      const xForwardedFor = req.headers['x-forwarded-for'];

      if (xRealIp && typeof xRealIp === 'string') {
        candidateIp = xRealIp.trim();
      } else if (xForwardedFor && typeof xForwardedFor === 'string') {
        // Take the client IP (first item before proxy hops)
        const parts = xForwardedFor.split(',');
        candidateIp = parts[0].trim();
      }
    }

    if (candidateIp.startsWith('::ffff:')) {
      candidateIp = candidateIp.substring(7);
    }

    // Strip port if present for IPv4 (e.g. 203.0.113.195:49152)
    if (candidateIp.includes(':') && candidateIp.split(':').length === 2 && !candidateIp.includes('::')) {
      candidateIp = candidateIp.split(':')[0];
    }

    // Standardize localhost
    if (candidateIp === 'localhost' || candidateIp === '::1') {
      candidateIp = '127.0.0.1';
    }

    // Validate using Node.js built-in net.isIP (returns 4 or 6) or fallback regex
    const ipType = net.isIP(candidateIp);
    if (ipType === 0 && !IPV4_REGEX.test(candidateIp) && !IPV6_REGEX.test(candidateIp)) {
      this.logAttack(candidateIp, 'FAKE_OR_MALFORMED_IP', req.url, req.headers['user-agent']);
      this.stats.blockedSpoofedIps++;
      return null; // Invalid IP rejected
    }

    return candidateIp;
  }

  /**
   * Inspect incoming request through the defense pipeline.
   * Returns: { allowed: boolean, status: number, message: string, ip: string }
   */
  inspect(req) {
    this.stats.totalInspected++;
    const ip = this.resolveClientIp(req);
    const now = Date.now();

    // 1. Rejected if IP is malformed/spoofed
    if (!ip) {
      return {
        allowed: false,
        status: 400,
        message: 'Yêu cầu bị từ chối: Địa chỉ IP không hợp lệ hoặc giả mạo (Anti-Spoofing Triggered).',
        ip: 'invalid'
      };
    }

    const url = req.url || '/';
    const userAgent = (req.headers['user-agent'] || '').toLowerCase();

    // 2. Exploit / Vulnerability Probe Check (Immediate Auto-Jail, applies to all)
    for (const pattern of PROBE_PATHS) {
      if (pattern.test(url)) {
        this.jailIp(ip, 'PROBE_EXPLOIT_PATH', 30 * 60 * 1000); // 30 minutes
        this.stats.blockedProbes++;
        this.logAttack(ip, 'PROBE_EXPLOIT_PATH', url, userAgent);
        return {
          allowed: false,
          status: 403,
          message: 'Phát hiện hành vi thăm dò lỗ hổng bảo mật. Địa chỉ IP đã bị phong tỏa.',
          ip
        };
      }
    }

    // 3. Bad User-Agent / Malicious Scanner Check
    for (const badAgent of BAD_USER_AGENTS) {
      if (userAgent.includes(badAgent)) {
        this.jailIp(ip, `MALICIOUS_SCANNER_${badAgent.toUpperCase()}`, 15 * 60 * 1000);
        this.stats.blockedBots++;
        this.logAttack(ip, 'MALICIOUS_SCANNER', url, userAgent);
        return {
          allowed: false,
          status: 403,
          message: 'Từ chối truy cập: Phát hiện công cụ quét bảo mật độc hại (Scanner detected).',
          ip
        };
      }
    }

    // 4. Permanent Blacklist check
    if (this.blacklist.has(ip)) {
      return {
        allowed: false,
        status: 403,
        message: 'Địa chỉ IP của bạn đã bị quản trị viên đưa vào danh sách đen vĩnh viễn.',
        ip
      };
    }

    // 5. Check Jailed IP (Temporary ban)
    const jail = this.jailedIps.get(ip);
    if (jail) {
      if (now < jail.until) {
        const remainingSec = Math.ceil((jail.until - now) / 1000);
        return {
          allowed: false,
          status: 429,
          headers: { 'Retry-After': remainingSec.toString() },
          message: `IP [${ip}] tạm thời bị chặn do nghi vấn tấn công (${jail.reason}). Mở khóa sau: ${remainingSec} giây.`,
          ip
        };
      } else {
        // Jail expired
        this.jailedIps.delete(ip);
      }
    }

    // 6. Whitelist bypass (trusted local loopback bypasses rate limit, but NOT exploit/scanners)
    if (this.whitelist.has(ip) && !req.headers['x-forwarded-for']) {
      return { allowed: true, ip };
    }

    // 7. Anti-Bot Browser Header Integrity (For web pages, not API calls)
    if (!url.startsWith('/api/') && req.method === 'GET' && !url.match(/\.(css|js|png|jpg|ico|svg|woff2?)$/i)) {
      // Automated bot without Accept header or suspicious blank User-Agent
      if (!userAgent || (!req.headers['accept'] && !userAgent.includes('curl'))) {
        this.stats.blockedBots++;
        this.logAttack(ip, 'SUSPICIOUS_HEADLESS_BOT', url, userAgent);
        return {
          allowed: false,
          status: 403,
          message: 'Trình duyệt của bạn không gửi đủ tiêu đề hợp lệ (Anti-Bot Verification Failed).',
          ip
        };
      }
    }

    // 8. Rate Limiting & DoS / DDoS Mitigation
    const isStatic = url.match(/\.(css|js|png|jpg|jpeg|gif|ico|svg|woff2?|map)$/i);
    const isSubmit = url.includes('/api/v2/submit') || url.includes('/api/v1/submissions');
    const isAuth = /^\/api\/(?:v1\/|v2\/)?auth\/(?:login|register)(?:[/?]|$)/.test(url);

    // Retrieve or initialize IP state
    let record = this.ipHistory.get(ip);
    if (!record) {
      record = { requests: [], violations: 0, lastSubmission: 0, lastAuth: 0 };
      this.ipHistory.set(ip, record);
    }

    // A) Sensitive Submission Flooding Prevention (Maximum 1 submission every 2 seconds)
    if (isSubmit && req.method === 'POST') {
      const elapsedSinceSub = now - record.lastSubmission;
      if (elapsedSinceSub < 2000) {
        this.stats.blockedDDoS++;
        this.logAttack(ip, 'SUBMISSION_SPAM_FLOOD', url, userAgent);
        return {
          allowed: false,
          status: 429,
          headers: { 'Retry-After': '2' },
          message: 'Bạn đang nộp bài quá nhanh. Vui lòng chờ ít nhất 2 giây giữa mỗi lần nộp bài.',
          ip
        };
      }
      record.lastSubmission = now;
    }

    // B) Sensitive Auth Brute Force Prevention (Max 5 attempts / 30 seconds)
    if (isAuth && req.method === 'POST') {
      const elapsedSinceAuth = now - record.lastAuth;
      if (elapsedSinceAuth < 3000) { // 3s cooldown between tries
        record.violations++;
        if (record.violations >= 5) {
          this.jailIp(ip, 'AUTH_BRUTE_FORCE_PROTECT', 10 * 60 * 1000);
          this.stats.blockedDDoS++;
          this.logAttack(ip, 'AUTH_BRUTE_FORCE', url, userAgent);
          return {
            allowed: false,
            status: 429,
            headers: { 'Retry-After': '600' },
            message: 'Đăng nhập sai quá nhiều lần. IP của bạn tạm thời bị khóa 10 phút.',
            ip
          };
        }
      }
      record.lastAuth = now;
    }

    // C) Sliding Window Request Rate Limiting
    // Keep requests within last 5 seconds
    const windowStart = now - 5000;
    record.requests = record.requests.filter(t => t > windowStart);
    record.requests.push(now);

    const reqCountIn5s = record.requests.length;

    // Define thresholds based on defense mode
    let maxAllowedIn5s = 100; // Normal mode: 20 req/s
    if (this.mode === 'high') {
      maxAllowedIn5s = isStatic ? 80 : 35; // 7 req/s for dynamic/API
    } else if (this.mode === 'under_attack') {
      maxAllowedIn5s = isStatic ? 40 : 15; // Extreme Cloudflare-like protection: 3 req/s
    }

    if (reqCountIn5s > maxAllowedIn5s) {
      record.violations++;
      this.stats.blockedDDoS++;

      // If continuous flooding exceeds 2x threshold -> auto jail
      if (reqCountIn5s > maxAllowedIn5s * 2 || record.violations >= 3) {
        const jailDuration = (this.mode === 'under_attack' ? 30 : 15) * 60 * 1000;
        this.jailIp(ip, 'DDOS_FLOOD_THRESHOLD_EXCEEDED', jailDuration);
        this.logAttack(ip, 'DDOS_FLOOD_ATTACK', url, userAgent);
        return {
          allowed: false,
          status: 429,
          headers: { 'Retry-After': '900' },
          message: `Lưu lượng truy cập bất thường từ IP [${ip}] (${reqCountIn5s} yêu cầu/5s). Đã kích hoạt cơ chế Anti-DDoS WAF.`,
          ip
        };
      }

      this.logAttack(ip, 'RATE_LIMIT_WARNING', url, userAgent);
      return {
        allowed: false,
        status: 429,
        headers: { 'Retry-After': '5' },
        message: 'Hệ thống phát hiện tần suất gửi yêu cầu quá cao (Rate Limit Exceeded). Vui lòng thử lại sau giây lát.',
        ip
      };
    }

    // Request Allowed
    return { allowed: true, ip };
  }

  /**
   * Apply Enterprise OWASP Security Headers.
   */
  applySecurityHeaders(res) {
    res.setHeader('X-Content-Type-Options', 'nosniff');
    res.setHeader('X-Frame-Options', 'SAMEORIGIN');
    res.setHeader('X-XSS-Protection', '1; mode=block');
    res.setHeader('Referrer-Policy', 'strict-origin-when-cross-origin');
    res.setHeader('Permissions-Policy', 'camera=(), microphone=(), geolocation=()');
    res.setHeader('X-DDoS-Protection', `Active Mode: ${this.mode.toUpperCase()}`);
  }

  /**
   * Jail an IP address for specified duration.
   */
  jailIp(ip, reason, durationMs = 15 * 60 * 1000) {
    this.jailedIps.set(ip, {
      until: Date.now() + durationMs,
      reason: reason,
      jailedAt: new Date().toISOString()
    });
    this.stats.activeJailedCount = this.jailedIps.size;
  }

  /**
   * Log security events for administrative auditing.
   */
  logAttack(ip, type, targetPath, userAgent) {
    const entry = {
      id: Date.now() + Math.random().toString(36).substr(2, 4),
      timestamp: new Date().toISOString(),
      ip: ip || 'unknown',
      type: type,
      path: (targetPath || '/').slice(0, 100),
      userAgent: (userAgent || '').slice(0, 80)
    };
    this.attackLogs.unshift(entry);
    if (this.attackLogs.length > 100) {
      this.attackLogs.pop();
    }
  }

  /**
   * Memory Cleanup for IP sliding windows.
   */
  cleanup() {
    const now = Date.now();
    const expiry = now - 15000;

    for (const [ip, record] of this.ipHistory.entries()) {
      record.requests = record.requests.filter(t => t > expiry);
      if (record.requests.length === 0 && now - record.lastSubmission > 60000 && now - record.lastAuth > 60000) {
        this.ipHistory.delete(ip);
      }
    }

    // Clean expired jails
    for (const [ip, jail] of this.jailedIps.entries()) {
      if (now >= jail.until) {
        this.jailedIps.delete(ip);
      }
    }
    this.stats.activeJailedCount = this.jailedIps.size;
  }

  /**
   * Admin Status Report.
   */
  getSecurityReport() {
    const now = Date.now();
    const activeJails = [];
    for (const [ip, jail] of this.jailedIps.entries()) {
      activeJails.push({
        ip,
        reason: jail.reason,
        jailedAt: jail.jailedAt,
        remainingSec: Math.max(0, Math.ceil((jail.until - now) / 1000))
      });
    }

    return {
      mode: this.mode,
      stats: {
        ...this.stats,
        activeJailedCount: this.jailedIps.size,
        trackedIpsCount: this.ipHistory.size,
        blacklistCount: this.blacklist.size,
        whitelistCount: this.whitelist.size
      },
      activeJails: activeJails,
      recentAttacks: this.attackLogs.slice(0, 25),
      blacklist: Array.from(this.blacklist),
      whitelist: Array.from(this.whitelist)
    };
  }
}

// Global Singleton Instance
const securityDefense = new SecurityDefenseSystem();

module.exports = {
  securityDefense,
  SecurityDefenseSystem
};
