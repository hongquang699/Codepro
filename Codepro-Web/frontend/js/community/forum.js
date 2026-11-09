/**
 * Forum logic - Load Categories and Threads
 */
document.addEventListener('DOMContentLoaded', () => {
  initForum();
});

async function initForum() {
  const e = window.escapeCommunityHtml;
  const catGrid = document.getElementById('forumCatGrid');
  const threadTableBdy = document.getElementById('forumThreadTbody');

  try {
    const catRes = await CommunityAPI.getCategories();
    if (catRes && catRes.status === 200 && catGrid) {
      catGrid.innerHTML = catRes.data.objects.map(c => `
        <a href="/frontend/html/community/forum/category.html?slug=${encodeURIComponent(c.slug)}" class="forum-cat-card">
          <div>
            <div class="forum-cat-title">
              <span>💬</span> ${e(c.name)}
            </div>
            <div class="forum-cat-desc">${e(c.description)}</div>
          </div>
          <div class="forum-cat-meta">
            <span>📝 ${e(c.thread_count || 0)} chủ đề</span>
            <span>💬 ${e(c.post_count || 0)} phản hồi</span>
          </div>
        </a>
      `).join('');
    }

    const threadRes = await CommunityAPI.getThreads();
    if (threadRes && threadRes.status === 200 && threadTableBdy) {
      if (threadRes.data.objects.length === 0) {
        threadTableBdy.innerHTML = '<tr><td colspan="5" style="text-align:center;padding:2rem;color: var(--color-text-dim);">Chưa có chủ đề thảo luận nào.</td></tr>';
      } else {
        threadTableBdy.innerHTML = threadRes.data.objects.map(t => {
          const dateStr = new Date(t.last_activity_at).toLocaleDateString('vi-VN', {hour:'2-digit', minute:'2-digit'});
          return `
            <tr class="forum-thread-row">
              <td>
                <div style="display:flex;align-items:center;">
                  ${t.is_pinned ? '<span class="pinned-badge">GHIM</span>' : ''}
                  ${t.is_locked ? '<span class="locked-badge">KHÓA</span>' : ''}
                  <a href="/frontend/html/community/forum/thread.html?id=${window.communityId(t.id)}" class="forum-thread-title">${e(t.title)}</a>
                </div>
                <div style="font-size:0.78rem;color: var(--color-text-muted);margin-top:0.25rem;">
                  Tác giả: <a href="/frontend/html/user/profile.html?u=${encodeURIComponent(t.author_username)}" style="color: var(--color-primary);text-decoration:none;">${e(t.author_username)}</a>
                </div>
              </td>
              <td><span style="font-size:0.82rem;color: var(--color-text-muted);background: var(--color-card);padding:0.2rem 0.5rem;border-radius:4px;">${e(t.category_name)}</span></td>
              <td style="color: var(--color-text-secondary);font-weight:600;">${e(t.reply_count)}</td>
              <td style="color: var(--color-text-muted);">${e(t.view_count)}</td>
              <td style="font-size:0.8rem;color: var(--color-text-dim);">${e(dateStr)}</td>
            </tr>
          `;
        }).join('');
      }
    }
  } catch (err) {
    console.error('Forum load error:', err);
  }
}
