/**
 * CodeProOJ Authentication & Session Helper
 */
const Auth = {
  getToken() { 
    return localStorage.getItem('token'); 
  },
  getUser() {
    try {
      const u = localStorage.getItem('user');
      return u ? JSON.parse(u) : null;
    } catch (e) {
      return null;
    }
  },
  setUser(user, token) {
    if (user) {
      localStorage.setItem('user', JSON.stringify(user));
      if (user.username) localStorage.setItem('username', user.username);
      const isUserAdmin = Boolean(user.is_admin || user.role === 'admin' || user.is_staff || user.is_superuser);
      localStorage.setItem('role', isUserAdmin ? 'admin' : (user.role || 'user'));
      if (isUserAdmin) {
        document.cookie = 'role=admin; path=/; max-age=86400; SameSite=Lax';
        document.cookie = 'is_admin=true; path=/; max-age=86400; SameSite=Lax';
      } else {
        document.cookie = 'role=user; path=/; max-age=86400; SameSite=Lax';
        document.cookie = 'is_admin=; path=/; max-age=0; expires=Thu, 01 Jan 1970 00:00:00 GMT';
        document.cookie = 'admin_token=; path=/; max-age=0; expires=Thu, 01 Jan 1970 00:00:00 GMT';
      }
    }
    if (token) localStorage.setItem('token', token);
    if (typeof initNavbar === 'function') {
      initNavbar();
    }
  },
  getUsername() {
    const u = this.getUser();
    return u?.username || localStorage.getItem('username') || '';
  },
  logout() {
    localStorage.removeItem('user');
    localStorage.removeItem('username');
    localStorage.removeItem('role');
    localStorage.removeItem('token');
    sessionStorage.clear();
    document.cookie = 'role=; path=/; max-age=0; expires=Thu, 01 Jan 1970 00:00:00 GMT';
    document.cookie = 'is_admin=; path=/; max-age=0; expires=Thu, 01 Jan 1970 00:00:00 GMT';
    document.cookie = 'admin_token=; path=/; max-age=0; expires=Thu, 01 Jan 1970 00:00:00 GMT';
    document.cookie = 'cp_session=; path=/; max-age=0; expires=Thu, 01 Jan 1970 00:00:00 GMT';
    window.location.href = '/frontend/html/auth/login.html';
  },
  isAuthenticated() { 
    return !!this.getToken(); 
  },
  canCreateOrganization() {
    const u = this.getUser();
    if (!u) return false;
    return u.is_staff === true || u.is_superuser === true || u.role === 'teacher';
  },
  requireAuth() {
    if (!this.isAuthenticated()) {
      window.location.href = `/frontend/html/auth/login.html?next=${encodeURIComponent(window.location.pathname + window.location.search)}`;
    }
  }
};
