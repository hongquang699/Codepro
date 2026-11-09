/**
 * CodeProOJ - TMath Coding Style Submission Detail Controller
 */

let currentSubId = null;
let pollTimer = null;

function escapeHtml(str) {
  if (str == null) return '';
  return String(str)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#039;');
}

function getVerdictInfo(verdict, isGrading) {
  const v = (verdict || '').toUpperCase();
  if (isGrading || ['QUEUED', 'JUDGING', 'COMPILING', 'RUNNING', 'CHECKING', 'PENDING', 'P', 'J'].includes(v)) {
    return {
      cssClass: 'verdict-hero-judging',
      badgeClass: 'tle',
      title: '⏳ ĐANG CHẤM BÀI...',
      subtitle: 'Hệ thống Sandbox đang thực thi mã nguồn qua các bộ test...'
    };
  }

  switch (v) {
    case 'AC':
    case 'ACCEPTED':
      return {
        cssClass: 'verdict-hero-ac',
        badgeClass: 'ac',
        title: '✔ CHẤP NHẬN (ACCEPTED)',
        subtitle: 'Lời giải hoàn toàn chính xác và đã vượt qua tất cả các bộ dữ liệu test.'
      };
    case 'WA':
    case 'WRONG ANSWER':
      return {
        cssClass: 'verdict-hero-wa',
        badgeClass: 'wa',
        title: '✖ KẾT QUẢ SAI (WRONG ANSWER)',
        subtitle: 'Kết quả đầu ra không khớp với đáp án chuẩn tại một số bộ test.'
      };
    case 'TLE':
    case 'TIME LIMIT EXCEEDED':
      return {
        cssClass: 'verdict-hero-tle',
        badgeClass: 'tle',
        title: '⏱ QUÁ THỜI GIAN (TIME LIMIT EXCEEDED)',
        subtitle: 'Thuật toán vượt quá giới hạn thời gian cho phép của bài toán.'
      };
    case 'MLE':
    case 'MEMORY LIMIT EXCEEDED':
      return {
        cssClass: 'verdict-hero-mle',
        badgeClass: 'mle',
        title: '💾 QUÁ BỘ NHỚ (MEMORY LIMIT EXCEEDED)',
        subtitle: 'Chương trình sử dụng vượt quá dung lượng bộ nhớ RAM cho phép.'
      };
    case 'RTE':
    case 'RUNTIME ERROR':
      return {
        cssClass: 'verdict-hero-rte',
        badgeClass: 'rte',
        title: '💥 LỖI THỰC THI (RUNTIME ERROR)',
        subtitle: 'Chương trình kết thúc bất thường (Segmentation fault, chia cho 0, exception).'
      };
    case 'CE':
    case 'COMPILATION ERROR':
      return {
        cssClass: 'verdict-hero-ce',
        badgeClass: 'ce',
        title: '🔧 LỖI BIÊN DỊCH (COMPILATION ERROR)',
        subtitle: 'Mã nguồn không thể biên dịch thành công. Vui lòng xem log chi tiết bên dưới.'
      };
    default:
      return {
        cssClass: 'verdict-hero-wa',
        badgeClass: 'wa',
        title: `${v || 'KẾT QUẢ ĐÃ CHẤM'}`,
        subtitle: 'Chi tiết bài nộp đã được cập nhật từ máy chấm.'
      };
  }
}

