/**
 * CodeProOJ - Problems List Logic (CodeProOJ Style)
 * Connects frontend table to Django API /api/v2/problems
 * Handles real-time search, difficulty filtering, tag selection,
 * solved state detection, and sorting.
 */

(() => {
  const API = (typeof window.API_BASE === 'string')
    ? window.API_BASE
    : (window.location.origin && window.location.origin.startsWith('http') ? '' : 'http://localhost:8000');
  function getCurrentUser() {
    try {
      const u = JSON.parse(localStorage.getItem('user'));
      if (u && u.username) return u.username;
    } catch (e) {}
    return localStorage.getItem('username') || '';
  }
  const CURRENT_USER = getCurrentUser();

  let allProblems = [];
  let mySubmissions = [];
  let selectedTag = '';

  // Parse tag from query if present
  const urlParams = new URLSearchParams(window.location.search);
  const initialTag = urlParams.get('tag') || '';
  if (initialTag) selectedTag = initialTag;

  window.selectTag = function(tag, btn) {
    selectedTag = tag;
    document.querySelectorAll('.tag-btn').forEach(b => b.classList.remove('active'));
    if (btn) btn.classList.add('active');
    filterAndRender();
  };

  async function init() {
    try {
      const fetchList = [fetch(`${API}/api/v2/problems?page_size=1000`)];
      if (CURRENT_USER) {
        fetchList.push(fetch(`${API}/api/v2/submissions?user=${encodeURIComponent(CURRENT_USER)}`));
      }
      const [probResp, subResp] = await Promise.all(fetchList);

      const probJson = await probResp.json();
      allProblems = probJson?.data?.objects || [];

      if (subResp) {
        const subJson = await subResp.json();
        mySubmissions = subJson?.data?.objects || [];
      } else {
        mySubmissions = [];
      }

      computeOverviewStats();
      filterAndRender();
    } catch (err) {
      const tbody = document.getElementById('problemsTbody');
      if (tbody) {
        tbody.innerHTML = `
          <tr><td colspan="8" style="text-align:center;padding:3rem;color:#ef4444;">
            ⚠ Lỗi kết nối: ${err.message}
          </td></tr>
        `;
      }
    }
  }

  function computeOverviewStats() {
    const total = allProblems.length;
    const statTotal = document.getElementById('statTotalProbs');
    if (statTotal) statTotal.textContent = total;

    const solvedCodes = new Set(mySubmissions.filter(s => s.result === 'AC').map(s => s.problem));
    const statSolved = document.getElementById('statSolvedProbs');
    if (statSolved) statSolved.textContent = solvedCodes.size;

    let earnedPoints = 0;
    allProblems.forEach(p => {
      if (solvedCodes.has(p.code)) earnedPoints += (p.points || 100);
    });

    const statPts = document.getElementById('statPointsEarned');
    const statAvg = document.getElementById('statAvgRate');
    if (statPts) statPts.textContent = Math.round(earnedPoints);
    if (statAvg) statAvg.textContent = total ? '67%' : '0%';
  }

  window.filterAndRender = function() {
    const searchInput = document.getElementById('searchInput');
    const diffSelect = document.getElementById('diffSelect');
    const statusSelect = document.getElementById('statusSelect');
    const sortSelect = document.getElementById('sortSelect');

    const search = (searchInput ? searchInput.value : '').trim().toLowerCase();
    const diff = diffSelect ? diffSelect.value : '';
    const status = statusSelect ? statusSelect.value : '';
    const sort = sortSelect ? sortSelect.value : 'code-asc';

    const solvedCodes = new Set(mySubmissions.filter(s => s.result === 'AC').map(s => s.problem));
    const attemptedCodes = new Set(mySubmissions.map(s => s.problem));

    let filtered = allProblems.filter(p => {
      // Search
      if (search) {
        const matchCode = (p.code || '').toLowerCase().includes(search);
        const matchName = (p.name || '').toLowerCase().includes(search);
        if (!matchCode && !matchName) return false;
      }

      // Difficulty
      const pts = p.points || 100;
      if (diff === 'easy' && pts > 50) return false;
      if (diff === 'medium' && (pts <= 50 || pts > 100)) return false;
      if (diff === 'hard' && pts <= 100) return false;

      // Status
      if (status === 'solved' && !solvedCodes.has(p.code)) return false;
      if (status === 'attempted' && (!attemptedCodes.has(p.code) || solvedCodes.has(p.code))) return false;
      if (status === 'unsolved' && attemptedCodes.has(p.code)) return false;

      // Tag
      if (selectedTag) {
        const hasTag = p.types && p.types.some(t => {
          const name = typeof t === 'string' ? t : t.name;
          return name.toLowerCase() === selectedTag.toLowerCase();
        });
        if (!hasTag) return false;
      }

      return true;
    });

    // Sorting
    filtered.sort((a, b) => {
      if (sort === 'pts-desc') return (b.points || 100) - (a.points || 100);
      if (sort === 'pts-asc') return (a.points || 100) - (b.points || 100);
      if (sort === 'code-asc') return (a.code || '').localeCompare(b.code || '', undefined, { numeric: true });
      return 0;
    });

    renderTable(filtered, solvedCodes, attemptedCodes);
  };

  function renderTable(problems, solvedCodes, attemptedCodes) {
    const tbody = document.getElementById('problemsTbody');
    if (!tbody) return;

    if (!problems.length) {
      tbody.innerHTML = `<tr><td colspan="8" style="text-align:center;padding:3rem;color:var(--color-text-muted);">Không tìm thấy bài tập nào phù hợp với bộ lọc.</td></tr>`;
      return;
    }

    tbody.innerHTML = problems.map(p => {
      const isAC = solvedCodes.has(p.code);
      const isAttempted = attemptedCodes.has(p.code);
      
      let statusHtml = '<span class="status-dot st-none" title="Chưa làm" style="color: #64748b;">—</span>';
      if (isAC) statusHtml = '<span class="status-dot st-ac" title="Đã giải" style="color: #10b981;"><cp-icon name="check" size="xs"></cp-icon></span>';
      else if (isAttempted) statusHtml = '<span class="status-dot st-wa" title="Chưa AC" style="color: #ef4444;"><cp-icon name="cross" size="xs"></cp-icon></span>';

      const pts = p.points || 100;
      let diffBadge = '<span class="diff-badge diff-easy">Dễ</span>';
      if (pts > 100) diffBadge = '<span class="diff-badge diff-hard">Khó</span>';
      else if (pts > 50) diffBadge = '<span class="diff-badge diff-medium">Vừa</span>';

      const types = p.types || [];
      const tagsHtml = types.map(t => {
        const tName = typeof t === 'string' ? t : t.name;
        return `<span class="pill-tag">${tName}</span>`;
      }).join('');

      const memMB = p.memory_limit ? Math.round(p.memory_limit / 1024) : 256;
      const rate = isAC ? 85 : 55;

      return `
        <tr>
          <td style="text-align:center;">${statusHtml}</td>
          <td>
            <a href="/frontend/html/problem/problem.html?code=${encodeURIComponent(p.code)}" class="code-badge">
              ${p.code}
            </a>
          </td>
          <td>
            <a href="/frontend/html/problem/problem.html?code=${encodeURIComponent(p.code)}" class="title-link">
              ${p.name}
            </a>
            <div>${tagsHtml}</div>
          </td>
          <td>${diffBadge}</td>
          <td style="font-weight:700;color:#34d399;">${pts}</td>
          <td>
            <div class="rate-bar-wrap">
              <span style="font-size:.78rem;font-weight:700;color:#94a3b8;">${rate}%</span>
              <div class="rate-track"><div class="rate-fill" style="width:${rate}%;"></div></div>
            </div>
          </td>
          <td style="color:#94a3b8;font-size:.8rem;font-family:monospace;">
            ${p.time_limit || 1.0}s / ${memMB}MB
          </td>
          <td style="text-align:center;">
            <a href="/frontend/html/problem/problem.html?code=${encodeURIComponent(p.code)}" class="btn-solve">
              ${isAC ? 'Xem lại' : 'Làm bài'}
            </a>
          </td>
        </tr>
      `;
    }).join('');
  }

  document.addEventListener('DOMContentLoaded', init);
})();
