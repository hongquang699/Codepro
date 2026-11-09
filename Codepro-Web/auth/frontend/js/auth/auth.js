/**
 * frontend/js/auth/auth.js
 * CodeProOJ Authentication Core Client Library
 */

const Auth = {
  API_BASE: '/api/v1/auth',

  getRedirectUrl() {
    const params = new URLSearchParams(window.location.search);
    const next = params.get('next');
    if (next && next.startsWith('/') && !next.startsWith('//')) {
      return next;
    }
    return '/';
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
      await fetch(`${this.API_BASE}/logout`, {
        method: 'POST',
        credentials: 'include',
        headers: { 'Content-Type': 'application/json' }
      });
    } catch (e) {
      console.warn('Logout request failed:', e);
    } finally {
      localStorage.removeItem('user');
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
