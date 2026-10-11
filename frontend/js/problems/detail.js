/**
 * CodeProOJ - Problem Detail JavaScript (CodeProOJ Style)
 * Handles problem loading, LaTeX rendering, tab navigation,
 * and linking to the dedicated Submit Page (/submit?code=...)
 */

(() => {
  const API = (typeof window.API_BASE === 'string')
    ? window.API_BASE
    : (window.location.origin && window.location.origin.startsWith('http') ? '' : 'http://localhost:8000');
  const urlParams = new URLSearchParams(window.location.search);
  const CODE = urlParams.get('code') || urlParams.get('problem') || 'SUMA';
  function getCurrentUser() {
    try {
      const u = JSON.parse(localStorage.getItem('user'));
      if (u && u.username) return u.username;
    } catch (e) {}
    return localStorage.getItem('username') || '';
  }
  const CURRENT_USER = getCurrentUser();

  let currentProblem = null;
  let allSubmissions = [];

  /* ── Switch Tabs ────────────────────────────────────────── */
  window.switchTab = function(tabName, btn) {
    document.querySelectorAll('.prob-tab').forEach(b => b.classList.remove('active'));
    document.querySelectorAll('.prob-tab-panel').forEach(p => p.classList.remove('active'));
    if (btn) btn.classList.add('active');
    const panel = document.getElementById('panel-' + tabName);
    if (panel) panel.classList.add('active');

    if (tabName === 'mysubs') renderMySubs();
    if (tabName === 'allsubs') renderAllSubs();
    if (tabName === 'stats') renderStats();
  };

  /* ── Fetch Problem Data ─────────────────────────────────── */
  async function fetchProblem() {
    try {
      const resp = await fetch(`${API}/api/v2/problem/${encodeURIComponent(CODE)}`);
      if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
      const json = await resp.json();
      currentProblem = json?.data?.object;
      if (!currentProblem) throw new Error('Không có dữ liệu bài toán');

      renderHeader(currentProblem);
      renderStatement(currentProblem);
      fetchSubmissions();
    } catch (err) {
      document.getElementById('statementBody').innerHTML = `
        <div style="text-align:center;padding:3rem;color:#ef4444;">
          <h3>⚠ Lỗi tải bài toán</h3>
          <p>${err.message}</p>
        </div>
      `;
    }
  }

  /* ── Render Header & Sidebar Info ────────────────────────── */
  function renderHeader(p) {
    document.title = `${p.code} - ${p.name} | CodeProOJ`;
    const bcCode = document.getElementById('bcCode');
    const bcTitle = document.getElementById('bcTitle');
    const probCode = document.getElementById('probCode');
    const probTitle = document.getElementById('probTitle');

    if (bcCode) bcCode.textContent = p.code;
    if (bcTitle) bcTitle.textContent = p.name;
    if (probCode && probCode.querySelector('span')) probCode.querySelector('span').textContent = p.code;
    if (probTitle) probTitle.textContent = p.name;

    const memMB = p.memory_limit ? Math.round(p.memory_limit / 1024) : 256;
    const pillTime = document.getElementById('pillTime');
    const pillMem = document.getElementById('pillMem');
    const pillPts = document.getElementById('pillPts');
    const sbTime = document.getElementById('sbTime');
    const sbMem = document.getElementById('sbMem');
    const sbPoints = document.getElementById('sbPoints');

    const getIcon = (name) => (window.CPIcons ? window.CPIcons.get(name, { size: '13px' }) : '');

    if (pillTime) pillTime.innerHTML = `${getIcon('clock')} ${p.time_limit || 1.0}s`;
    if (pillMem) pillMem.innerHTML = `${getIcon('database')} ${memMB} MB`;
    if (pillPts) pillPts.innerHTML = `${getIcon('award')} ${p.points || 100} điểm`;
    if (sbTime) sbTime.textContent = `${p.time_limit || 1.0}s`;
    if (sbMem) sbMem.textContent = `${memMB} MB`;
    if (sbPoints) sbPoints.textContent = `${p.points || 100} điểm`;

    // Setup Submit Buttons leading to dedicated submit page
    const submitUrl = `/submit?code=${encodeURIComponent(p.code)}`;
    const btnHeaderSubmit = document.getElementById('btnHeaderSubmit');
    const btnSidebarSubmit = document.getElementById('btnSidebarSubmit');
    const btnBottomSubmit = document.getElementById('btnBottomSubmit');

    if (btnHeaderSubmit) btnHeaderSubmit.href = submitUrl;
    if (btnSidebarSubmit) btnSidebarSubmit.href = submitUrl;
    if (btnBottomSubmit) btnBottomSubmit.href = submitUrl;

    // Difficulty calculation
    const pts = p.points || 100;
    const diffEl = document.getElementById('pillDiff');
    const sbDiff = document.getElementById('sbDiff');
    let diffName = 'Trung bình';
    let diffClass = 'medium';

    if (pts <= 50) {
      diffName = 'Dễ';
      diffClass = 'easy';
    } else if (pts <= 100) {
      diffName = 'Trung bình';
      diffClass = 'medium';
    } else if (pts <= 200) {
      diffName = 'Khó';
      diffClass = 'hard';
    } else {
      diffName = 'Expert';
      diffClass = 'expert';
    }

    if (diffEl) {
      diffEl.className = `meta-pill pill-diff ${diffClass}`;
      diffEl.textContent = `● ${diffName}`;
    }
    if (sbDiff) sbDiff.textContent = diffName;

    // Tags & Authors
    const sbTags = document.getElementById('sbTags');
    if (sbTags) {
      const types = p.types || [];
      sbTags.textContent = types.map(t => typeof t === 'string' ? t : t.name).join(', ') || 'Thuật toán';
    }

    const sbAuthor = document.getElementById('sbAuthor');
    if (sbAuthor) {
      const authList = p.authors && p.authors.length ? p.authors.join(', ') : 'Admin / CodeProOJ Team';
      sbAuthor.textContent = authList;
    }
  }

  /* ── Render Statement (Markdown + MathJax) ───────────────── */
  function renderStatement(p) {
    const desc = p.description || '';
    const body = document.getElementById('statementBody');
    if (!body) return;

    if (!desc.trim()) {
      body.innerHTML = '<p style="color:var(--color-text-muted);">Bài toán chưa có mô tả chi tiết.</p>';
      return;
    }

    if (typeof marked !== 'undefined') {
      body.innerHTML = marked.parse(desc);
    } else {
      body.innerHTML = `<p>${desc.replace(/\\n/g, '<br>')}</p>`;
    }

    formatExampleBlocks(body);

    if (window.MathJax && MathJax.typesetPromise) {
      MathJax.typesetPromise([body]).catch(e => console.warn('MathJax error:', e));
    }
  }

  function formatExampleBlocks(container) {
    const codeBlocks = container.querySelectorAll('pre');
    codeBlocks.forEach(pre => {
      const btn = document.createElement('button');
      btn.className = 'copy-btn';
      btn.textContent = 'Sao chép';
      btn.style.float = 'right';
      btn.style.marginBottom = '6px';
      btn.onclick = () => {
        navigator.clipboard.writeText(pre.innerText);
        btn.textContent = '✓ Đã chép';
        setTimeout(() => btn.textContent = 'Sao chép', 1500);
      };
      pre.parentNode.insertBefore(btn, pre);
    });
  }

  /* ── Submissions Data ───────────────────────────────────── */
  async function fetchSubmissions() {
    try {
      const resp = await fetch(`${API}/api/v2/submissions?problem=${encodeURIComponent(CODE)}`);
      const json = await resp.json();
      allSubmissions = json?.data?.objects || [];

      const mySubs = allSubmissions.filter(s => s.user === CURRENT_USER);
      const myCount = document.getElementById('mySubsCount');
      const allCount = document.getElementById('allSubsCount');
      if (myCount) myCount.textContent = mySubs.length;
      if (allCount) allCount.textContent = allSubmissions.length;

      const hasAC = mySubs.some(s => s.result === 'AC');
      const badge = document.getElementById('solvedBadge');
      const sbBest = document.getElementById('sbBestVerdict');

      const getIcon = (name) => (window.CPIcons ? window.CPIcons.get(name, { size: '13px' }) : '');

      if (hasAC) {
        if (badge) {
          badge.className = 'ac-badge solved-yes';
          badge.innerHTML = `${getIcon('check')} Đã giải (AC)`;
        }
        if (sbBest) {
          sbBest.className = 'ac-badge solved-yes';
          sbBest.innerHTML = `${getIcon('check')} Accepted (100đ)`;
        }
      } else if (mySubs.length > 0) {
        if (badge) {
          badge.className = 'ac-badge solved-no';
          badge.style.color = '#f87171';
          badge.innerHTML = `${getIcon('cross')} Chưa AC`;
        }
        if (sbBest) {
          sbBest.className = 'ac-badge solved-no';
          sbBest.style.color = '#f87171';
          badge.innerHTML = `${getIcon('cross')} Chưa đạt điểm tối đa`;
        }
      } else {
        if (badge) {
          badge.className = 'ac-badge solved-no';
          badge.innerHTML = `— Chưa nộp`;
        }
        if (sbBest) {
          sbBest.className = 'ac-badge solved-no';
          sbBest.textContent = 'Chưa nộp bài';
        }
      }
    } catch (err) {
      console.warn('Cannot fetch submissions:', err);
    }
  }

  function renderSubRow(s, showUser = true) {
    const isAC = s.result === 'AC';
    const vClass = `vb-${s.result || 'WA'}`;
    const timeMs = s.time != null ? Math.round(parseFloat(s.time) * 1000) + ' ms' : '—';
    const memMB = s.memory != null ? parseFloat(s.memory).toFixed(1) + ' MB' : '—';
    const dateStr = s.date ? new Date(s.date).toLocaleString('vi-VN') : '—';

    return `
      <tr>
        <td><a href="/submissions/${s.id}" style="color:#60a5fa;font-family:monospace;font-weight:700;">#${s.id}</a></td>
        ${showUser ? `<td><a href="/profile/${s.user}" style="color:#cbd5e1;font-weight:600;">${s.user}</a></td>` : ''}
        <td><span class="vb ${vClass}">${s.result || 'Pending'}</span></td>
        <td style="font-weight:700;color:${isAC ? '#34d399' : '#f87171'};">${s.points != null ? s.points : '—'}</td>
        <td style="font-family:monospace;color:#94a3b8;">${timeMs}</td>
        <td style="font-family:monospace;color:#94a3b8;">${memMB}</td>
        <td><span style="font-family:monospace;font-size:.78rem;background:rgba(255,255,255,.05);padding:.15rem .45rem;border-radius:4px;">${s.language}</span></td>
        <td style="color:#64748b;font-size:.78rem;">${dateStr}</td>
        <td style="text-align:center;white-space:nowrap;">
          <button class="btn-sub-act btn-sub-code" onclick="viewSource(${s.id})" title="Xem mã nguồn đã nộp">
            <cp-icon name="code" size="xs"></cp-icon> Mã nguồn
          </button>
          <button class="btn-sub-act btn-sub-res" onclick="viewResult(${s.id})" title="Xem chi tiết kết quả từng test">
            <cp-icon name="chart" size="xs"></cp-icon> Kết quả
          </button>
        </td>
      </tr>
    `;
  }

  function renderMySubs() {
    if (!CURRENT_USER) {
      const tbody = document.getElementById('mySubsTbody');
      if (tbody) {
        tbody.innerHTML = `<tr><td colspan="8" style="text-align:center;padding:3rem;color:var(--color-text-muted);">Vui lòng <a href="/frontend/html/auth/login.html" style="color:var(--color-primary,#3b82f6);text-decoration:underline;">đăng nhập</a> để xem lịch sử nộp bài của bạn.</td></tr>`;
      }
      return;
    }
    const mySubs = allSubmissions.filter(s => s.user === CURRENT_USER);
    const tbody = document.getElementById('mySubsTbody');
    if (!tbody) return;
    if (!mySubs.length) {
      tbody.innerHTML = `<tr><td colspan="8" style="text-align:center;padding:3rem;color:var(--color-text-muted);">Bạn chưa có bài nộp nào cho bài toán này.</td></tr>`;
      return;
    }
    tbody.innerHTML = mySubs.map(s => renderSubRow(s, false)).join('');
  }

  function renderAllSubs() {
    const tbody = document.getElementById('allSubsTbody');
    if (!tbody) return;
    if (!allSubmissions.length) {
      tbody.innerHTML = `<tr><td colspan="9" style="text-align:center;padding:3rem;color:var(--color-text-muted);">Chưa có bài nộp nào trong hệ thống.</td></tr>`;
      return;
    }
    tbody.innerHTML = allSubmissions.slice(0, 50).map(s => renderSubRow(s, true)).join('');
  }

  function renderStats() {
    const total = allSubmissions.length;
    const acList = allSubmissions.filter(s => s.result === 'AC');
    const acCount = acList.length;
    const uniqueUsers = new Set(acList.map(s => s.user)).size;
    const rate = total ? Math.round((acCount / total) * 100) : 0;

    const statTotal = document.getElementById('statTotal');
    const statAC = document.getElementById('statAC');
    const statRate = document.getElementById('statRate');
    const statUsers = document.getElementById('statUsers');

    if (statTotal) statTotal.textContent = total;
    if (statAC) statAC.textContent = acCount;
    if (statRate) statRate.textContent = `${rate}%`;
    if (statUsers) statUsers.textContent = uniqueUsers;

    // Language breakdown
    const langCounts = {};
    allSubmissions.forEach(s => {
      const l = s.language || 'CPP17';
      langCounts[l] = (langCounts[l] || 0) + 1;
    });

    const statLangs = document.getElementById('statLangs');
    if (statLangs) {
      statLangs.innerHTML = Object.entries(langCounts).map(([lang, count]) => {
        const pct = total ? Math.round((count / total) * 100) : 0;
        return `
          <div>
            <div style="display:flex;justify-content:space-between;font-size:.82rem;margin-bottom:3px;">
              <span style="font-family:monospace;color:#cbd5e1;">${lang}</span>
              <span style="color:#94a3b8;">${count} (${pct}%)</span>
            </div>
            <div style="background:rgba(255,255,255,.06);height:6px;border-radius:3px;overflow:hidden;">
              <div style="background:#3b82f6;width:${pct}%;height:100%;"></div>
            </div>
          </div>
        `;
      }).join('');
    }

    // Verdict breakdown
    const verCounts = {};
    allSubmissions.forEach(s => {
      const v = s.result || 'WA';
      verCounts[v] = (verCounts[v] || 0) + 1;
    });

    const statVerdicts = document.getElementById('statVerdicts');
    if (statVerdicts) {
      statVerdicts.innerHTML = Object.entries(verCounts).map(([ver, count]) => {
        const vClass = `vb-${ver}`;
        return `
          <div style="background:rgba(255,255,255,.04);border:1px solid var(--color-border);padding:.4rem .8rem;border-radius:6px;display:flex;align-items:center;gap:.5rem;">
            <span class="vb ${vClass}">${ver}</span>
            <strong style="color:#fff;font-size:.85rem;">${count}</strong>
          </div>
        `;
      }).join('');
    }
  }

  window.copyCodeText = function() {
    navigator.clipboard.writeText(CODE);
    alert(`Đã sao chép mã bài: ${CODE}`);
  };

  // ══════════════ MODALS: VIEW SOURCE & VIEW RESULT ══════════════
  let currentSourceText = '';

  function escapeHtml(str) {
    if (!str) return '';
    return String(str)
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;')
      .replace(/'/g, '&#039;');
  }

  window.closeSourceModal = function() {
    const modal = document.getElementById('modalSourceCode');
    if (modal) modal.style.display = 'none';
  };

  window.closeResultModal = function() {
    const modal = document.getElementById('modalSubmissionResult');
    if (modal) modal.style.display = 'none';
  };

  // Close modals on Escape key
  document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape') {
      window.closeSourceModal();
      window.closeResultModal();
    }
  });

  window.copySourceCode = function() {
    if (!currentSourceText) return;
    navigator.clipboard.writeText(currentSourceText).then(() => {
      const btnText = document.getElementById('copySourceText');
      if (btnText) {
        btnText.textContent = '✓ Đã chép!';
        setTimeout(() => { btnText.textContent = 'Sao chép mã'; }, 2000);
      }
    }).catch(err => {
      console.warn('Copy failed:', err);
    });
  };

  window.viewSource = async function(subId) {
    const modal = document.getElementById('modalSourceCode');
    if (!modal) return;

    const titleEl = document.getElementById('modalSrcTitle');
    const subTitleEl = document.getElementById('modalSrcSubtitle');
    const metaEl = document.getElementById('modalSrcMeta');
    const codeEl = document.getElementById('modalSrcCode');
    const linkEl = document.getElementById('modalSrcFullLink');

    titleEl.textContent = `Mã nguồn bài nộp #${subId}`;
    subTitleEl.textContent = 'Đang tải mã nguồn từ máy chủ...';
    metaEl.innerHTML = `<span style="color:#94a3b8;"><div class="spinner-sm" style="display:inline-block;vertical-align:middle;margin-right:6px;"></div>Đang tải thông tin bài nộp...</span>`;
    codeEl.textContent = '// Đang tải mã nguồn...';
    if (linkEl) linkEl.href = `/submissions/${subId}`;
    modal.style.display = 'flex';

    try {
      const res = await fetch(`/api/v2/submission/${subId}`);
      const data = await res.json();
      const s = data.data ? data.data.object : (data.object || data);

      if (!s) {
        codeEl.textContent = '// Không thể tải bài nộp hoặc bài nộp không tồn tại.';
        return;
      }

      currentSourceText = s.source || '';
      titleEl.textContent = `Mã nguồn bài nộp #${s.id} (${s.language || '—'})`;
      subTitleEl.textContent = `Bài tập: ${s.problem} • Thí sinh: ${s.user} • Nộp lúc: ${s.date ? new Date(s.date).toLocaleString('vi-VN') : '—'}`;

      const isAC = s.result === 'AC';
      const vClass = `vb-${s.result || 'WA'}`;
      const timeMs = s.time != null ? Math.round(parseFloat(s.time) * 1000) + ' ms' : '—';
      const memMB = s.memory != null ? parseFloat(s.memory).toFixed(1) + ' MB' : '—';

      metaEl.innerHTML = `
        <span class="vb ${vClass}">${s.result || 'Pending'}</span>
        <span style="color:${isAC ? '#34d399' : '#f87171'};font-weight:700;">${s.points != null ? s.points : 0} điểm</span>
        <span style="color:#94a3b8;">Thời gian: <strong style="color:#f59e0b;">${timeMs}</strong></span>
        <span style="color:#94a3b8;">Bộ nhớ: <strong style="color:#a78bfa;">${memMB}</strong></span>
        <span style="color:#94a3b8;">Ngôn ngữ: <strong style="color:#60a5fa;">${s.language || '—'}</strong></span>
      `;

      codeEl.textContent = currentSourceText || '// Bài nộp không có mã nguồn hoặc mã nguồn rỗng.';
    } catch (err) {
      console.error('Error fetching source code:', err);
      codeEl.textContent = '// Lỗi kết nối khi tải mã nguồn bài nộp.';
    }
  };

  window.viewResult = async function(subId) {
    const modal = document.getElementById('modalSubmissionResult');
    if (!modal) return;

    const titleEl = document.getElementById('modalResTitle');
    const subTitleEl = document.getElementById('modalResSubtitle');
    const summaryEl = document.getElementById('modalResSummary');
    const errorBox = document.getElementById('modalResError');
    const errorText = document.getElementById('modalResErrorText');
    const countEl = document.getElementById('modalResCasesCount');
    const casesTbody = document.getElementById('modalResCasesTbody');
    const linkEl = document.getElementById('modalResFullLink');

    titleEl.textContent = `Chi tiết kết quả bài nộp #${subId}`;
    subTitleEl.textContent = 'Đang tải dữ liệu từ máy chủ...';
    summaryEl.innerHTML = `<div style="grid-column:1/-1;text-align:center;padding:1rem;color:#94a3b8;"><div class="spinner-sm" style="display:inline-block;vertical-align:middle;margin-right:6px;"></div> Đang tải kết quả...</div>`;
    errorBox.style.display = 'none';
    casesTbody.innerHTML = `<tr><td colspan="6" style="text-align:center;padding:2rem;color:#94a3b8;">Đang tải danh sách test cases...</td></tr>`;
    if (linkEl) linkEl.href = `/submissions/${subId}`;
    modal.style.display = 'flex';

    try {
      const res = await fetch(`/api/v2/submission/${subId}`);
      const data = await res.json();
      const s = data.data ? data.data.object : (data.object || data);

      if (!s) {
        casesTbody.innerHTML = `<tr><td colspan="6" style="text-align:center;padding:2rem;color:#f87171;">Không thể tải bài nộp này.</td></tr>`;
        return;
      }

      titleEl.textContent = `Chi tiết kết quả bài nộp #${s.id}`;
      subTitleEl.textContent = `Bài tập: ${s.problem} • Thí sinh: ${s.user} • Ngôn ngữ: ${s.language} • Nộp lúc: ${s.date ? new Date(s.date).toLocaleString('vi-VN') : '—'}`;

      const isAC = s.result === 'AC';
      const vClass = `vb-${s.result || 'WA'}`;
      const timeMs = s.time != null ? Math.round(parseFloat(s.time) * 1000) + ' ms' : '—';
      const memMB = s.memory != null ? parseFloat(s.memory).toFixed(1) + ' MB' : '—';
      const points = s.points != null ? s.points : 0;

      // Summary cards
      summaryEl.innerHTML = `
        <div style="background:rgba(255,255,255,.04);border:1px solid var(--color-border);border-radius:8px;padding:.75rem;text-align:center;">
          <div style="font-size:.75rem;color:#94a3b8;margin-bottom:.3rem;">Phán quyết</div>
          <span class="vb ${vClass}" style="font-size:.85rem;padding:.2rem .7rem;">${s.result || 'Pending'}</span>
        </div>
        <div style="background:rgba(255,255,255,.04);border:1px solid var(--color-border);border-radius:8px;padding:.75rem;text-align:center;">
          <div style="font-size:.75rem;color:#94a3b8;margin-bottom:.3rem;">Điểm số</div>
          <div style="font-size:1.25rem;font-weight:800;color:${isAC ? '#34d399' : '#f87171'};">${points}đ</div>
        </div>
        <div style="background:rgba(255,255,255,.04);border:1px solid var(--color-border);border-radius:8px;padding:.75rem;text-align:center;">
          <div style="font-size:.75rem;color:#94a3b8;margin-bottom:.3rem;">Thời gian</div>
          <div style="font-size:1.05rem;font-weight:700;color:#f59e0b;font-family:monospace;">${timeMs}</div>
        </div>
        <div style="background:rgba(255,255,255,.04);border:1px solid var(--color-border);border-radius:8px;padding:.75rem;text-align:center;">
          <div style="font-size:.75rem;color:#94a3b8;margin-bottom:.3rem;">Bộ nhớ</div>
          <div style="font-size:1.05rem;font-weight:700;color:#a78bfa;font-family:monospace;">${memMB}</div>
        </div>
        <div style="background:rgba(255,255,255,.04);border:1px solid var(--color-border);border-radius:8px;padding:.75rem;text-align:center;">
          <div style="font-size:.75rem;color:#94a3b8;margin-bottom:.3rem;">Ngôn ngữ</div>
          <div style="font-size:.95rem;font-weight:700;color:#60a5fa;font-family:monospace;">${s.language || '—'}</div>
        </div>
      `;

      // Error message display
      if (s.error && s.error.trim()) {
        errorBox.style.display = 'block';
        errorText.textContent = s.error;
      } else {
        errorBox.style.display = 'none';
      }

      // Test cases list
      const cases = (s.test_cases || []).slice().sort((a, b) => (a.case || 0) - (b.case || 0));
      countEl.textContent = cases.length;

      if (!cases.length) {
        casesTbody.innerHTML = `<tr><td colspan="6" style="text-align:center;padding:2rem;color:#94a3b8;">Không có dữ liệu test cases chi tiết cho bài nộp này.</td></tr>`;
      } else {
        casesTbody.innerHTML = cases.map(tc => {
          const cAC = tc.status === 'AC';
          const tcClass = `vb-${tc.status || 'WA'}`;
          const tcTime = tc.time != null ? Math.round(parseFloat(tc.time) * 1000) + ' ms' : '—';
          const tcMem = tc.memory != null ? parseFloat(tc.memory).toFixed(1) + ' MB' : '—';
          const pts = tc.points != null ? parseFloat(tc.points).toFixed(1) : '—';
          const totalPts = tc.total_points != null ? parseFloat(tc.total_points).toFixed(1) : '—';
          const fb = escapeHtml(tc.feedback || (cAC ? 'Chấp nhận (Đúng kết quả)' : (tc.status || '')));

          return `
            <tr>
              <td style="text-align:center;font-weight:700;font-family:monospace;color:#94a3b8;">#${tc.case}</td>
              <td><span class="vb ${tcClass}">${tc.status}</span></td>
              <td style="font-weight:600;color:${cAC ? '#34d399' : '#f87171'};">${pts} / ${totalPts}</td>
              <td style="font-family:monospace;color:#cbd5e1;">${tcTime}</td>
              <td style="font-family:monospace;color:#cbd5e1;">${tcMem}</td>
              <td style="color:#94a3b8;font-size:.82rem;">${fb}</td>
            </tr>
          `;
        }).join('');
      }
    } catch (err) {
      console.error('Error fetching submission result:', err);
      casesTbody.innerHTML = `<tr><td colspan="6" style="text-align:center;padding:2rem;color:#f87171;">Lỗi kết nối khi tải chi tiết kết quả.</td></tr>`;
    }
  };

  fetchProblem();
})();

