/**
 * CodeProOJ - Submissions All List Logic
 */

const API = (typeof window.API_BASE === 'string')
  ? window.API_BASE
  : (window.location.origin && window.location.origin.startsWith('http') ? '' : 'http://localhost:8000');
const escapeSubmissionHtml = value => String(value ?? '').replace(/[&<>"']/g, char => ({
  '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;'
})[char]);
    let autoInterval = null;

    function getVerdictLabel(v) {
      const getIcon = (name) => (window.CPIcons ? window.CPIcons.get(name, { size: '13px' }) : '');
      const map = {
        'AC': `${getIcon('check')} AC`,
        'WA': `${getIcon('cross')} WA`,
        'TLE': `${getIcon('clock')} TLE`,
        'MLE': `${getIcon('database')} MLE`,
        'RTE': `${getIcon('zap')} RE`,
        'CE': `${getIcon('settings')} CE`,
        'SE': `${getIcon('shield')} SE`,
        'IE': `${getIcon('shield')} SE`,
        'G': `${getIcon('clock')} Đang chấm`,
        'QU': `${getIcon('inbox')} Chờ`,
        'RUNNING': `${getIcon('clock')} Đang chấm`
      };
      return map[v] || escapeSubmissionHtml(v);
    }
    const verdictClass = {
      'AC':'verdict-AC','WA':'verdict-WA','TLE':'verdict-TLE','MLE':'verdict-MLE',
      'RTE':'verdict-RE','CE':'verdict-CE','G':'verdict-G','QU':'verdict-QU',
      'RUNNING':'verdict-RUNNING','SE':'verdict-SE','IE':'verdict-SE'
    };

    function formatTime(t) {
      if (!t && t !== 0) return '—';
      const ms = Math.round(parseFloat(t) * 1000);
      return ms + ' ms';
    }
    function formatMem(m) {
      if (!m && m !== 0) return '—';
      return parseFloat(m).toFixed(1) + ' MB';
    }
    function formatDate(d) {
      if (!d) return '—';
      const dt = new Date(d);
      return dt.toLocaleDateString('vi', { day:'2-digit', month:'2-digit' }) + ' ' + dt.toLocaleTimeString('vi', { hour:'2-digit', minute:'2-digit' });
    }

    async function loadSubmissions() {
      const refreshIcon = document.getElementById('refreshIcon');
      refreshIcon.classList.add('spinning');

      const filterUser = document.getElementById('filterUser').value.trim();
      const filterProblem = document.getElementById('filterProblem').value.trim();
      const filterVerdict = document.getElementById('filterVerdict').value;

      let url = `${API}/api/v2/submissions`;
      const params = [];
      if (filterUser) params.push(`user=${encodeURIComponent(filterUser)}`);
      if (filterProblem) params.push(`problem=${encodeURIComponent(filterProblem)}`);
      if (params.length) url += '?' + params.join('&');

      try {
        const resp = await fetch(url);
        const json = await resp.json();
        const subs = json?.data?.objects || [];

        // Stats
        const total = subs.length;
        const ac = subs.filter(s => s.result === 'AC').length;
        const wa = subs.filter(s => s.result === 'WA').length;
        const other = subs.filter(s => ['TLE','MLE','RTE','RE'].includes(s.result)).length;
        document.getElementById('totalCount').textContent = total;
        document.getElementById('acCount').textContent = ac;
        document.getElementById('waCount').textContent = wa;
        document.getElementById('tleCount').textContent = other;

        // Filter by verdict
        let filtered = filterVerdict ? subs.filter(s => (s.result||'').startsWith(filterVerdict)) : subs;

        const tbody = document.getElementById('subTableBody');
        if (!filtered.length) {
          tbody.innerHTML = `<tr><td colspan="9"><div class="empty-state">
            <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><circle cx="11" cy="11" r="8"/><path d="m21 21-4.35-4.35"/></svg>
            <div>Không có bài nộp nào phù hợp</div>
          </div></td></tr>`;
          return;
        }

        tbody.innerHTML = filtered.map(s => {
          const v = s.result || s.status || 'QU';
          const cls = verdictClass[v] || 'verdict-WA';
          const lbl = getVerdictLabel(v);
          const isJudging = ['G','QU','RUNNING'].includes(v);
          const userIcon = window.CPIcons ? window.CPIcons.get('user', { size: '12px' }) : '';

          return `<tr>
            <td><a href="/frontend/html/submission/submission.html?id=${Number.isSafeInteger(Number(s.id)) ? Number(s.id) : 0}" class="sub-link">#${escapeSubmissionHtml(s.id)}</a></td>
            <td><a href="/profile/${encodeURIComponent(s.user)}" class="prob-link" style="display:inline-flex;align-items:center;gap:0.35rem;">${userIcon} ${escapeSubmissionHtml(s.user)}</a></td>
            <td><a href="/frontend/html/problem/problem.html?code=${encodeURIComponent(s.problem)}" class="prob-link">${escapeSubmissionHtml(s.problem)}</a></td>
            <td>
              <span class="verdict-badge ${cls}">
                ${isJudging ? '<span class="pulse-dot live" style="width:6px;height:6px;"></span>' : ''}
                ${lbl}
              </span>
            </td>
            <td class="pts-col">${escapeSubmissionHtml(s.points != null ? s.points : '—')}</td>
            <td class="time-col">${formatTime(s.time)}</td>
            <td class="mem-col">${formatMem(s.memory)}</td>
            <td><span class="lang-badge">${escapeSubmissionHtml(s.language || '—')}</span></td>
            <td style="font-size:.8rem;color:var(--color-text-muted);">${formatDate(s.date)}</td>
          </tr>`;
        }).join('');

      } catch (e) {
        document.getElementById('subTableBody').innerHTML =
          `<tr><td colspan="9" class="empty-state" style="color:#ef4444;">⚠ Lỗi kết nối API: ${escapeSubmissionHtml(e.message)}</td></tr>`;
      } finally {
        refreshIcon.classList.remove('spinning');
      }
    }

    function startAutoRefresh() {
      if (autoInterval) clearInterval(autoInterval);
      autoInterval = setInterval(loadSubmissions, 5000);
    }
    function stopAutoRefresh() {
      if (autoInterval) clearInterval(autoInterval);
      autoInterval = null;
    }

    document.getElementById('autoRefresh').addEventListener('change', function() {
      const dot = document.getElementById('pulseDot');
      if (this.checked) {
        startAutoRefresh();
        dot.classList.add('live');
      } else {
        stopAutoRefresh();
        dot.classList.remove('live');
      }
    });

    // Filters trigger reload on Enter
    ['filterUser','filterProblem'].forEach(id => {
      document.getElementById(id).addEventListener('keydown', e => { if (e.key === 'Enter') loadSubmissions(); });
    });
    document.getElementById('filterVerdict').addEventListener('change', loadSubmissions);
    document.getElementById('filterLang').addEventListener('change', loadSubmissions);

    // Init
    loadSubmissions();
    startAutoRefresh();

// Window exports for inline event handlers
window.loadSubmissions = loadSubmissions;
window.toggleAutoRefresh = toggleAutoRefresh;