async function loadSubmission(id) {
  currentSubId = id;
  clearTimeout(pollTimer);

  let sub = null;

  // 1. Try API v2
  try {
    const res2 = await fetch(`/api/v2/submission/${id}`);
    if (res2.ok) {
      const j2 = await res2.json();
      if (j2.data && j2.data.object) {
        sub = j2.data.object;
      }
    }
  } catch (e) {
    console.warn("API v2 submission fetch failed, trying v1...", e);
  }

  // 2. Fallback to API v1 if v2 failed
  if (!sub) {
    try {
      const res1 = await fetch(`/api/v1/submissions/${id}/`);
      if (res1.ok) {
        const j1 = await res1.json();
        sub = {
          id: j1.id,
          problem: typeof j1.problem === 'object' ? j1.problem.code : j1.problem,
          problem_name: typeof j1.problem === 'object' ? j1.problem.name : '',
          user: typeof j1.user === 'object' ? j1.user.username : j1.user,
          date: j1.created_at,
          time: (j1.execution_time || 0) / 1000,
          memory: j1.memory_used || 0,
          points: j1.score,
          result: j1.verdict,
          status: j1.status === 'FINISHED' ? 'D' : 'P',
          language: typeof j1.language === 'object' ? j1.language.name : j1.language,
          source: j1.source_code || '',
          error: j1.error || '',
          test_cases: j1.testcases || []
        };
      }
    } catch (e) {
      console.error("API v1 submission fetch failed:", e);
    }
  }

  if (!sub) {
    document.getElementById('verdictHero').className = 'verdict-hero-card verdict-hero-wa';
    document.getElementById('verdictTitle').textContent = '⚠️ Không tìm thấy bài nộp';
    document.getElementById('verdictSubtitle').textContent = `Mã bài nộp #${id} không tồn tại trên hệ thống hoặc đã bị xóa.`;
    return;
  }

  renderSubmissionDetails(sub);

  // Poll if submission is still in progress
  const v = (sub.result || sub.verdict || '').toUpperCase();
  const isPending = ['P', 'J', 'QUEUED', 'JUDGING', 'COMPILING', 'RUNNING', 'CHECKING', 'PENDING'].includes(sub.status) ||
                    ['QUEUED', 'JUDGING', 'COMPILING', 'RUNNING', 'CHECKING', 'PENDING'].includes(v);
  if (isPending) {
    pollTimer = setTimeout(() => {
      loadSubmission(id);
    }, 1200);
  }
}

