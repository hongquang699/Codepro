/**
 * frontend/js/auth/auth.js
 * CodeProOJ Authentication Core Client Library
 */

const Auth = {
  API_BASE: '/api/v1/auth',

  async getCsrfToken() {
    let match = document.cookie.match(/(?:^|;\s*)csrftoken=([^;]+)/);
    if (!match) {
      await fetch(`${this.API_BASE}/me`, { credentials: 'include' });
      match = document.cookie.match(/(?:^|;\s*)csrftoken=([^;]+)/);
    }
    return match ? decodeURIComponent(match[1]) : '';
  },

  getRedirectUrl() {
    const params = new URLSearchParams(window.location.search);
    const next = params.get('next');
    if (!next) return '/';
    try {
      // Browsers treat "/\evil.com" as "//evil.com", so check the resolved origin, not the prefix.
      const url = new URL(next, window.location.origin);
      return url.origin === window.location.origin ? url.pathname + url.search + url.hash : '/';
    } catch {
      return '/';
    }
  },

  async getCurrentUser() {
    try {
      const res = await fetch(`${this.API_BASE}/me`, {
        credentials: 'include',
        headers: { 'Accept': 'application/json' }
      });
      if (!res.ok) return null;
      const data = await res.json();
      return data.authenticated ? data.user : null;
    } catch {
      return null;
    }
  },

  async logout() {
    try {
      const csrfToken = await this.getCsrfToken();
      await fetch(`${this.API_BASE}/logout`, {
        method: 'POST',
        credentials: 'include',
        headers: { 'Content-Type': 'application/json', 'X-CSRFToken': csrfToken }
      });
    } catch (e) {
      console.warn('Logout request failed:', e);
    } finally {
      localStorage.removeItem('user');
      localStorage.removeItem('username');
      localStorage.removeItem('role');
      localStorage.removeItem('token');
      sessionStorage.clear();
      document.cookie = 'role=; path=/; max-age=0; expires=Thu, 01 Jan 1970 00:00:00 GMT';
      document.cookie = 'is_admin=; path=/; max-age=0; expires=Thu, 01 Jan 1970 00:00:00 GMT';
      document.cookie = 'admin_token=; path=/; max-age=0; expires=Thu, 01 Jan 1970 00:00:00 GMT';
      document.cookie = 'cp_session=; path=/; max-age=0; expires=Thu, 01 Jan 1970 00:00:00 GMT';
      window.location.href = '/login';
    }
  },

  showAlert(containerId, message, type = 'error') {
    const el = document.getElementById(containerId);
    if (!el) return;
    el.textContent = message;
    el.className = `auth-alert ${type}`;
    el.style.display = 'block';
  },

  hideAlert(containerId) {
    const el = document.getElementById(containerId);
    if (!el) return;
    el.style.display = 'none';
  },

  togglePassword(inputId, toggleBtn) {
    const input = document.getElementById(inputId);
    if (!input) return;
    const isPassword = input.type === 'password';
    input.type = isPassword ? 'text' : 'password';

    // Update icon if using svg or span
    if (toggleBtn) {
      const eyeIcon = toggleBtn.querySelector('i') || toggleBtn;
      if (eyeIcon) {
        eyeIcon.setAttribute('data-icon', isPassword ? 'eye-slash' : 'eye');
        if (window.renderIcons) window.renderIcons();
      }
    }
  }
};

window.Auth = Auth;
