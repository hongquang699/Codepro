const { SecurityDefenseSystem } = require('../../apps/web/security');

describe('gateway client IP resolution', () => {
  const defense = new SecurityDefenseSystem();
  const fromProxy = (headers) => ({ socket: { remoteAddress: '127.0.0.1' }, headers });

  test('ignores a client-supplied CF-Connecting-IP (admin whitelist bypass)', () => {
    const req = fromProxy({ 'cf-connecting-ip': '127.0.0.1', 'x-real-ip': '203.0.113.9' });
    expect(defense.resolveClientIp(req)).toBe('203.0.113.9');
  });

  test('does not trust forwarded headers from an untrusted socket', () => {
    const req = { socket: { remoteAddress: '203.0.113.50' }, headers: { 'x-real-ip': '127.0.0.1' } };
    expect(defense.resolveClientIp(req)).toBe('203.0.113.50');
  });
});