async function renderSubmissionDetails(sub) {
  const probCode = (sub.problem || 'APLUS').trim().toUpperCase();
  document.getElementById('docTitle').textContent = `Bài nộp #${sub.id} [${probCode}] | CodeProOJ`;
  document.getElementById('headerSubId').textContent = sub.id;
  document.getElementById('breadSubId').textContent = sub.id;
  document.getElementById('headerUsername').textContent = sub.user || 'Thí sinh';

  // Problem Link & Name
  const probLink = `/problem?code=${encodeURIComponent(probCode)}`;
  const submitLink = `/submit?code=${encodeURIComponent(probCode)}`;

  document.getElementById('btnResubmit').href = submitLink;
  document.getElementById('btnViewProblem').href = probLink;
  document.getElementById('breadProbLink').href = probLink;
  document.getElementById('headerProbLink').href = probLink;

  // Fetch problem name if not already cached
  if (!sub.problem_name) {
    try {
      const pRes = await fetch(`/api/v2/problem/${encodeURIComponent(probCode)}`);
      if (pRes.ok) {
        const pj = await pRes.json();
        const pObj = pj.data?.object || pj.data;
        if (pObj && pObj.name) {
          sub.problem_name = pObj.name;
        }
      }
    } catch (e) {}
  }

  const fullProbTitle = `[${probCode}] ${sub.problem_name || probCode}`;
  document.getElementById('breadProbText').textContent = fullProbTitle;
  document.getElementById('headerProbLink').textContent = fullProbTitle;

  // Verdict Hero Banner
  const isJudging = ['P', 'J', 'QUEUED', 'JUDGING', 'COMPILING', 'RUNNING', 'CHECKING', 'PENDING'].includes(sub.status) ||
                    ['QUEUED', 'JUDGING', 'COMPILING', 'RUNNING', 'CHECKING', 'PENDING'].includes((sub.result || '').toUpperCase());
  const vInfo = getVerdictInfo(sub.result || sub.verdict, isJudging);

  const hero = document.getElementById('verdictHero');
  hero.className = `verdict-hero-card ${vInfo.cssClass}`;
  document.getElementById('verdictTitle').textContent = vInfo.title;
  document.getElementById('verdictSubtitle').textContent = vInfo.subtitle;

  // Stats Grid
  const pts = sub.points != null ? sub.points : (sub.score != null ? sub.score : 0);
  const scoreEl = document.getElementById('statScore');
  scoreEl.textContent = `${pts} / 100`;
  if (pts >= 100) {
    scoreEl.style.color = '#10b981';
  } else if (pts > 0) {
    scoreEl.style.color = '#f59e0b';
  } else {
    scoreEl.style.color = '#ef4444';
  }

  // Execution Time
  const timeSeconds = sub.time != null ? sub.time : ((sub.execution_time || 0) / 1000);
  const timeMs = Math.round(timeSeconds * 1000);
  document.getElementById('statTime').textContent = `${timeMs} ms`;

  // Memory
  const memMb = sub.memory != null ? parseFloat(sub.memory) : (sub.memory_used || 0);
  document.getElementById('statMemory').textContent = `${memMb.toFixed(1)} MB`;

  // Language & Date
  document.getElementById('statLang').textContent = sub.language || 'C++17';
  document.getElementById('sourceLangTag').textContent = sub.language || 'C++17';

  if (sub.date) {
    try {
      const d = new Date(sub.date);
      document.getElementById('statDate').textContent = d.toLocaleString('vi-VN', {
        hour: '2-digit', minute: '2-digit', second: '2-digit',
        day: '2-digit', month: '2-digit', year: 'numeric'
      });
    } catch (e) {
      document.getElementById('statDate').textContent = sub.date;
    }
  }

  // Compiler Box
  const cBox = document.getElementById('compilerBox');
  if (sub.error && sub.error.trim()) {
    cBox.textContent = `[Compiler Output / Warning]\n${sub.error.trim()}`;
    cBox.style.display = 'block';
  } else {
    cBox.style.display = 'none';
  }

  // Testcases Table Breakdown
  const tcList = sub.test_cases || sub.testcases || [];
  const tcBody = document.getElementById('testcaseTableBody');
  const countBadge = document.getElementById('testcaseCountBadge');

  if (tcList.length > 0) {
    const acCount = tcList.filter(tc => (tc.status || '').toUpperCase() === 'AC').length;
    countBadge.textContent = `${acCount} / ${tcList.length} Passed`;
    countBadge.style.color = acCount === tcList.length ? '#34d399' : '#f59e0b';

    tcBody.innerHTML = tcList.map((tc, idx) => {
      const st = (tc.status || 'AC').toUpperCase();
      let badgeClass = 'ac';
      let icon = '✔';
      if (st === 'WA') { badgeClass = 'wa'; icon = '✖'; }
      else if (st === 'TLE') { badgeClass = 'tle'; icon = '⏱'; }
      else if (st === 'MLE') { badgeClass = 'mle'; icon = '💾'; }
      else if (st === 'RTE') { badgeClass = 'rte'; icon = '💥'; }
      else if (st === 'CE') { badgeClass = 'ce'; icon = '🔧'; }

      const tcTime = tc.time != null ? `${(tc.time < 1 ? Math.round(tc.time * 1000) + ' ms' : tc.time.toFixed(2) + ' s')}` : '--';
      const tcMem = tc.memory != null ? `${parseFloat(tc.memory).toFixed(1)} MB` : '--';
      const tcPts = tc.points != null ? tc.points : '--';
      const tcTotPts = tc.total_points != null ? tc.total_points : '--';
      const tcFeedback = tc.feedback || (st === 'AC' ? 'Correct answer' : st);

      return `
        <tr>
          <td style="font-weight:700;font-family:monospace;color: var(--color-text-muted);">#${escapeHtml(tc.case || idx + 1)}</td>
          <td>
            <span class="tc-badge ${badgeClass}">${icon} ${escapeHtml(st)}</span>
          </td>
          <td style="font-family:monospace;color: #f59e0b;">${tcTime}</td>
          <td style="font-family:monospace;color: var(--color-accent);">${tcMem}</td>
          <td style="font-weight:700;color: ${st === 'AC' ? '#34d399' : '#94a3b8'};font-family:monospace;">
            ${escapeHtml(tcPts)} / ${escapeHtml(tcTotPts)}
          </td>
          <td style="font-size:0.86rem;color: var(--color-text-secondary);">
            ${escapeHtml(tcFeedback)}
          </td>
        </tr>
      `;
    }).join('');
  } else {
    countBadge.textContent = isJudging ? 'Đang chấm...' : '0 test';
    tcBody.innerHTML = `
      <tr>
        <td colspan="6" style="text-align: center; padding: 28px; color: var(--color-text-muted);">
          ${isJudging ? '<span class="btn-spin" style="margin-right:8px;vertical-align:middle;"></span> Đang xử lý các bộ test...' : 'Không có thông tin chi tiết từng testcase.'}
        </td>
      </tr>
    `;
  }

  // Source Code Viewer
  const srcViewer = document.getElementById('sourceCodeViewer');
  if (sub.source && sub.source.trim()) {
    srcViewer.textContent = sub.source;
  } else {
    srcViewer.textContent = '// Không có dữ liệu mã nguồn đã nộp.';
  }
}

