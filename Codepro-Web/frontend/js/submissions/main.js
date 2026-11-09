/**
 * CodeProOJ Submissions Live Stream Logic
 * Fetches and displays submissions from /api/v2/submissions
 */

async function loadSubmissions() {
  const h = value => String(value ?? '').replace(/[&<>"']/g, char => ({
    '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;'
  })[char]);
  const container = document.getElementById('submissionsTableBody');
  if (!container) return;

  const urlParams = new URLSearchParams(window.location.search);
  const probFilter = urlParams.get('problem') || '';
  const userFilter = urlParams.get('user') || '';

  let endpoint = '/submissions?';
  if (probFilter) endpoint += `problem=${encodeURIComponent(probFilter)}&`;
  if (userFilter) endpoint += `user=${encodeURIComponent(userFilter)}&`;

  container.innerHTML = `
    <tr>
      <td colspan="8" style="text-align: center; padding: 2rem; color: var(--color-text-muted);">
        Đang tải danh sách bài nộp từ hệ thống...
      </td>
    </tr>
  `;

  try {
    const res = await api.get(endpoint);
    if (!res.success || !res.data || !res.data.objects) {
      container.innerHTML = `
        <tr>
          <td colspan="8" style="text-align: center; padding: 2rem; color: #ef4444;">
            Không thể tải bài nộp: ${res.error?.message || 'Lỗi kết nối'}
          </td>
        </tr>
      `;
      return;
    }

    const subs = res.data.objects;
    if (subs.length === 0) {
      container.innerHTML = `
        <tr>
          <td colspan="8" style="text-align: center; padding: 2rem; color: var(--color-text-muted);">
            Chưa có bài nộp nào phù hợp tiêu chí.
          </td>
        </tr>
      `;
      return;
    }

    const currentUser = (typeof Auth !== 'undefined' && Auth.getUser) ? Auth.getUser() : null;
    const isAdmin = currentUser && (currentUser.is_staff || currentUser.is_superuser);

    container.innerHTML = subs.map(s => {
      const v = s.result || s.status || 'QU';
      let badgeClass = 'badge-pending';
      let badgeColor = '#f59e0b';

      if (v === 'AC') {
        badgeClass = 'badge-ac';
        badgeColor = '#10b981';
      } else if (['WA', 'RTE'].includes(v)) {
        badgeClass = 'badge-wa';
        badgeColor = '#ef4444';
      } else if (v === 'CE') {
        badgeColor = '#f97316';
      } else if (v === 'TLE') {
        badgeColor = '#eab308';
      }

      const dateStr = s.date ? new Date(s.date).toLocaleString('vi-VN') : 'Vừa xong';

      return `
        <tr>
          <td style="font-family: monospace; font-weight: 700;">#${h(s.id)}</td>
          <td>
            <a href="/frontend/html/user/profile.html?user=${encodeURIComponent(s.user)}" style="color: var(--color-primary); font-weight: 600; text-decoration: none;">
              ${h(s.user)}
            </a>
          </td>
          <td>
            <a href="/frontend/html/problems/problem.html?code=${encodeURIComponent(s.problem)}" style="color: #fff; font-weight: 600; text-decoration: none;">
              ${h(s.problem)}
            </a>
          </td>
          <td><span style="font-size: 0.8rem; color: var(--color-text-muted);">${h(s.language)}</span></td>
          <td>
            <span style="display: inline-block; padding: 3px 8px; border-radius: 4px; font-weight: 700; font-size: 0.85rem; background: ${badgeColor}22; color: ${badgeColor}; border: 1px solid ${badgeColor}44;">
              ${h(v)}
            </span>
          </td>
          <td style="font-weight: 700; color: ${v === 'AC' ? '#10b981' : 'inherit'};">
            ${h(s.points !== null ? s.points + 'đ' : '-')}
          </td>
          <td style="font-size: 0.85rem; color: var(--color-text-muted);">
            ${(s.time !== null) ? s.time.toFixed(3) + 's' : '-'} / ${(s.memory !== null) ? Math.round(s.memory) + 'KB' : '-'}
          </td>
          <td style="font-size: 0.8rem; color: var(--color-text-muted);">
            ${dateStr}
            ${isAdmin ? `
              <button onclick="rejudgeSubmission(${Number.isSafeInteger(Number(s.id)) ? Number(s.id) : 0})" class="btn btn-secondary" style="margin-left: 8px; padding: 0.2rem 0.5rem; font-size: 0.75rem;" title="Chấm lại bài nộp này">
                Rejudge
              </button>
            ` : ''}
          </td>
        </tr>
      `;
    }).join('');
  } catch (err) {
    container.innerHTML = `
      <tr>
        <td colspan="8" style="text-align: center; padding: 2rem; color: #ef4444;">
          Lỗi: ${h(err.message)}
        </td>
      </tr>
    `;
  }
}

async function rejudgeSubmission(id) {
  if (!confirm(`Bạn có chắc muốn Rejudge bài nộp #${id}?`)) return;

  try {
    const res = await api.post(`/rejudge/${id}`, {});
    if (res.success) {
      alert(`Đã rejudge thành công bài nộp #${id}!`);
      loadSubmissions();
    } else {
      alert(`Lỗi rejudge: ${res.error?.message || 'Không thể thực hiện'}`);
    }
  } catch (e) {
    alert(`Lỗi: ${e.message}`);
  }
}

document.addEventListener('DOMContentLoaded', loadSubmissions);
