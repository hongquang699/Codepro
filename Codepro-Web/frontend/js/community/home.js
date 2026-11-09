/**
 * Community Home Logic - Feed, Quick Post, Top Coders, Trending Threads
 */
document.addEventListener('DOMContentLoaded', () => {
  initCommunityHome();
});

async function initCommunityHome() {
  await loadFeed();
  setupQuickComposer();
}

async function loadFeed() {
  const e = window.escapeCommunityHtml;
  const feedContainer = document.getElementById('feedList');
  const trendingContainer = document.getElementById('trendingThreadsList');
  const topCodersContainer = document.getElementById('topCodersList');
  const upcomingContestsContainer = document.getElementById('upcomingContestsList');

  try {
    const res = await CommunityAPI.getFeed();
    if (!res || res.status !== 200) {
      feedContainer.innerHTML = '<div style="color: var(--color-text-muted);padding:2rem;">Không thể tải bài viết cộng đồng.</div>';
      return;
    }

    const { posts, trending_threads, top_coders, upcoming_contests } = res.data;

    // Render Posts Feed
    if (!posts || posts.length === 0) {
      feedContainer.innerHTML = '<div style="color: var(--color-text-muted);padding:2rem;">Chưa có bài viết nào. Hãy là người đầu tiên chia sẻ!</div>';
    } else {
      feedContainer.innerHTML = posts.map(p => renderPostCard(p)).join('');
    }

    // Render Trending Threads
    if (trendingContainer) {
      trendingContainer.innerHTML = (trending_threads || []).map(t => `
        <div style="padding:0.6rem 0;border-bottom: 1px solid rgba(255,255,255,0.05);">
          <a href="/frontend/html/community/forum/thread.html?id=${window.communityId(t.id)}" style="color: #fff;font-weight:600;font-size:0.88rem;text-decoration:none;display:block;line-height:1.4;">
            ${t.is_pinned ? '<span style="color: #fbbf24;">📌</span> ' : ''}${e(t.title)}
          </a>
          <div style="font-size:0.75rem;color: var(--color-text-dim);margin-top:0.25rem;">
            <span>${e(t.category_name)}</span> · <span>💬 ${e(t.reply_count)} phản hồi</span>
          </div>
        </div>
      `).join('') || '<div style="color: var(--color-text-dim);font-size:0.85rem;">Chưa có chủ đề nổi bật.</div>';
    }

    // Render Top Coders
    if (topCodersContainer) {
      topCodersContainer.innerHTML = (top_coders || []).map((u, idx) => {
        const uColor = (typeof CPRating !== 'undefined') ? CPRating.getColor(u.rating) : '#38bdf8';
        return `
          <div class="top-coder-row">
            <div class="top-coder-rank">#${idx + 1}</div>
            <div style="flex:1;">
              <a href="/profile/${encodeURIComponent(u.username)}" style="color: ${uColor};font-weight:700;font-size:0.88rem;text-decoration:none;">
                ${e(u.username)}
              </a>
              <div style="font-size:0.75rem;color: var(--color-text-muted);">${e(u.display_rank || 'Newbie')} · ${e(u.problem_count || 0)} bài AC</div>
            </div>
            <span style="font-size:0.8rem;font-weight:700;color: ${uColor};">${e(u.rating != null ? u.rating : 0)}</span>
          </div>
        `;
      }).join('');
    }

    // Render Upcoming Contests
    if (upcomingContestsContainer) {
      upcomingContestsContainer.innerHTML = (upcoming_contests || []).map(c => `
        <div style="padding:0.6rem 0;border-bottom: 1px solid rgba(255,255,255,0.05);">
          <a href="/frontend/html/contest/detail.html?key=${encodeURIComponent(c.key)}" style="color: #fff;font-weight:700;font-size:0.88rem;text-decoration:none;">
            ${e(c.name)}
          </a>
          <div style="font-size:0.75rem;color: #f59e0b;margin-top:0.2rem;">
            ⏱ Bắt đầu: ${e(new Date(c.start_time).toLocaleString('vi-VN'))}
          </div>
        </div>
      `).join('') || '<div style="color: var(--color-text-dim);font-size:0.85rem;">Hiện chưa có kỳ thi mới.</div>';
    }

  } catch (err) {
    console.error('Error loading community feed:', err);
  }
}