// Rejudge Handler
window.triggerRejudge = async function() {
  if (!currentSubId) return;
  const btn = document.getElementById('btnRejudge');
  btn.disabled = true;
  btn.innerHTML = `<span class="btn-spin" style="width:14px;height:14px;border-width:2px;margin-right:4px;"></span> Đang yêu cầu chấm lại...`;

  try {
    const res = await fetch(`/api/v2/rejudge/${currentSubId}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({})
    });
    const j = await res.json();
    if (res.ok) {
      document.getElementById('verdictHero').className = 'verdict-hero-card verdict-hero-judging';
      document.getElementById('verdictTitle').innerHTML = '⏳ ĐANG CHẤM LẠI...';
      document.getElementById('verdictSubtitle').textContent = 'Hệ thống đã nhận yêu cầu chấm lại và đang gửi tới máy chấm sandbox...';
      setTimeout(() => loadSubmission(currentSubId), 800);
    } else {
      alert('Lỗi chấm lại: ' + (j.error || j.message || 'Không thể chấm lại'));
    }
  } catch (err) {
    alert('Lỗi kết nối máy chủ khi chấm lại: ' + err.message);
  } finally {
    btn.disabled = false;
    btn.innerHTML = `<cp-icon name="refresh" size="xs"></cp-icon> Chấm lại`;
  }
};

// Copy Code Handler
document.addEventListener('DOMContentLoaded', () => {
  const btnCopy = document.getElementById('btnCopyCode');
  if (btnCopy) {
    btnCopy.addEventListener('click', () => {
      const code = document.getElementById('sourceCodeViewer').textContent;
      navigator.clipboard.writeText(code).then(() => {
        btnCopy.innerHTML = `<cp-icon name="check" size="xs"></cp-icon> Đã sao chép!`;
        setTimeout(() => {
          btnCopy.innerHTML = `<cp-icon name="document" size="xs"></cp-icon> Sao chép mã`;
        }, 2000);
      });
    });
  }

  // Extract ID from pathname or query param
  let subId = null;
  const pathParts = window.location.pathname.split('/').filter(Boolean);
  const subIdx = pathParts.findIndex(p => p === 'submissions' || p === 'submission');
  if (subIdx !== -1 && pathParts[subIdx + 1] && !isNaN(pathParts[subIdx + 1])) {
    subId = parseInt(pathParts[subIdx + 1], 10);
  } else {
    const params = new URLSearchParams(window.location.search);
    subId = parseInt(params.get('id'), 10);
  }

  if (subId) {
    loadSubmission(subId);
  } else {
    document.getElementById('verdictHero').className = 'verdict-hero-card verdict-hero-wa';
    document.getElementById('verdictTitle').textContent = '⚠️ Thiếu mã bài nộp';
    document.getElementById('verdictSubtitle').textContent = 'Vui lòng cung cấp mã bài nộp hợp lệ trên URL (ví dụ: /submissions/61 hoặc ?id=61).';
  }
});
