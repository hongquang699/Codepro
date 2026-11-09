/**
 * CodeProOJ Contest Admin Shared UI Controller
 */

const ContestAdminUI = {
  renderSidebar(activeSection = 'dashboard', contestKey) {
    const key = contestKey || ContestAdminAPI.getContestKey();
    const pathKey = encodeURIComponent(key);
    const htmlKey = String(key).replace(/[&<>"']/g, char => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' })[char]);
    const target = document.getElementById('caSidebarTarget');
    if (!target) return;

    const sections = [
      { id: 'dashboard', label: 'Bảng Điều Khiển (Dashboard)', icon: 'chart', path: `/admin/contests/${pathKey}/dashboard` },
      { id: 'settings', label: 'Cấu Hình & Lịch Thi', icon: 'settings', path: `/admin/contests/${pathKey}/settings` },
      { id: 'problems', label: 'Quản Lý Bài Tập', icon: 'edit', path: `/admin/contests/${pathKey}/problems` },
      { id: 'participants', label: 'Thí Sinh & Đội Thi', icon: 'users', path: `/admin/contests/${pathKey}/participants` },
      { id: 'submissions', label: 'Bài Nộp & Rejudge', icon: 'document', path: `/admin/contests/${pathKey}/submissions` },
      { id: 'ranking', label: 'Bảng Điểm & Freeze', icon: 'trophy', path: `/admin/contests/${pathKey}/ranking` },
      { id: 'announcements', label: 'Thông Báo Kỳ Thi', icon: 'bell', path: `/admin/contests/${pathKey}/announcements` },
      { id: 'clarifications', label: 'Hỏi Đáp (Clarification)', icon: 'bubble', path: `/admin/contests/${pathKey}/clarifications` },
      { id: 'jury', label: 'Cụm Máy Chấm (Jury)', icon: 'judge', path: `/admin/contests/${pathKey}/jury` },
      { id: 'reports', label: 'Báo Cáo & Thống Kê', icon: 'chart', path: `/admin/contests/${pathKey}/reports` },
      { id: 'anti-cheat', label: 'Bot Chống Gian Lận', icon: 'shield', path: `/admin/contests/${pathKey}/anti-cheat` },
      { id: 'audit', label: 'Nhật Ký Kiểm Toán (Audit)', icon: 'shield', path: `/admin/contests/${pathKey}/audit` },
    ];

    target.innerHTML = `
      <div class="ca-sidebar-brand">
        <svg width="28" height="28" viewBox="0 0 36 36" fill="none"><rect width="36" height="36" rx="8" fill="#3B82F6"/><path d="M12 12L7 20L12 28M24 12L29 20L24 28M19 10L17 30" stroke="white" stroke-width="2.5" stroke-linecap="round"/></svg>
        <div>
          <div class="ca-brand-title">Contest Admin <span class="ca-brand-badge">OJ</span></div>
          <div style="font-size:.68rem;color: var(--color-text-dim);font-family:monospace;">${htmlKey}</div>
        </div>
      </div>

      <div class="ca-sidebar-group">Quản trị kỳ thi</div>
      ${sections.map(s => `
        <a href="${s.path}" class="ca-nav-item ${activeSection === s.id ? 'active' : ''}">
          <cp-icon name="${s.icon}" size="sm"></cp-icon>
          <span>${s.label}</span>
        </a>
      `).join('')}

      <div style="margin-top:auto;padding-top:1.25rem;border-top: 1px solid var(--color-border-subtle);">
        <a href="/admin/menu" class="ca-nav-item" style="color: #fca5a5;font-weight:700;">
          <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round" style="margin-right:6px;"><rect x="3" y="3" width="7" height="7"/><rect x="14" y="3" width="7" height="7"/><rect x="14" y="14" width="7" height="7"/><rect x="3" y="14" width="7" height="7"/></svg>
          <span>Menu Quản Trị</span>
        </a>
        <a href="/contests/${pathKey}" target="_blank" class="ca-nav-item" style="color: var(--color-primary);">
          <cp-icon name="arrow-left" size="sm"></cp-icon>
          <span>Trang thi công khai &rarr;</span>
        </a>
        <a href="/admin/contests" class="ca-nav-item" style="color: var(--color-text-muted);font-size:.8rem;">
          <span>&larr; Đổi kỳ thi khác</span>
        </a>
      </div>
    `;
  },

  renderHeader(title, subtitle, extraButtons = '') {
    const target = document.getElementById('caHeaderTarget');
    if (!target) return;
    const key = ContestAdminAPI.getContestKey();
    const pathKey = encodeURIComponent(key);
    const htmlKey = String(key).replace(/[&<>"']/g, char => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' })[char]);

    target.innerHTML = `
      <div class="ca-topbar">
        <div class="ca-title-block">
          <h1>
            <span>${title}</span>
            <span class="ca-badge ca-badge-upcoming" id="caContestKeyBadge" style="font-family:monospace;">${htmlKey}</span>
            <span id="caContestStatusBadge" class="ca-badge ca-badge-running">LOADING</span>
          </h1>
          <div class="ca-subtitle">${subtitle || ''}</div>
        </div>
        <div class="ca-topbar-actions">
          <a href="/admin/menu" class="ca-btn ca-btn-secondary" style="border-color: rgba(239,68,68,0.4);color: #fca5a5;" title="Trở về Menu Quản Trị">
            ⊞ Menu Admin
          </a>
          ${extraButtons}
          <a href="/contests/${pathKey}" target="_blank" class="ca-btn ca-btn-secondary">
            👁️ Xem trang thi
          </a>
        </div>
      </div>
    `;
  },

  updateStatusBadge(status, isFrozen = false) {
    const el = document.getElementById('caContestStatusBadge');
    if (!el) return;
    if (isFrozen) {
      el.className = 'ca-badge ca-badge-frozen';
      el.innerHTML = '❄️ FROZEN';
      return;
    }
    if (status === 'RUNNING') {
      el.className = 'ca-badge ca-badge-running';
      el.innerHTML = '● RUNNING';
    } else if (status === 'UPCOMING') {
      el.className = 'ca-badge ca-badge-upcoming';
      el.innerHTML = '⏳ UPCOMING';
    } else {
      el.className = 'ca-badge ca-badge-finished';
      el.innerHTML = '✓ FINISHED';
    }
  }
};
