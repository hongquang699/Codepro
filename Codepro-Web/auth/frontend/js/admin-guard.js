/**
 * CodeProOJ - Admin Route Guard
 * Checks account authentication and admin role (is_staff, is_superuser, admin/teacher/setter).
 * Does NOT require re-entering credentials if already logged in as admin.
 */
(() => {
  function checkAdminPrivileges(u) {
    if (!u) return false;
    return Boolean(
      u.is_staff === true ||
      u.is_superuser === true ||
      u.is_admin === true ||
      u.role === 'admin' ||
      u.role === 'teacher' ||
      u.role === 'setter' ||
      (u.username && u.username.toLowerCase() === 'admin')
    );
  }

  function showForbiddenModal(username) {
    const existing = document.getElementById('adminForbiddenOverlay');
    if (existing) return;

    const overlay = document.createElement('div');
    overlay.id = 'adminForbiddenOverlay';
    overlay.style.cssText = `
      position: fixed; inset: 0; background: rgba(11, 15, 25, 0.95);
      backdrop-filter: blur(12px); display: flex; align-items: center;
      justify-content: center; z-index: 999999; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
      padding: 1rem;
    `;

    overlay.innerHTML = `
      <div style="background: #1e293b; border: 1px solid #ef4444; border-radius: 16px; padding: 2.5rem; max-width: 460px; width: 100%; text-align: center; box-shadow: 0 25px 50px -12px rgba(0,0,0,0.7);">
        <div style="width: 56px; height: 56px; border-radius: 50%; background: rgba(239, 68, 68, 0.15); color: #f87171; display: inline-flex; align-items: center; justify-content: center; font-size: 28px; margin-bottom: 1.25rem;">
          &#9888;
        </div>
        <h2 style="color: #ffffff; font-size: 1.35rem; margin: 0 0 0.5rem 0;">Từ chối truy cập Quản trị</h2>
        <p style="color: #94a3b8; font-size: 0.95rem; line-height: 1.5; margin: 0 0 1.5rem 0;">
          Tài khoản <strong>@${username || 'hiện tại'}</strong> là tài khoản thí sinh / người dùng thông thường và không có quyền truy cập Control Center.
        </p>
        <div style="display: flex; gap: 0.75rem; justify-content: center;">
          <a href="/" style="flex: 1; padding: 0.75rem 1rem; border-radius: 8px; background: #334155; color: #fff; text-decoration: none; font-weight: 500; font-size: 0.9rem;">
            Về Trang chủ
          </a>
          <a href="/login?next=${encodeURIComponent(window.location.pathname + window.location.search)}" style="flex: 1; padding: 0.75rem 1rem; border-radius: 8px; background: #dc2626; color: #fff; text-decoration: none; font-weight: 500; font-size: 0.9rem;">
            Đổi tài khoản Admin
          </a>
        </div>
      </div>
    `;

    document.body.appendChild(overlay);
  }

  function redirectToLogin() {
    const nextUrl = encodeURIComponent(window.location.pathname + window.location.search);
    window.location.replace(`/login?next=${nextUrl}`);
  }

  function ensureAdminCookies() {
    document.cookie = 'role=admin; path=/; max-age=86400; SameSite=Lax';
    document.cookie = 'is_admin=true; path=/; max-age=86400; SameSite=Lax';
  }

  // 1. Fast local verification
  let localUser = null;
  try {
    const raw = localStorage.getItem('user');
    localUser = raw ? JSON.parse(raw) : null;
  } catch (e) {
    localUser = null;
  }

  if (localUser) {
    if (checkAdminPrivileges(localUser)) {
      // User is authenticated and has admin role: grant immediate access!
      ensureAdminCookies();
      return;
    } else {
      // User is logged in but not an admin: show forbidden
      document.addEventListener('DOMContentLoaded', () => {
        showForbiddenModal(localUser.username);
      });
      return;
    }
  }

  // 2. If no local user object, check active session via /api/v1/auth/me
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
    localStorage.setItem('user', JSON.stringify(u));

    if (checkAdminPrivileges(u)) {
      ensureAdminCookies();
    } else {
      showForbiddenModal(u.username);
    }
  })
  .catch(err => {
    console.warn('[AdminGuard] Could not verify session with server:', err);
    // If network fails and no cached user, redirect to login
    redirectToLogin();
  });
})();
