/**
 * CodeProOJ - Admin Users Management Logic
 */

(() => {
    const API = (typeof window.API_BASE === 'string') ? window.API_BASE : '';
    let allUsers = [];

    function ratingColor(r) {
      if (typeof CPRating !== 'undefined') return CPRating.getColor(r);
      const num = parseInt(r, 10);
      if (isNaN(num) || num <= 0) return '#94a3b8';
      if (num >= 2400) return '#ef4444';
      if (num >= 2100) return '#f97316';
      if (num >= 1900) return '#a855f7';
      if (num >= 1600) return '#3b82f6';
      if (num >= 1400) return '#10b981';
      if (num >= 1200) return '#06b6d4';
      return '#94a3b8';
    }

    async function loadUsers() {
      try {
        const resp = await fetch(`${API}/api/v2/users`);
        const json = await resp.json();
        allUsers = json?.data?.objects || [];
        document.getElementById('userCountSummary').textContent = `${allUsers.length} thành viên`;
        renderUsers(allUsers);
      } catch (err) {
        document.getElementById('userListTbody').innerHTML = `
          <tr><td colspan="7" style="text-align:center;padding:3rem;color:#ef4444;">⚠ Lỗi tải: ${err.message}</td></tr>
        `;
      }
    }

    window.filterUsers = function() {
      const q = (document.getElementById('userFilter').value || '').trim().toLowerCase();
      const filtered = allUsers.filter(u => 
        (u.username || '').toLowerCase().includes(q) || (u.email || '').toLowerCase().includes(q)
      );
      renderUsers(filtered);
    };

    function renderUsers(users) {
      const tbody = document.getElementById('userListTbody');
      if (!users.length) {
        tbody.innerHTML = '<tr><td colspan="7" style="text-align:center;padding:3rem;color:#64748b;">Không tìm thấy thành viên nào.</td></tr>';
        return;
      }

      tbody.innerHTML = users.map(u => {
        const rating = u.rating || 1500;
        const color = ratingColor(rating);
        const letter = (u.username || 'U')[0].toUpperCase();

        return `
          <tr>
            <td>
              <div style="display:flex;align-items:center;">
                <div class="user-avatar-sm" style="background:${color};">${letter}</div>
                <div>
                  <a href="/frontend/html/user/profile.html?u=${u.username}" target="_blank" style="color:${color};font-weight:700;text-decoration:none;font-size:.92rem;">
                    ${u.username}
                  </a>
                  ${u.is_staff || u.is_superuser ? '<span style="font-size:.65rem;background:#dc2626;color:#fff;padding:.1rem .35rem;border-radius:3px;margin-left:4px;">STAFF</span>' : ''}
                </div>
              </div>
            </td>
            <td style="color:#94a3b8;font-size:.84rem;">${u.email || '—'}</td>
            <td style="font-weight:800;color:${color};">${rating}</td>
            <td>
              <span style="font-size:.78rem;font-weight:700;color:${color};background:${color}18;padding:.2rem .6rem;border-radius:999px;border:1px solid ${color}33;">
                ${u.display_rank || 'Coder'}
              </span>
            </td>
            <td style="font-weight:700;color:#34d399;">${u.problem_count || 0} bài</td>
            <td style="font-weight:700;color:#f59e0b;">${Math.round(u.points || 0)}đ</td>
            <td style="text-align:center;">
              <a href="/frontend/html/submission/all.html?user=${u.username}" class="btn-act" target="_blank">Bài nộp</a>
              <a href="/frontend/html/user/profile.html?u=${u.username}" class="btn-act" target="_blank" style="margin-left:4px;">Hồ sơ</a>
            </td>
          </tr>
        `;
      }).join('');
    }

    loadUsers();
  })();
