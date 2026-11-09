function getTierClass(tier, rating) {
  if (typeof CPRating !== 'undefined') {
    return CPRating.getTierClass(tier, rating);
  }
  const r = parseInt(rating, 10);
  if (!isNaN(r) && r <= 0) {
    return 'tier-unrated';
  }
  const map = {
    'Legendary Grandmaster': 'tier-lgm',
    'Grandmaster': 'tier-gm',
    'International Master': 'tier-im',
    'Master': 'tier-m',
    'Candidate Master': 'tier-cm',
    'Expert': 'tier-exp',
    'Specialist': 'tier-spec',
    'Pupil': 'tier-pup',
    'Newbie': 'tier-new',
    'Unrated': 'tier-unrated'
  };
  return map[tier] || (r > 0 ? 'tier-new' : 'tier-unrated');
}

function escapeRankingHtml(value) {
  return String(value ?? '').replace(/[&<>"']/g, char => ({
    '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;'
  })[char]);
}

function rankingBadgeClass(value) {
  const badge = String(value ?? '').toLowerCase();
  return /^[a-z0-9-]{1,24}$/.test(badge) ? badge : 'new';
}

function renderRankingTable(items, tbodyId = 'rankingTableBody') {
  const tbody = document.getElementById(tbodyId);
  if (!tbody) return;

  if (!items || items.length === 0) {
    tbody.innerHTML = '<tr><td colspan="6" style="text-align: center; color: var(--color-text-muted); padding: 30px;">Không có dữ liệu xếp hạng.</td></tr>';
    return;
  }

  tbody.innerHTML = items.map(item => {
    let rankBadgeClass = 'standard';
    if (item.rank === 1) rankBadgeClass = 'top-1';
    else if (item.rank === 2) rankBadgeClass = 'top-2';
    else if (item.rank === 3) rankBadgeClass = 'top-3';

    const tierClass = getTierClass(item.tier, item.rating);
    const initial = (item.username || '?').charAt(0).toUpperCase();
    const e = escapeRankingHtml;
    const verifiedBadge = item.is_verified ? `
      <svg width="15" height="15" viewBox="0 0 24 24" fill="none" style="vertical-align:middle;margin-left:4px;display:inline-block;" title="Tài khoản đã xác minh (Tích xanh)">
        <path d="M9 12L11 14L15 10M12 3L13.91 4.26L16.14 3.73L17.55 5.48L19.78 5.74L20.31 7.97L22.06 9.38L21.53 11.61L22.79 13.52L21.53 15.43L22.06 17.66L20.31 19.07L19.78 21.3L17.55 21.56L16.14 23.31L13.91 22.78L12 24.04L10.09 22.78L7.86 23.31L6.45 21.56L4.22 21.3L3.69 19.07L1.94 17.66L2.47 15.43L1.21 13.52L2.47 11.61L1.94 9.38L3.69 7.97L4.22 5.74L6.45 5.48L7.86 3.73L10.09 4.26L12 3Z" fill="#38BDF8" stroke="#0284C7" stroke-width="1.2" stroke-linecap="round" stroke-linejoin="round"/>
        <path d="M8.5 12.5L11 15L16 9" stroke="white" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
      </svg>
    ` : '';

    return `
      <tr>
        <td>
          <span class="rank-badge ${rankBadgeClass}">${e(item.rank)}</span>
        </td>
        <td>
          <a href="/profile/${encodeURIComponent(item.username)}" class="user-cell" style="text-decoration: none; color: inherit;">
            <div class="user-avatar">${e(initial)}</div>
            <div>
              <span class="user-handle ${tierClass}" style="display:inline-flex;align-items:center;">
                ${e(item.username)} ${verifiedBadge}
              </span>
              ${item.school ? `<div class="user-school">${e(item.school)}</div>` : ''}
            </div>
          </a>
        </td>
        <td>
          <span class="${tierClass}" style="font-weight: 700;">${e(item.rating)}</span>
          <span class="rating-pill pill-${rankingBadgeClass(item.badge || ((item.rating === 0 || !item.rating) ? 'ur' : 'new'))}" style="margin-left: 6px;">${e(item.badge || ((item.rating === 0 || !item.rating) ? 'UR' : 'NEW'))}</span>
        </td>
        <td><strong>${e(item.solved)}</strong></td>
        <td><strong style="color: var(--color-primary);">${e(item.score)}</strong></td>
        <td>${e(item.country || 'Vietnam')}</td>
      </tr>
    `;
  }).join('');
}

function renderProblemScoreCell(probRes) {
  if (!probRes) return '<span class="score-empty">.</span>';
  if (probRes.solved) {
    const tries = probRes.tries > 1 ? ` +${escapeRankingHtml(Number(probRes.tries) - 1)}` : '+';
    const time = probRes.time != null ? `<div class="score-time">${escapeRankingHtml(probRes.time)}'</div>` : '';
    return `<div class="score-cell solved"><span class="score-tries">${tries}</span>${time}</div>`;
  }
  if (probRes.tries > 0) {
    return `<div class="score-cell failed"><span class="score-tries">-${escapeRankingHtml(probRes.tries)}</span></div>`;
  }
  return '<span class="score-empty">.</span>';
}

window.renderRankingTable = renderRankingTable;
window.getTierClass = getTierClass;
window.renderProblemScoreCell = renderProblemScoreCell;
window.escapeRankingHtml = escapeRankingHtml;
window.rankingBadgeClass = rankingBadgeClass;
