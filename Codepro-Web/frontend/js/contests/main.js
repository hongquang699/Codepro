/**
 * CodeProOJ Contests Logic
 * Fetches and displays contests from /api/v2/contests
 */

async function loadContests() {
  const h = value => String(value ?? '').replace(/[&<>"']/g, char => ({
    '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;'
  })[char]);
  const container = document.getElementById('contestsContainer');
  if (!container) return;

  container.innerHTML = `
    <div style="text-align: center; padding: 2rem; color: var(--color-text-muted);">
      Đang tải danh sách kỳ thi từ hệ thống...
    </div>
  `;

  try {
    const res = await api.get('/contests');
    if (!res.success || !res.data || !res.data.objects) {
      container.innerHTML = `
        <div style="text-align: center; padding: 2rem; color: #ef4444;">
          Không thể tải danh sách kỳ thi: ${h(res.error?.message || 'Lỗi')}
        </div>
      `;
      return;
    }

    const contests = res.data.objects;
    if (contests.length === 0) {
      container.innerHTML = `
        <div style="text-align: center; padding: 2rem; color: var(--color-text-muted);">
          Hiện chưa có kỳ thi nào được công bố.
        </div>
      `;
      return;
    }

    const now = new Date();

    container.innerHTML = contests.map(c => {
      const start = new Date(c.start_time);
      const end = new Date(c.end_time);

      let statusBadge = '<span class="badge badge-ac">ĐANG DIỄN RA</span>';
      if (now < start) {
        statusBadge = '<span class="badge badge-pending">SẮP DIỄN RA</span>';
      } else if (now > end) {
        statusBadge = '<span style="display: inline-block; padding: 3px 8px; border-radius: 4px; font-weight: 700; font-size: 0.75rem; background: rgba(255,255,255,0.1); color: var(--color-text-muted);">ĐÃ KẾT THÚC</span>';
      }

      return `
        <div class="card" style="margin-bottom: 1.5rem; display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 1rem;">
          <div>
            <div style="display: flex; align-items: center; gap: 0.75rem; margin-bottom: 0.5rem;">
              ${statusBadge}
              <span style="font-weight: 700; color: #a855f7; font-size: 0.8rem; text-transform: uppercase;">${h(c.format || 'ICPC')} Format</span>
            </div>
            <h2 style="margin: 0 0 0.5rem 0;">
              <a href="/frontend/html/contest/scoreboard.html?contest=${encodeURIComponent(c.key)}" style="color: inherit; text-decoration: none;">
                ${h(c.name)}
              </a>
            </h2>
            <div style="color: var(--color-text-muted); font-size: 0.875rem;">
              Bắt đầu: <strong>${start.toLocaleString('vi-VN')}</strong> &bull; Kết thúc: <strong>${end.toLocaleString('vi-VN')}</strong>
            </div>
          </div>

          <div style="display: flex; gap: 0.75rem;">
            <a href="/frontend/html/contest/scoreboard.html?contest=${encodeURIComponent(c.key)}" class="btn btn-secondary">
              📊 Bảng xếp hạng (Scoreboard)
            </a>
            <a href="/frontend/html/problems/index.html" class="btn btn-primary">
              Vào thi &rarr;
            </a>
          </div>
        </div>
      `;
    }).join('');
  } catch (err) {
    container.innerHTML = `
      <div style="text-align: center; padding: 2rem; color: #ef4444;">
        Lỗi kết nối: ${h(err.message)}
      </div>
    `;
  }
}

document.addEventListener('DOMContentLoaded', loadContests);
