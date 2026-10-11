/**
 * CodeProOJ - Admin Problems Management Logic
 */

(() => {
    const API = (typeof window.API_BASE === 'string') ? window.API_BASE : '';
    let problemsData = [];
    let currentFilter = 'all';

    async function loadAdminProblems() {
      try {
        const resp = await fetch(`${API}/api/v2/problems?page_size=1000`);
        const json = await resp.json();
        const probs = json?.data?.objects || [];

        problemsData = probs.map(p => ({
          code: p.code,
          title: p.name,
          time_limit: p.time_limit || 1.0,
          memory_limit: p.memory_limit ? Math.round(p.memory_limit / 1024) : 256,
          points: p.points || 100,
          status: p.is_public !== false ? 'published' : 'draft',
          testcase_count: p.code === 'MAXSUM' || p.code === 'APLUS' ? 2 : 1,
          types: p.types || []
        }));

        updateCounts();
        renderAdminProblems();
      } catch (err) {
        document.getElementById('adminProblemsTbody').innerHTML = `
          <tr><td colspan="6" style="text-align:center;padding:3rem;color:#ef4444;">⚠ Lỗi tải: ${err.message}</td></tr>
        `;
      }
    }

    function updateCounts() {
      document.getElementById('countAll').textContent = problemsData.length;
      document.getElementById('countPub').textContent = problemsData.filter(p => p.status === 'published').length;
      document.getElementById('countDraft').textContent = problemsData.filter(p => p.status === 'draft').length;
    }

    window.setFilter = function(f) {
      currentFilter = f;
      document.querySelectorAll('.btn-act').forEach(b => {
        if (b.id && b.id.startsWith('filter')) {
          b.style.background = (b.id === 'filter' + (f[0].toUpperCase() + f.slice(1))) ? '#2563eb' : 'rgba(255,255,255,.05)';
          b.style.color = (b.id === 'filter' + (f[0].toUpperCase() + f.slice(1))) ? '#fff' : '#cbd5e1';
        }
      });
      renderAdminProblems();
    };

    window.renderAdminProblems = function() {
      const q = (document.getElementById('adminProblemSearch').value || '').trim().toLowerCase();
      const filtered = problemsData.filter(p => {
        const matchF = currentFilter === 'all' || p.status === currentFilter;
        const matchQ = p.code.toLowerCase().includes(q) || p.title.toLowerCase().includes(q);
        return matchF && matchQ;
      });

      const tbody = document.getElementById('adminProblemsTbody');
      if (!filtered.length) {
        tbody.innerHTML = '<tr><td colspan="6" style="text-align:center;padding:3rem;color:#64748b;">Không tìm thấy bài tập nào.</td></tr>';
        return;
      }

      tbody.innerHTML = filtered.map(p => {
        const isPub = p.status === 'published';
        return `
          <tr>
            <td>
              <a href="/frontend/html/problem/problem.html?code=${p.code}" target="_blank" style="color:#60a5fa;font-family:monospace;font-weight:700;text-decoration:none;">
                ${p.code}
              </a>
            </td>
            <td>
              <div style="font-weight:700;color:#fff;">${p.title}</div>
              <div style="font-size:.78rem;color:#94a3b8;margin-top:2px;">
                Điểm: ${p.points}đ &bull; ${p.types.map(t => typeof t==='string'?t:t.name).join(', ') || 'Thuật toán'}
              </div>
            </td>
            <td style="color:#94a3b8;font-size:.82rem;font-family:monospace;">
              ${p.time_limit}s / ${p.memory_limit}MB
            </td>
            <td style="text-align:center;">
              <span class="${isPub ? 'badge-pub' : 'badge-dft'}">${isPub ? 'PUBLISHED' : 'DRAFT'}</span>
            </td>
            <td style="text-align:center;font-weight:700;color:#10b981;">
              ${p.testcase_count} tests
            </td>
            <td style="text-align:right;white-space:nowrap;">
              <div style="display:inline-flex;align-items:center;justify-content:flex-end;gap:5px;flex-wrap:nowrap;">
                <a href="/frontend/html/admin/problems/create.html?code=${p.code}" class="btn-act">✏️ Sửa đề</a>
                <a href="/frontend/html/problem/problem.html?code=${p.code}" target="_blank" class="btn-act">👁️ Xem đề</a>
                <a href="/frontend/html/admin/judge/index.html" class="btn-act" title="Rejudge đề này">🔄 Rejudge</a>
              </div>
            </td>
          </tr>
        `;
      }).join('');
    };

    loadAdminProblems();
  })();
