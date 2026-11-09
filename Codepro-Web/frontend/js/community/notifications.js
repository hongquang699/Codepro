/**
 * Notifications Logic
 */
document.addEventListener('DOMContentLoaded', () => {
  loadNotifications();
  setupReadAll();
});

async function loadNotifications() {
  const e = window.escapeCommunityHtml;
  const listEl = document.getElementById('notifsList');
  if (!listEl) return;

  try {
    const res = await CommunityAPI.getNotifications();
    if (!res || res.status !== 200) {
      listEl.innerHTML = '<div style="color: var(--color-text-muted);padding:2rem;">Không thể tải thông báo.</div>';
      return;
    }

    const notifs = res.data.objects || [];
    if (notifs.length === 0) {
      listEl.innerHTML = '<div style="color: var(--color-text-dim);padding:2rem;text-align:center;">Bạn không có thông báo mới nào.</div>';
      return;
    }

    listEl.innerHTML = notifs.map(n => {
      const icon = n.notification_type === 'comment' ? '💬' : (n.notification_type === 'reply' ? '↩️' : (n.notification_type === 'reaction' ? '👍' : '🔔'));
      const bg = n.is_read ? 'transparent' : 'rgba(59, 130, 246, 0.05)';
      return `
        <div style="padding:1rem;border-bottom: 1px solid rgba(255,255,255,0.05);background: ${bg};display:flex;align-items:flex-start;gap:0.75rem;">
          <div style="font-size:1.2rem;">${icon}</div>
          <div style="flex:1;">
            <div style="font-weight:700;color: #fff;font-size:0.92rem;margin-bottom:0.2rem;">${e(n.title)}</div>
            <div style="font-size:0.86rem;color: var(--color-text-secondary);line-height:1.4;">${e(n.message)}</div>
            <div style="font-size:0.75rem;color: var(--color-text-dim);margin-top:0.4rem;">${e(new Date(n.created_at).toLocaleString('vi-VN'))}</div>
          </div>
          ${window.communityLink(n.link) ? `<a href="${window.communityLink(n.link)}" class="comm-btn-primary" style="padding:0.3rem 0.75rem;font-size:0.78rem;">Xem</a>` : ''}
        </div>
      `;
    }).join('');

  } catch (err) {
    console.error('Notifications error:', err);
  }
}

function setupReadAll() {
  const btn = document.getElementById('btnReadAll');
  if (!btn) return;
  btn.addEventListener('click', async () => {
    try {
      await CommunityAPI.readAllNotifications();
      await loadNotifications();
    } catch (err) {
      console.error('Read all error:', err);
    }
  });
}
