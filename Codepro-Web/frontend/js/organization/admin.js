/**
 * Organization Admin Shared UI & Controller
 */

const OrgAdmin = {
  renderSidebar(slug, activeSection = 'dashboard') {
    const target = document.getElementById('orgAdminSidebar');
    if (!target) return;
    const pathSlug = encodeURIComponent(slug);

    if (activeSection !== 'dashboard') {
      const main = document.querySelector('main');
      if (main) main.style.visibility = 'hidden';
      OrgAPI.getOrg(slug).then(response => {
        if (response.data?.can_manage === true) {
          if (main) main.style.visibility = '';
          return;
        }
        window.location.href = response.status === 404
          ? '/admin/menu'
          : `/organizations/${encodeURIComponent(slug)}`;
      });
    }

    const navItems = [
      { id: 'dashboard', label: 'Tổng quan (Dashboard)', icon: 'home', link: `/organizations/${pathSlug}/admin` },
      { id: 'settings', label: 'Cài đặt Tổ chức', icon: 'settings', link: `/organizations/${pathSlug}/admin/settings` },
      { id: 'members', label: 'Quản lý Thành viên', icon: 'users', link: `/organizations/${pathSlug}/admin/members` },
      { id: 'roles', label: 'Vai trò & Cấp bậc', icon: 'shield', link: `/organizations/${pathSlug}/admin/roles` },
      { id: 'permissions', label: 'Ma trận Phân quyền', icon: 'lock', link: `/organizations/${pathSlug}/admin/permissions` },
      { id: 'contests', label: 'Gán & Quản lý Cuộc thi', icon: 'trophy', link: `/organizations/${pathSlug}/admin/contests` },
      { id: 'problems', label: 'Gán & Quản lý Bài tập', icon: 'code', link: `/organizations/${pathSlug}/admin/problems` },
      { id: 'blog', label: 'Bài viết / Blog', icon: 'file-text', link: `/organizations/${pathSlug}/admin/blog` },
      { id: 'announcements', label: 'Thông báo Chính thức', icon: 'bell', link: `/organizations/${pathSlug}/admin/announcements` },
      { id: 'invitations', label: 'Lời mời Thành viên', icon: 'mail', link: `/organizations/${pathSlug}/admin/invitations` },
      { id: 'audit-log', label: 'Nhật ký Kiểm toán (Audit)', icon: 'activity', link: `/organizations/${pathSlug}/admin/audit-log` }
    ];

    target.innerHTML = `
      <div class="org-admin-sidebar">
        <div class="org-admin-sidebar-title">Quản trị Tổ chức</div>
        ${navItems.map(item => `
          <a href="${item.link}" class="org-admin-nav-item ${activeSection === item.id ? 'active' : ''}">
            <cp-icon name="${item.icon}" size="sm"></cp-icon>
            <span>${item.label}</span>
          </a>
        `).join('')}

        <div style="margin-top:1.5rem;padding-top:1rem;border-top: 1px solid var(--color-border-subtle);">
          <a href="/organizations/${pathSlug}" class="org-admin-nav-item" style="color: var(--color-primary);">
            <cp-icon name="arrow-left" size="sm"></cp-icon>
            <span>&larr; Xem trang công khai</span>
          </a>
        </div>
      </div>
    `;
  }
};
