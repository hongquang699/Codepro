async function loadRatingHistory(username = 'tourist_vn') {
  const e = window.escapeRankingHtml;
  try {
    const data = await window.RatingApi.fetchRatingHistory(username);
    const titleEl = document.getElementById('historyTitle');
    const subEl = document.getElementById('historySubtitle');
    if (titleEl) titleEl.innerHTML = `<i class="fi fi-rr-chart-line-up"></i> Lịch sử Rating: ${e(data.username)} (${e(data.rating)})`;
    if (subEl) subEl.innerText = `Danh hiệu: ${data.tier} | Kỷ lục Rating: ${data.max_rating} | Số kỳ thi: ${data.contests_participated}`;

    const tbody = document.getElementById('historyTableBody');
    if (!tbody) return;

    if (!data.history || data.history.length === 0) {
      tbody.innerHTML = '<tr><td colspan="8" style="text-align: center; color: var(--color-text-muted); padding: 40px;">Thí sinh này chưa tham gia kỳ thi tính rating nào.</td></tr>';
      renderChart([]);
      return;
    }

    tbody.innerHTML = data.history.map((h, idx) => {
      const deltaCls = h.rating_change > 0 ? 'rating-up' : (h.rating_change < 0 ? 'rating-down' : 'rating-neutral');
      const sign = h.rating_change > 0 ? '+' : '';
      return `
        <tr>
          <td>${idx + 1}</td>
          <td><strong>${e(h.contest_name)}</strong></td>
          <td><span class="rank-badge standard">${e(h.rank)}</span></td>
          <td style="color: var(--color-text-muted);">${e(h.old_rating)}</td>
          <td><strong>${e(h.new_rating)}</strong></td>
          <td><span class="${deltaCls}" style="font-weight: 700;">${sign}${e(h.rating_change)}</span></td>
          <td style="color: var(--color-primary);"><strong>${e(h.performance || '-')}</strong></td>
          <td style="color: var(--color-text-muted); font-size: 13px;">${e(h.date)}</td>
        </tr>
      `;
    }).join('');

    renderChart(data.history);

  } catch (err) {
    const tbody = document.getElementById('historyTableBody');
    if (tbody) {
      tbody.innerHTML = `<tr><td colspan="8" style="text-align: center; color: #ef4444; padding: 30px;">Lỗi: ${e(err.message)}</td></tr>`;
    }
  }
}

function renderChart(history) {
  const container = document.getElementById('chartContainer');
  if (!container) return;

  if (!history || history.length === 0) {
    container.innerHTML = `
      <div style="display:flex;flex-direction:column;align-items:center;justify-content:center;height:200px;color: var(--color-text-muted);gap:0.5rem;">
        <span style="font-size:2.5rem;font-weight:900;color: var(--color-text-dim);font-family:monospace;">0</span>
        <span style="color: var(--color-text-secondary);font-weight:600;">Chưa có dữ liệu biến động Rating</span>
        <span style="color: var(--color-text-dim);font-size:0.85rem;">Rating ban đầu là 0 (Unrated). Biểu đồ sẽ xuất hiện sau kỳ thi có tính rate đầu tiên.</span>
      </div>
    `;
    return;
  }

  const width = 800;
  const height = 240;
  const pad = 40;

  const ratings = history.map(h => Number(h.new_rating) || 0);
  const minR = Math.max(0, Math.min(...ratings) - 150);
  const maxR = Math.max(...ratings) + 150;

  const points = history.map((h, i) => {
    const x = history.length === 1 ? width / 2 : pad + (i / (history.length - 1)) * (width - 2 * pad);
    const rating = Number(h.new_rating) || 0;
    const y = height - pad - ((rating - minR) / (maxR - minR)) * (height - 2 * pad);
    return { x, y, rating, contest: h.contest_name };
  });

  const polylinePoints = points.map(p => `${p.x},${p.y}`).join(' ');

  let svg = `
    <svg viewBox="0 0 ${width} ${height}" class="chart-svg" style="overflow: visible;">
      <!-- Grid Lines -->
      <line x1="${pad}" y1="${height - pad}" x2="${width - pad}" y2="${height - pad}" stroke="#334155" stroke-dasharray="4"/>
      <line x1="${pad}" y1="${pad}" x2="${width - pad}" y2="${pad}" stroke="#334155" stroke-dasharray="4"/>
      
      <!-- Polyline -->
      <polyline fill="none" stroke="#3b82f6" stroke-width="3" stroke-linecap="round" stroke-linejoin="round" points="${polylinePoints}" />
  `;

  // Draw Points
  for (const p of points) {
    svg += `
      <circle cx="${p.x}" cy="${p.y}" r="6" fill="#fbbf24" stroke="#1e293b" stroke-width="2">
        <title>${window.escapeRankingHtml(p.contest)}: ${p.rating}</title>
      </circle>
      <text x="${p.x}" y="${p.y - 12}" fill="#f1f5f9" font-size="12" font-weight="bold" text-anchor="middle">${p.rating}</text>
    `;
  }

  svg += `</svg>`;
  container.innerHTML = svg;
}

document.addEventListener('DOMContentLoaded', () => {
  const urlParams = new URLSearchParams(window.location.search);
  const user = urlParams.get('user') || 'tourist_vn';
  const inputEl = document.getElementById('usernameInput');
  if (inputEl) inputEl.value = user;

  loadRatingHistory(user);

  const btn = document.getElementById('loadHistoryBtn');
  if (btn) {
    btn.addEventListener('click', () => {
      const u = inputEl ? inputEl.value.trim() : 'tourist_vn';
      loadRatingHistory(u);
    });
  }
});

window.loadRatingHistory = loadRatingHistory;
