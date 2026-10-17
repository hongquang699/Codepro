/**
 * CodeProOJ - Adaptive Dynamic Navigation Bar Component
 * Features:
 * - Red brand badge [ </> ] CodeProOJ
 * - Admin link for authorized accounts
 * - Dual Theme Switcher (Auto / Light / Dark)
 * - Bilingual Language Switcher (VI / EN)
 * - Strict no-underline styling
 */

function escapeNavbarText(value) {
  return String(value).replace(/[&<>"']/g, char => ({
    '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;'
  })[char]);
}

function initNavbar() {
  const navbar = document.querySelector('.navbar');
  if (!navbar) return;

  let navContainer = navbar.querySelector('.nav-container');
  if (!navContainer) return;

  // Retrieve current user and auth state
  let user = null;
  try {
    const raw = localStorage.getItem('user');
    user = raw ? JSON.parse(raw) : null;
  } catch (e) {
    user = null;
  }
  user = window.__cpVerifiedUser || user;

  const token = localStorage.getItem('token');
  const rawRole = localStorage.getItem('role');
  const rawUsername = localStorage.getItem('username');
  if (!user && rawUsername) {
    user = { username: rawUsername, role: rawRole || 'user' };
  }
  const isAuth = !!user && !!(token || window.__cpVerifiedUser);
  const isAdmin = Boolean(user && (
    user.role === 'admin' ||
    user.is_staff === true ||
    user.is_superuser === true ||
    user.is_admin === true
  ));

  const currentPath = window.location.pathname.toLowerCase();

  // Standard Navigation Links
  const navItems = [
    { label: 'Trang chủ', key: 'nav.home', icon: 'home', href: '/', exactMatch: true },
    { label: 'Bài tập', key: 'nav.problems', icon: 'code', href: '/problems', match: ['/problems', '/frontend/html/problem', '/frontend/html/problems'] },
    { label: 'Cuộc thi', key: 'nav.contests', icon: 'trophy', href: '/contests', match: ['/contests', '/frontend/html/contest'] },
    { label: 'Tải Client', key: 'nav.client', icon: 'download', href: '/client', match: ['/client'] },
    { label: 'Xếp hạng', key: 'nav.rankings', icon: 'award', href: '/ranking', match: ['/ranking', '/frontend/html/ranking'] },
    { label: 'Tổ chức', key: 'nav.organizations', icon: 'shield', href: '/organizations', match: ['/organizations', '/frontend/html/organization'] },
    { label: 'Bài nộp', key: 'nav.submissions', icon: 'send', href: '/submissions', match: ['/submissions', '/frontend/html/submissions'] }
  ];

  const linksHtml = navItems.map(item => {
    let isActive = false;
    if (item.exactMatch) {
      isActive = currentPath === item.href;
    } else {
      const matchList = item.match || [item.href];
      isActive = matchList.some(m => currentPath.startsWith(m));
    }
    const iconSvg = (typeof CPIcons !== 'undefined' && item.icon) 
      ? CPIcons.get(item.icon, { size: 16 }) 
      : '';
    const translatedText = (typeof CPI18n !== 'undefined') ? CPI18n.t(item.key, item.label) : item.label;
    return `<li><a href="${item.href}" class="${isActive ? 'active' : ''}${item.key === 'nav.client' ? ' nav-client-link' : ''}" style="white-space: nowrap !important;">${iconSvg}<span data-i18n="${item.key}" class="nav-text" style="white-space: nowrap !important;">${translatedText}</span></a></li>`;
  }).join('');

  // Switchers (Theme and Language)
  const currentLang = (typeof CPI18n !== 'undefined') ? CPI18n.getLang() : 'vi';
  const switchersHtml = `
    <div class="nav-switchers">
      <button class="btn-nav-control cp-theme-toggle" id="themeToggleBtn" title="Chế độ hiển thị" onclick="window.CPTheme && window.CPTheme.cycleTheme()">
        <span class="theme-icon-wrap"></span>
      </button>
      <button class="btn-nav-control cp-lang-toggle" id="langToggleBtn" title="Chuyển ngôn ngữ" onclick="window.CPI18n && window.CPI18n.toggleLang()">
        <span class="lang-text">${currentLang.toUpperCase()}</span>
      </button>
    </div>
  `;

  // Auth Actions HTML
  let authHtml = '';
  if (isAuth && user) {
    const username = String(user.username || 'User');
    const safeUsername = escapeNavbarText(username);
    const avatarInitial = escapeNavbarText(Array.from(username)[0].toUpperCase());
    const logoutText = (typeof CPI18n !== 'undefined') ? CPI18n.t('nav.logout', 'Đăng xuất') : 'Đăng xuất';
    authHtml = `
      <div class="nav-account-actions">
        <a href="/profile/${encodeURIComponent(username)}"
           id="navUserProfileLink" class="nav-account-link"
           aria-label="Hồ sơ của ${safeUsername}" title="Hồ sơ của ${safeUsername}">
          <span class="nav-account-avatar" aria-hidden="true">${avatarInitial}</span>
          <span class="nav-account-name">${safeUsername}</span>
        </a>
        <button onclick="logoutUser()" class="btn-nav-control nav-logout-button" data-i18n="nav.logout">
          ${logoutText}
        </button>
      </div>
    `;
  } else {
    const loginText = (typeof CPI18n !== 'undefined') ? CPI18n.t('nav.login', 'Đăng nhập') : 'Đăng nhập';
    const registerText = (typeof CPI18n !== 'undefined') ? CPI18n.t('nav.register', 'Đăng ký') : 'Đăng ký';
    authHtml = `
      <div style="display: flex; align-items: center; gap: 0.5rem;">
        <a href="/frontend/html/auth/login.html" class="btn-nav-control" style="font-size: 0.88rem; font-weight: 600; padding: 0.35rem 0.75rem;" data-i18n="nav.login">${loginText}</a>
        <a href="/frontend/html/auth/register.html" class="btn-nav-control" style="background: var(--color-primary, #2563eb); color: #fff; font-size: 0.85rem; font-weight: 600; padding: 0.35rem 0.85rem; border-color: transparent;" data-i18n="nav.register">${registerText}</a>
      </div>
    `;
  }

  // Construct complete container HTML
  const adminText = (typeof CPI18n !== 'undefined') ? CPI18n.t('nav.admin', 'Quản trị') : 'Quản trị';
  navContainer.innerHTML = `
    <div class="nav-left-group">
      <a href="/" class="nav-brand">
        <img class="brand-badge-code" src="/frontend/assets/icons/favicon.svg" width="28" height="28" alt="">
        <span class="brand-text">CodeProOJ</span>
      </a>
      ${isAdmin ? `
        <a href="/admin/menu" class="nav-admin-link ${currentPath.startsWith('/admin') ? 'active' : ''}" id="navAdminMenuLink" style="display: inline-flex; align-items: center; gap: 6px; background: ${currentPath.startsWith('/admin') ? 'rgba(220, 38, 38, 0.35)' : 'rgba(220, 38, 38, 0.18)'}; color: ${currentPath.startsWith('/admin') ? '#ffffff' : '#fca5a5'}; border: 1px solid ${currentPath.startsWith('/admin') ? '#ef4444' : 'rgba(239, 68, 68, 0.4)'}; padding: 0.25rem 0.75rem; border-radius: 6px; font-weight: 700; text-decoration: none !important; white-space: nowrap !important; box-shadow: ${currentPath.startsWith('/admin') ? '0 0 12px rgba(220, 38, 38, 0.5)' : '0 2px 8px rgba(220, 38, 38, 0.2)'};" title="Menu Quản Trị Hệ Thống (Dành riêng cho Admin)">
          <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round" style="flex-shrink:0;"><rect x="3" y="3" width="7" height="7"/><rect x="14" y="3" width="7" height="7"/><rect x="14" y="14" width="7" height="7"/><rect x="3" y="14" width="7" height="7"/></svg>
          <span style="white-space: nowrap !important;">Menu Admin</span>
        </a>
      ` : ''}
    </div>

    <div class="nav-right-group">
      <ul class="nav-links">
        ${linksHtml}
      </ul>
      <div class="nav-actions">
        ${switchersHtml}
        ${authHtml}
      </div>
    </div>
  `;

  // Initialize icons and theme/lang buttons
  if (window.CPTheme) window.CPTheme.updateButtons();
  if (window.CPI18n) window.CPI18n.updateButtons();
  if (window.CPIcons) window.CPIcons.renderAll();

  // Keep the cached user profile in sync with the server.
  if (isAuth && user) {
    fetch('/api/v1/auth/me', { credentials: 'include', headers: { 'Accept': 'application/json' } })
      .then(r => r.ok ? r.json() : null)
      .then(res => {
        if (res && res.authenticated && res.user) {
          const freshRating = (res.user.rating != null && !isNaN(parseInt(res.user.rating, 10))) ? parseInt(res.user.rating, 10) : 0;
          user.rating = freshRating;
          try {
            const curRaw = localStorage.getItem('user');
            const curObj = curRaw ? JSON.parse(curRaw) : {};
            localStorage.setItem('user', JSON.stringify({ ...curObj, ...res.user, rating: freshRating }));
          } catch (e) {}
        }
      }).catch(() => {});
  }

  // Check and render Global Announcement Banner or Maintenance Notice
  fetch('/api/v2/admin/system').then(r => r.json()).then(res => {
    const data = res?.data || {};
    if (data.maintenance_mode) {
      const banner = document.createElement('div');
      banner.style.cssText = 'background: #b91c1c; color: #fff; text-align: center; padding: 0.65rem 1rem; font-size: 0.88rem; font-weight: 700; z-index: 9999; border-bottom: 2px solid #ef4444;';
      banner.innerHTML = '⚠️ HỆ THỐNG ĐANG TRONG CHẾ ĐỘ BẢO TRÌ NÂNG CẤP MÁY CHẤM. VUI LÒNG QUAY LẠI SAU.';
      document.body.prepend(banner);
    } else if (data.announcement_active && data.global_announcement) {
      const banner = document.createElement('div');
      banner.style.cssText = 'background: rgba(37, 99, 235, 0.15); border-bottom: 1px solid rgba(59, 130, 246, 0.3); color: #93c5fd; text-align: center; padding: 0.5rem 1rem; font-size: 0.85rem; font-weight: 600; display: flex; justify-content: center; align-items: center; gap: 0.5rem;';
      banner.innerHTML = `<span>📢</span> <span>${data.global_announcement}</span>`;
      navbar.insertAdjacentElement('afterend', banner);
    }
  }).catch(() => {});
}

window.logoutUser = function() {
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
};

// Initialize on DOM ready
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', initNavbar);
} else {
  initNavbar();
}
