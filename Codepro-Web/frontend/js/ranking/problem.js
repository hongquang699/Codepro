async function loadProblemSolvers(problemCode = 'APLUS') {
  const e = window.escapeRankingHtml;
  try {
    const data = await window.ContestRankingApi.fetchProblemSolvers(problemCode, 50);
    const titleEl = document.getElementById('problemTitle');
    const subEl = document.getElementById('problemSubtitle');
    if (titleEl) titleEl.innerHTML = `<i class="fi fi-rr-bulb"></i> Top lời giải: ${e(data.problem_name)} (${e(data.problem_code)})`;
    if (subEl) subEl.innerText = `Tổng số lượt giải Accepted: ${data.total_ac}`;

    const tbody = document.getElementById('problemSolversBody');
    if (!tbody) return;

    if (!data.solvers || data.solvers.length === 0) {
      tbody.innerHTML = '<tr><td colspan="7" style="text-align: center; color: var(--color-text-muted); padding: 40px;">Chưa có bài giải nào được chấp nhận.</td></tr>';
      return;
    }

    tbody.innerHTML = data.solvers.map(s => {
      let badgeCls = 'standard';
      if (s.rank === 1) badgeCls = 'top-1';
      else if (s.rank === 2) badgeCls = 'top-2';
      else if (s.rank === 3) badgeCls = 'top-3';

      const tierCls = window.getTierClass ? window.getTierClass(s.tier, s.rating) : ((s.rating === 0 || !s.rating) ? 'tier-unrated' : 'tier-new');

      return `
        <tr>
          <td><span class="rank-badge ${badgeCls}">${e(s.rank)}</span></td>
          <td>
            <a href="/profile/${encodeURIComponent(s.username)}" class="user-handle ${tierCls}">
              ${e(s.username)}
            </a>
          </td>
          <td><strong class="${tierCls}">${e(s.rating)}</strong></td>
          <td><strong style="color: #10b981;">${e(s.time)}s</strong></td>
          <td>${e(s.memory)} KB</td>
          <td><code>${e(s.language)}</code></td>
          <td style="color: var(--color-text-muted); font-size: 13px;">${e(s.date)}</td>
        </tr>
      `;
    }).join('');
  } catch (err) {
    const tbody = document.getElementById('problemSolversBody');
    if (tbody) {
      tbody.innerHTML = `<tr><td colspan="7" style="text-align: center; color: #ef4444; padding: 30px;">Lỗi: ${e(err.message)}</td></tr>`;
    }
  }
}

document.addEventListener('DOMContentLoaded', () => {
  const urlParams = new URLSearchParams(window.location.search);
  const code = urlParams.get('code') || 'APLUS';
  const inputEl = document.getElementById('problemCodeInput');
  if (inputEl) inputEl.value = code;

  loadProblemSolvers(code);

  const btn = document.getElementById('loadProblemBtn');
  if (btn) {
    btn.addEventListener('click', () => {
      const c = inputEl ? inputEl.value.trim() : 'APLUS';
      loadProblemSolvers(c);
    });
  }
});

window.loadProblemSolvers = loadProblemSolvers;
