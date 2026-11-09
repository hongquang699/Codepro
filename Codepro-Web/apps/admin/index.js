/**
 * Coding Platform Admin Service & CLI Gateway
 */
const http = require('http');

console.log('====================================================');
console.log('   CodeProOJ ADMIN PLATFORM SERVICE & RUNTIME');
console.log('====================================================');
console.log('[APPS/ADMIN] Admin service active.');
console.log('[APPS/ADMIN] Management Console: https://codeprooj.com/admin (or http://localhost:8888/admin)');
console.log('[APPS/ADMIN] Monitoring Judge Cluster & Django Backend...');

// Periodic health monitor for admin dashboard metrics
setInterval(async () => {
  try {
    const req = http.get('http://127.0.0.1:8000/api/v2/system/health', (res) => {
      if (res.statusCode === 200) {
        // healthy
      }
    });
    req.on('error', () => {
      // Backend starting or offline
    });
  } catch (e) {}
}, 30000);

module.exports = {
  status: 'running',
  dashboardUrl: 'https://codeprooj.com/admin'
};
