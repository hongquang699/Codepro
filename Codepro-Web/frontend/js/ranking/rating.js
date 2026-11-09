let currentPage = 1;
const pageSize = 50;

async function loadRatingLeaderboard(page = 1) {
  const e = window.escapeRankingHtml;
  currentPage = page;
  const tier = document.getElementById('tierFilter') ? document.getElementById('tierFilter').value : '';
  const search = document.getElementById('searchUser') ? document.getElementById('searchUser').value.trim() : '';

  try {
    const data = await window.RatingApi.fetchRatingLeaderboard({
      page: currentPage,
      page_size: pageSize,
      tier,
      search
    });

    const tbody = document.getElementById('ratingTableBody');
    if (!tbody) return;

    if (!data.items || data.items.length === 0) {
      tbody.innerHTML = '<tr><td colspan="6" style="text-align: center; color: var(--color-text-muted); padding: 30px;">Không có thí sinh nào trong danh mục này.</td></tr>';
      return;
    }

    tbody.innerHTML = data.items.map(item => {
      let badgeCls = 'standard';
      if (item.rank === 1) badgeCls = 'top-1';
      else if (item.rank === 2) badgeCls = 'top-2';
      else if (item.rank === 3) badgeCls = 'top-3';

      const tierCls = window.getTierClass ? window.getTierClass(item.tier, item.rating) : ((item.rating === 0 || !item.rating) ? 'tier-unrated' : 'tier-new');
      const initial = (item.username || '?').charAt(0).toUpperCase();

      return `
        <tr>
          <td><span class="rank-badge ${badgeCls}">${e(item.rank)}</span></td>
          <td>
            <a href="/profile/${encodeURIComponent(item.username)}" class="user-cell" style="text-decoration: none; color: inherit;">
              <div class="user-avatar">${e(initial)}</div>
              <div>
                <span class="user-handle ${tierCls}">
                  ${e(item.username)}
                </span>
              </div>
            </a>
          </td>
          <td><strong class="${tierCls}" style="font-size: 15px;">${e(item.rating)}</strong></td>
          <td><span style="color: var(--color-text-muted);">${e(item.max_rating)}</span></td>
          <td>
            <span class="rating-pill pill-${window.rankingBadgeClass(item.badge || ((item.rating === 0 || !item.rating) ? 'ur' : 'new'))}">${e(item.tier || 'Unrated')}</span>
          </td>
          <td><strong>${e(item.contests_count || 0)}</strong></td>
        </tr>
      `;
    }).join('');

    if (window.renderPagination) {
      window.renderPagination(data.total, currentPage, pageSize, 'loadRatingLeaderboard', 'rankingPagination');
    }
  } catch (err) {
    const tbody = document.getElementById('ratingTableBody');
    if (tbody) {
      tbody.innerHTML = `<tr><td colspan="6" style="text-align: center; color: #ef4444; padding: 30px;">Lỗi: ${e(err.message)}</td></tr>`;
    }
  }
}

document.addEventListener('DOMContentLoaded', () => {
  loadRatingLeaderboard(1);

  const tierFilter = document.getElementById('tierFilter');
  const searchUser = document.getElementById('searchUser');

  if (tierFilter) tierFilter.addEventListener('change', () => loadRatingLeaderboard(1));
  if (searchUser) {
    searchUser.addEventListener('keydown', (e) => {
      if (e.key === 'Enter') loadRatingLeaderboard(1);
    });
  }
});

window.loadRatingLeaderboard = loadRatingLeaderboard;
