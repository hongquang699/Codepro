/**
 * CodeProOJ Leaderboard / Ranking Logic
 * Fetches users from /api/v2/users and sorts by rating
 */

async function loadRankings() {
  const tbody = document.getElementById('rankingTableBody');
  if (!tbody) return;

  tbody.innerHTML = `
    <tr>
      <td colspan="6" style="text-align: center; padding: 2rem; color: var(--color-text-muted);">
        Đang tải bảng xếp hạng từ hệ thống...
      </td>
    </tr>
  `;

  try {
    const res = await api.get('/users');
    if (!res.success || !res.data || !res.data.objects) {
      tbody.innerHTML = `
        <tr>
          <td colspan="6" style="text-align: center; padding: 2rem; color: #ef4444;">
            Không thể tải bảng xếp hạng: ${res.error?.message || 'Lỗi'}
          </td>
        </tr>
      `;
      return;
    }

    // Sort by rating descending
    const users = res.data.objects.sort((a, b) => (b.rating || 0) - (a.rating || 0));

    if (users.length === 0) {
      tbody.innerHTML = `
        <tr>
          <td colspan="6" style="text-align: center; padding: 2rem; color: var(--color-text-muted);">
            Chưa có thành viên nào trên hệ thống.
          </td>
        </tr>
      `;
      return;
    }

    tbody.innerHTML = users.map((u, idx) => {
      const rank = idx + 1;
      let medal = '';
      if (rank === 1) medal = '🥇 ';
      else if (rank === 2) medal = '🥈 ';
      else if (rank === 3) medal = '🥉 ';

      const rating = u.rating || 1500;
      const color = getRatingColor(rating);
      const solved = u.problem_count || 0;
      const org = u.organizations && u.organizations.length ? u.organizations.join(', ') : 'Tự do';

      return `
        <tr>
          <td style="font-weight: 700; text-align: center; font-size: 1rem;">
            ${medal}${rank}
          </td>
          <td>
            <a href="/frontend/html/user/profile.html?user=${encodeURIComponent(u.username)}" 
               style="color: ${color}; font-weight: 700; text-decoration: none; font-size: 1rem;">
              ${u.username}
            </a>
          </td>
          <td>
            <span style="display: inline-block; padding: 2px 8px; border-radius: 4px; font-weight: 600; font-size: 0.8rem; background: ${color}22; color: ${color}; border: 1px solid ${color}44;">
              ${u.display_rank || 'Coder'}
            </span>
          </td>
          <td>${org}</td>
          <td style="text-align: center; font-weight: 600;">
            ${solved} bài
          </td>
          <td style="font-weight: 800; font-size: 1.1rem; color: ${color};">
            ${rating}
          </td>
        </tr>
      `;
    }).join('');

  } catch (err) {
    tbody.innerHTML = `
      <tr>
        <td colspan="6" style="text-align: center; padding: 2rem; color: #ef4444;">
          Lỗi kết nối: ${err.message}
        </td>
      </tr>
    `;
  }
}

document.addEventListener('DOMContentLoaded', loadRankings);
