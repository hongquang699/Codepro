/**
 * Groups / Clubs logic
 */
document.addEventListener('DOMContentLoaded', () => {
  loadGroups();
});

async function loadGroups() {
  const e = window.escapeCommunityHtml;
  const container = document.getElementById('groupsGrid');
  if (!container) return;

  try {
    const res = await CommunityAPI.getGroups();
    if (!res || res.status !== 200) {
      container.innerHTML = '<div style="color: var(--color-text-muted);padding:2rem;">Không thể tải danh sách nhóm.</div>';
      return;
    }

    const groups = res.data.objects || [];
    if (groups.length === 0) {
      container.innerHTML = '<div style="color: var(--color-text-dim);padding:2rem;">Chưa có nhóm nào được tạo.</div>';
      return;
    }

    container.innerHTML = groups.map(g => `
      <div class="comm-card" style="display:flex;flex-direction:column;justify-content:space-between;">
        <div>
          <div style="display:flex;align-items:center;gap:0.75rem;margin-bottom:0.85rem;">
            <div class="comm-avatar" style="background: var(--color-accent);font-size:1.1rem;">
              ${e(g.name.charAt(0).toUpperCase())}
            </div>
            <div>
              <h3 style="color: #fff;font-size:1.05rem;font-weight:700;margin:0;">${e(g.name)}</h3>
              <div style="font-size:0.75rem;color: var(--color-text-muted);">Trưởng nhóm: ${e(g.owner_username)}</div>
            </div>
          </div>
          <p style="font-size:0.86rem;color: var(--color-text-secondary);line-height:1.5;margin-bottom:1rem;">${e(g.description)}</p>
        </div>

        <div style="display:flex;justify-content:space-between;align-items:center;padding-top:0.75rem;border-top: 1px solid rgba(255,255,255,0.06);">
          <span style="font-size:0.82rem;color: #38bdf8;font-weight:600;">👥 ${e(g.member_count)} thành viên</span>
          <button class="comm-btn-primary" style="padding:0.4rem 0.85rem;font-size:0.8rem;" onclick="handleJoinGroup(${window.communityId(g.id)})">
            Tham gia
          </button>
        </div>
      </div>
    `).join('');

  } catch (err) {
    console.error('Error loading groups:', err);
  }
}

window.handleJoinGroup = async function(groupId) {
  try {
    const res = await CommunityAPI.joinGroup(groupId);
    if (res && res.status === 200) {
      alert(res.data.message || 'Đã tham gia nhóm!');
      await loadGroups();
    }
  } catch (err) {
    alert('Lỗi: ' + err.message);
  }
};
