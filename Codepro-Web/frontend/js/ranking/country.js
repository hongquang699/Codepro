async function loadCountryRankings() {
  const e = window.escapeRankingHtml;
  try {
    const data = await window.RankingApi.fetchCountryRankings();
    const tbody = document.getElementById('countryTableBody');
    if (!tbody) return;

    if (!data.countries || data.countries.length === 0) {
      tbody.innerHTML = '<tr><td colspan="6" style="text-align: center; color: var(--color-text-muted); padding: 40px;">Không có dữ liệu quốc gia.</td></tr>';
      return;
    }

    tbody.innerHTML = data.countries.map((c, idx) => {
      let badgeCls = 'standard';
      if (idx === 0) badgeCls = 'top-1';
      else if (idx === 1) badgeCls = 'top-2';
      else if (idx === 2) badgeCls = 'top-3';

      return `
        <tr>
          <td><span class="rank-badge ${badgeCls}">${idx + 1}</span></td>
          <td><strong>${e(c.country)}</strong></td>
          <td>${e(c.users_count)}</td>
          <td><strong style="color: var(--color-primary);">${e(c.total_solved)}</strong></td>
          <td><strong style="color: #10b981;">${e(c.avg_rating)}</strong></td>
          <td>
            ${c.top_user ? `<a href="/profile/${encodeURIComponent(c.top_user)}" style="color: #f59e0b; font-weight: 600; text-decoration: none;">${e(c.top_user)}</a>` : '-'}
          </td>
        </tr>
      `;
    }).join('');
  } catch (err) {
    const tbody = document.getElementById('countryTableBody');
    if (tbody) {
      tbody.innerHTML = `<tr><td colspan="6" style="text-align: center; color: #ef4444; padding: 30px;">Lỗi: ${e(err.message)}</td></tr>`;
    }
  }
}

document.addEventListener('DOMContentLoaded', loadCountryRankings);
window.loadCountryRankings = loadCountryRankings;
