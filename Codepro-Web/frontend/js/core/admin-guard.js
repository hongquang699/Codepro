/**
 * CodeProOJ - Admin Route Guard
 * Checks the current server session for system administrator privileges.
 * Does NOT require re-entering credentials if already logged in as admin.
 */
(() => {
  window.adminApiHeaders = function(contentType) {
    const headers = contentType ? { 'Content-Type': contentType } : {};
    const token = localStorage.getItem('token');
    const csrf = document.cookie.match(/(?:^|;\s*)csrftoken=([^;]+)/);
    if (token) headers.Authorization = `Token ${token}`;
    if (csrf) headers['X-CSRFToken'] = decodeURIComponent(csrf[1]);
    return headers;
  };

  function checkAdminPrivileges(u) {
    if (!u) return false;
    return u.is_staff === true || u.is_superuser === true;
  }

  function showForbiddenModal(username) {
    const existing = document.getElementById('adminForbiddenOverlay');
    if (existing) return;

    const overlay = document.createElement('div');
    overlay.id = 'adminForbiddenOverlay';
    overlay.style.cssText = `
      position: fixed; inset: 0; background: color-mix(in srgb, var(--color-card) 95%, transparent);
      backdrop-filter: blur(12px); display: flex; align-items: center;
      justify-content: center; z-index: 999999; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
      padding: 1rem;
    `;

    overlay.innerHTML = `
      <div style="background: var(--color-card); border: 1px solid #ef4444; border-radius: 16px; padding: 2.5rem; max-width: 460px; width: 100%; text-align: center; box-shadow: 0 25px 50px -12px rgba(0,0,0,0.7);">
        <div style="width: 56px; height: 56px; border-radius: 50%; background: rgba(239, 68, 68, 0.15); color: #f87171; display: inline-flex; align-items: center; justify-content: center; font-size: 28px; margin-bottom: 1.25rem;">
          &#9888;
        </div>
        <h2 style="color: #ffffff; font-size: 1.35rem; margin: 0 0 0.5rem 0;">Từ chối truy cập Quản trị</h2>
        <p style="color: var(--color-text-muted); font-size: 0.95rem; line-height: 1.5; margin: 0 0 1.5rem 0;">
          Tài khoản <strong id="adminForbiddenUsername"></strong> chưa có quyền quản trị hệ thống.
        </p>
        <div style="display: flex; gap: 0.75rem; justify-content: center;">
          <a href="/" style="flex: 1; padding: 0.75rem 1rem; border-radius: 8px; background: var(--color-surface-hover); color: #fff; text-decoration: none; font-weight: 500; font-size: 0.9rem;">
            Về Trang chủ
          </a>
          <a href="/login?next=${encodeURIComponent(window.location.pathname + window.location.search)}" style="flex: 1; padding: 0.75rem 1rem; border-radius: 8px; background: #dc2626; color: #fff; text-decoration: none; font-weight: 500; font-size: 0.9rem;">
            Đổi tài khoản Admin
          </a>
        </div>
      </div>
    `;

    overlay.querySelector('#adminForbiddenUsername').textContent = `@${username || 'hiện tại'}`;

    document.body.appendChild(overlay);
  }

  function redirectToLogin() {
    const nextUrl = encodeURIComponent(window.location.pathname + window.location.search);
    window.location.replace(`/login?next=${nextUrl}`);
  }

  // Cached browser data can belong to an older account. Always check the current session.
  fetch('/api/v1/auth/me', {
    credentials: 'include',
    headers: { 'Accept': 'application/json' }
  })
  .then(res => {
    if (res.status === 401) {
      redirectToLogin();
      return null;
    }
    return res.json();
  })
  .then(data => {
    if (!data || !data.authenticated || !data.user) {
      redirectToLogin();
      return;
    }

    const u = data.user;
    try {
      const cached = JSON.parse(localStorage.getItem('user') || 'null');
      if (cached && cached.id !== u.id) localStorage.removeItem('token');
    } catch (e) {
      localStorage.removeItem('token');
    }
    localStorage.setItem('user', JSON.stringify(u));
    localStorage.setItem('username', u.username);
    localStorage.setItem('role', checkAdminPrivileges(u) ? 'admin' : (u.role || 'user'));
    window.__cpVerifiedUser = u;
    if (typeof window.initNavbar === 'function') window.initNavbar();

    if (!checkAdminPrivileges(u)) {
      showForbiddenModal(u.username);
    }
  })
  .catch(err => {
    console.warn('[AdminGuard] Could not verify session with server:', err);
    // A failed server check must not be replaced with cached privileges.
    redirectToLogin();
  });
})();