function renderPostCard(p) {
  const e = window.escapeCommunityHtml;
  const id = window.communityId(p.id);
  const rankClass = getRankClass(p.author_rank);
  const tagsHtml = (p.tags || []).map(t => `<a href="/frontend/html/community/feed/index.html?tag=${encodeURIComponent(t)}" class="comm-tag">#${e(t)}</a>`).join('');
  const dateFormatted = new Date(p.created_at).toLocaleDateString('vi-VN', { hour: '2-digit', minute: '2-digit', day: '2-digit', month: '2-digit' });

  return `
    <article class="comm-card" id="post-${id}">
      <div class="comm-card-header">
        <div class="comm-author-box">
          <div class="comm-avatar">${e(p.author_username.charAt(0).toUpperCase())}</div>
          <div>
            <div style="display:flex;align-items:center;gap:0.5rem;">
              <a href="/frontend/html/user/profile.html?u=${encodeURIComponent(p.author_username)}" class="comm-author-name">${e(p.author_username)}</a>
              <span class="comm-rank-badge ${rankClass}">${e(p.author_rank || 'Newbie')}</span>
            </div>
            <div class="comm-time-meta">${dateFormatted} ${p.is_pinned ? '· <strong style="color: #fbbf24;">📌 Ghim</strong>' : ''}</div>
          </div>
        </div>
      </div>

      <h2 class="comm-post-title">
        <a href="/frontend/html/community/posts/detail.html?id=${id}">${e(p.title)}</a>
      </h2>

      <div class="comm-post-content">
        ${e(p.summary || p.content.slice(0, 240) + '...')}
      </div>

      <div class="comm-tag-list">
        ${tagsHtml}
      </div>

      <div class="comm-action-bar">
        <button class="comm-btn-act" onclick="handleLikePost(${id})">
          <span id="likeIcon-${id}">👍</span> <span id="likeCount-${id}">${e(p.like_count || 0)}</span> Thích
        </button>
        <a href="/frontend/html/community/posts/detail.html?id=${id}#comments" class="comm-btn-act" style="text-decoration:none;">
          💬 ${e(p.comment_count || 0)} Bình luận
        </a>
        <a href="/frontend/html/community/posts/detail.html?id=${id}" class="comm-btn-act" style="text-decoration:none;">
          👁 ${e(p.view_count || 0)} Lượt xem
        </a>
      </div>
    </article>
  `;
}

function getRankClass(rank) {
  if (!rank) return 'rank-newbie';
  const r = String(rank).toLowerCase().replace(' ', '-');
  if (!/^[a-z0-9-]{1,32}$/.test(r)) return 'rank-newbie';
  return `rank-${r}`;
}

function setupQuickComposer() {
  const btn = document.getElementById('btnSubmitQuickPost');
  const titleInput = document.getElementById('quickPostTitle');
  const contentInput = document.getElementById('quickPostContent');

  if (!btn || !titleInput || !contentInput) return;

  btn.addEventListener('click', async () => {
    const title = titleInput.value.trim();
    const content = contentInput.value.trim();

    if (!title || !content) {
      alert('Vui lòng nhập đầy đủ tiêu đề và nội dung bài viết!');
      return;
    }

    btn.disabled = true;
    btn.textContent = 'Đang đăng...';

    try {
      const res = await CommunityAPI.createPost({ title, content });
      if (res && res.status === 201) {
        titleInput.value = '';
        contentInput.value = '';
        await loadFeed();
      } else {
        alert(res?.error?.message || 'Không thể đăng bài viết');
      }
    } catch (err) {
      alert('Lỗi: ' + err.message);
    } finally {
      btn.disabled = false;
      btn.textContent = 'Đăng bài';
    }
  });
}

window.handleLikePost = async function(postId) {
  try {
    const res = await CommunityAPI.toggleReaction('post', postId, 'like');
    if (res && res.status === 200) {
      const countEl = document.getElementById(`likeCount-${postId}`);
      if (countEl) countEl.textContent = res.data.reaction_count;
    }
  } catch (err) {
    console.error('Like error:', err);
  }
};
