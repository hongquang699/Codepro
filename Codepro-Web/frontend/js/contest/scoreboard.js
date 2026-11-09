/**
 * CodeProOJ Contest Scoreboard Logic
 * Connects to /api/v2/contest/<contest>/scoreboard
 *
 * Standings are keyed rows: a row that changes rank moves in place and keeps
 * the alert state (.rank-changed) until the visitor notices it.
 */

const SCOREBOARD_REFRESH_MS = 15000;
const rankMemory = new Map(); // user -> last rendered rank
let scoreboardTimer = null;

function escapeHtml(value) {
  return String(value ?? '').replace(/[&<>"']/g, char => ({
    '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;'
  })[char]);
}

function rowMarkup(s) {
  const h = escapeHtml;
  const top = s.rank >= 1 && s.rank <= 3 ? ` rank-top rank-${Number(s.rank)}` : '';
  return `
    <td class="rank-cell${top}">${h(s.rank)}</td>
    <td><a class="user-link" href="/profile/${encodeURIComponent(s.user)}">${h(s.user)}</a></td>
    <td class="score-cell">${h(s.score)}</td>
    <td class="penalty-cell">${h(s.penalty)} phút</td>
    <td><span class="badge badge-ac">Tham gia</span></td>
  `;
}

function markNoticed(row) {
  row.classList.remove('rank-changed');
  row.removeAttribute('data-change');
}

function renderStandings(tbody, standings, announce) {
  const reduceMotion = window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  const existing = new Map();
  tbody.querySelectorAll('tr[data-user]').forEach(tr => existing.set(tr.dataset.user, tr));

  // FLIP: remember where rows are before reordering.
  const before = new Map();
  existing.forEach((tr, user) => before.set(user, tr.getBoundingClientRect().top));

  const seen = new Set();
  const fragment = document.createDocumentFragment();
  standings.forEach(s => {
    const key = String(s.user);
    seen.add(key);
    let tr = existing.get(key);
    const previous = rankMemory.get(key);
    const isNew = !tr;
    if (isNew) {
      tr = document.createElement('tr');
      tr.dataset.user = key;
      tr.tabIndex = 0;
      ['pointerenter', 'focus', 'click'].forEach(evt =>
        tr.addEventListener(evt, () => markNoticed(tr)));
    }
    tr.innerHTML = rowMarkup(s);
    if (announce && previous !== undefined && previous !== s.rank) {
      tr.classList.add('rank-changed');
      tr.dataset.change = s.rank < previous ? 'up' : 'down';
      tr.setAttribute('aria-label', `${key}: hạng ${previous} thành ${s.rank}`);
    }
    rankMemory.set(key, s.rank);
    fragment.appendChild(tr);
  });
  existing.forEach((tr, user) => { if (!seen.has(user)) tr.remove(); });
  tbody.appendChild(fragment);

  if (reduceMotion) return;
  tbody.querySelectorAll('tr[data-user]').forEach(tr => {
    const from = before.get(tr.dataset.user);
    if (from === undefined) return;
    const delta = from - tr.getBoundingClientRect().top;
    if (!delta) return;
    tr.animate(
      [{ transform: `translateY(${delta}px)` }, { transform: 'translateY(0)' }],
      { duration: 420, easing: 'cubic-bezier(.2,.8,.2,1)' }
    );
  });
}

async function loadScoreboard(isRefresh) {
  const h = escapeHtml;
  const urlParams = new URLSearchParams(window.location.search);
  const contestKey = urlParams.get('contest') || 'weekly-01';

  const nameEl = document.getElementById('contestName');
  const tbody = document.getElementById('scoreboardBody');
  if (!tbody) return;

  const message = (text, tone) => {
    rankMemory.clear();
    tbody.innerHTML = `
      <tr>
        <td colspan="5" class="scoreboard-message ${tone || ''}">${text}</td>
      </tr>
    `;
  };

  try {
    const res = await api.get(`/contest/${encodeURIComponent(contestKey)}/scoreboard`);
    if (!res.success || !res.data) {
      message(`Không thể tải bảng điểm cho kỳ thi <code>${h(contestKey)}</code>.`, 'is-error');
      return;
    }

    const data = res.data;
    if (nameEl) nameEl.innerText = data.name || contestKey;

    const standings = data.standings || [];
    if (standings.length === 0) {
      message('Chưa có thí sinh nào tham gia kỳ thi này.');
      return;
    }

    if (tbody.querySelector('.scoreboard-message')) tbody.innerHTML = '';
    renderStandings(tbody, standings, Boolean(isRefresh));
  } catch (err) {
    message(`Lỗi: ${h(err.message)}`, 'is-error');
  }
}

function scheduleRefresh() {
  clearInterval(scoreboardTimer);
  scoreboardTimer = setInterval(() => {
    if (!document.hidden) loadScoreboard(true);
  }, SCOREBOARD_REFRESH_MS);
}

document.addEventListener('DOMContentLoaded', () => {
  loadScoreboard(false);
  scheduleRefresh();
});
