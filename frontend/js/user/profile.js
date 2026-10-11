/**
 * CodeProOJ - User Profile Logic (CodeProOJ Style)
 * Handles profile fetching, rating tier colorization,
 * submission breakdown tabs (All, AC, WA, Other),
 * 52-week activity heatmap, solved problems list,
 * language usage statistics, and canvas rating history chart.
 */

(() => {
  const API = (typeof window.API_BASE === 'string') ? window.API_BASE : '';
  const urlParams = new URLSearchParams(window.location.search);
  function getTargetUser() {
    const fromUrl = urlParams.get('u') || urlParams.get('user');
    if (fromUrl) return fromUrl;
    const parts = window.location.pathname.split('/').filter(Boolean);
    const pIdx = parts.indexOf('profile');
    if (pIdx !== -1 && parts[pIdx + 1] && !parts[pIdx + 1].endsWith('.html')) {
      return decodeURIComponent(parts[pIdx + 1]);
    }
    try {
      const u = JSON.parse(localStorage.getItem('user'));
      if (u && u.username) return u.username;
    } catch (e) {}
    return localStorage.getItem('username') || '';
  }
  const targetUser = getTargetUser();

  // Rating color helper
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

  function rankLabel(r) {
    if (typeof CPRating !== 'undefined') return CPRating.getRankName(r);
    const num = parseInt(r, 10);
    if (isNaN(num) || num <= 0) return 'Unrated';
    if (num >= 3000) return 'Legendary Grandmaster';
    if (num >= 2400) return 'Grandmaster';
    if (num >= 2100) return 'Master';
    if (num >= 1900) return 'Candidate Master';
    if (num >= 1600) return 'Expert';
    if (num >= 1400) return 'Specialist';
    if (num >= 1200) return 'Pupil';
    return 'Newbie';
  }

  const VMAP = {
    AC: { cls: 'vAC', icon: '✅', txt: 'AC' },
    WA: { cls: 'vWA', icon: '❌', txt: 'WA' },
    TLE: { cls: 'vTLE', icon: '⏱', txt: 'TLE' },
    MLE: { cls: 'vMLE', icon: '💾', txt: 'MLE' },
    RTE: { cls: 'vRE', icon: '💥', txt: 'RE' },
    CE: { cls: 'vCE', icon: '🔧', txt: 'CE' },
    G: { cls: 'vJudging', icon: '⏳', txt: 'Judging' },
    QU: { cls: 'vJudging', icon: '📥', txt: 'Queue' }
  };

  function vBadge(v) {
    const c = VMAP[v] || { cls: 'vCE', icon: '❓', txt: v };
    return `<span class="verdict-badge ${c.cls}">${c.icon} ${c.txt}</span>`;
  }

  function fTime(t) { return t != null ? Math.round(parseFloat(t) * 1000) + ' ms' : '—'; }
  function fMem(m) { return m != null ? parseFloat(m).toFixed(1) + ' MB' : '—'; }
  function fDate(d) {
    if (!d) return '—';
    const dt = new Date(d);
    return dt.toLocaleDateString('vi', { day: '2-digit', month: '2-digit', year: '2-digit' })
      + ' ' + dt.toLocaleTimeString('vi', { hour: '2-digit', minute: '2-digit' });
  }

  const sections = ['subs', 'solved', 'activity', 'rating'];
  window.switchSection = function(name) {
    sections.forEach(s => {
      const el = document.getElementById('sec-' + s);
      if (el) el.style.display = (s === name) ? '' : 'none';
    });
    document.querySelectorAll('.sidebar-link').forEach((l, i) => {
      l.classList.toggle('active', sections[i] === name);
    });
    if (name === 'activity') renderHeatmap();
    if (name === 'rating') renderRatingChart();
    if (name === 'solved') renderSolvedProblems();
    return false;
  };

  let currentTab = 'all';
  window.switchTab = function(name, btn) {
    currentTab = name;
    document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
    document.querySelectorAll('.tab-panel').forEach(p => p.classList.remove('active'));
    if (btn) btn.classList.add('active');
    const targetPanel = document.getElementById('tp-' + name);
    if (targetPanel) targetPanel.classList.add('active');
    renderSubTable();
  };

  let allSubs = [];
  let profile = {};

  function buildRows(subs) {
    if (!subs.length) return `<tr><td colspan="8"><div class="empty-box"><div class="eico">📭</div>Không có bài nộp.</div></td></tr>`;
    return subs.map(s => `
      <tr>
        <td><a class="sub-lnk" href="/frontend/html/submission/submission.html?id=${s.id}">#${s.id}</a></td>
        <td><a class="prob-lnk" href="/frontend/html/problem/problem.html?code=${s.problem}">${s.problem}</a></td>
        <td>${vBadge(s.result || s.status || 'QU')}</td>
        <td style="font-weight:700;color:var(--color-primary);">${s.points != null ? s.points : '—'}</td>
        <td style="font-family:monospace;font-size:.78rem;color:var(--color-text-muted);">${fTime(s.time)}</td>
        <td style="font-family:monospace;font-size:.78rem;color:var(--color-text-muted);">${fMem(s.memory)}</td>
        <td><span class="lang-pill">${s.language || '—'}</span></td>
        <td style="font-size:.78rem;color:var(--color-text-muted);">${fDate(s.date)}</td>
      </tr>
    `).join('');
  }

  window.renderSubTable = function() {
    const probInput = document.getElementById('filterProb');
    const langSelect = document.getElementById('filterLang');
    const sortSelect = document.getElementById('sortBy');

    const prob = (probInput ? probInput.value : '').trim().toLowerCase();
    const lang = langSelect ? langSelect.value : '';
    const sort = sortSelect ? sortSelect.value : 'date-desc';

    let filtered = allSubs.filter(s => {
      if (prob && !(s.problem || '').toLowerCase().includes(prob)) return false;
      if (lang && s.language !== lang) return false;
      if (currentTab === 'ac' && s.result !== 'AC') return false;
      if (currentTab === 'wa' && s.result !== 'WA') return false;
      if (currentTab === 'other' && !['TLE', 'MLE', 'RTE', 'RE', 'CE', 'SE'].includes(s.result)) return false;
      return true;
    });

    filtered.sort((a, b) => {
      if (sort === 'date-asc') return new Date(a.date) - new Date(b.date);
      if (sort === 'pts-desc') return (parseFloat(b.points) || 0) - (parseFloat(a.points) || 0);
      if (sort === 'time-asc') return (parseFloat(a.time) || 99) - (parseFloat(b.time) || 99);
      return new Date(b.date) - new Date(a.date);
    });

    const info = document.getElementById('subCountInfo');
    if (info) info.textContent = `${filtered.length} bài nộp`;

    ['all', 'ac', 'wa', 'other'].forEach(tab => {
      const tBody = document.getElementById('tbody-' + tab);
      if (tab === currentTab && tBody) tBody.innerHTML = buildRows(filtered);
    });
  };

  function updateCounts() {
    const total = allSubs.length;
    const ac = allSubs.filter(s => s.result === 'AC').length;
    const wa = allSubs.filter(s => s.result === 'WA').length;
    const other = allSubs.filter(s => ['TLE', 'MLE', 'RTE', 'RE', 'CE', 'SE'].includes(s.result)).length;
    const acRate = total ? Math.round(ac / total * 100) : 0;

    const cntAll = document.getElementById('cnt-all');
    const cntAc = document.getElementById('cnt-ac');
    const cntWa = document.getElementById('cnt-wa');
    const cntOther = document.getElementById('cnt-other');
    const statSub = document.getElementById('sTotalSub');
    const statRate = document.getElementById('sAcRate');

    if (cntAll) cntAll.textContent = total;
    if (cntAc) cntAc.textContent = ac;
    if (cntWa) cntWa.textContent = wa;
    if (cntOther) cntOther.textContent = other;
    if (statSub) statSub.textContent = total;
    if (statRate) statRate.textContent = total ? acRate + '%' : '—';
  }

  window.loadSubs = async function() {
    try {
      const resp = await fetch(`${API}/api/v2/submissions?user=${encodeURIComponent(targetUser)}`);
      const json = await resp.json();
      allSubs = json?.data?.objects || [];
      updateCounts();
      renderSubTable();
    } catch (e) {
      const tBody = document.getElementById('tbody-all');
      if (tBody) {
        tBody.innerHTML = `<tr><td colspan="8" class="empty-box" style="color:#ef4444;">⚠ Không thể tải dữ liệu: ${e.message}</td></tr>`;
      }
    }
  };

  async function loadProfile() {
    try {
      const resp = await fetch(`${API}/api/v2/user/${encodeURIComponent(targetUser)}`);
      const json = await resp.json();
      const u = json?.data?.object;
      if (!u) return;

      profile = u;
      const rating = (u.rating != null && !isNaN(parseInt(u.rating, 10))) ? parseInt(u.rating, 10) : 0;
      const color = ratingColor(rating);
      const label = rankLabel(rating);

      document.title = `${u.username} | CodeProOJ`;

      const av = document.getElementById('avatarCircle');
      if (av) {
        av.style.background = color;
        av.textContent = (u.username || 'U')[0].toUpperCase();
      }

      const uDisp = document.getElementById('usernameDisplay');
      if (uDisp) {
        uDisp.textContent = u.username;
        uDisp.style.color = color;
      }

      const rankEl = document.getElementById('rankBadge');
      if (rankEl) {
        rankEl.textContent = u.display_rank || label;
        rankEl.style.background = color + '22';
        rankEl.style.color = color;
        rankEl.style.border = '1px solid ' + color + '44';
      }

      const sRating = document.getElementById('sRating');
      const sPts = document.getElementById('sPoints');
      const sSolved = document.getElementById('sSolved');
      const sOrg = document.getElementById('sOrg');
      const sSince = document.getElementById('userSince');
      const crBig = document.getElementById('currentRatingBig');

      if (sRating) {
        sRating.textContent = rating;
        sRating.style.color = color;
      }
      if (sPts) sPts.textContent = u.points || 0;
      if (sSolved) sSolved.textContent = u.problem_count || 0;
      if (sOrg) sOrg.textContent = (u.organizations && u.organizations.length) ? u.organizations[0]?.name || '—' : '—';

      if (u.date_joined && sSince) {
        const joined = new Date(u.date_joined);
        sSince.textContent = 'Thành viên từ ' + joined.toLocaleDateString('vi', { year: 'numeric', month: 'long', day: 'numeric' });
      }

      if (crBig) {
        crBig.textContent = rating;
        crBig.style.color = color;
      }
    } catch (e) {
      console.warn('Error loading user profile:', e);
    }
  }

  function renderSolvedProblems() {
    const solved = allSubs.filter(s => s.result === 'AC');
    const unique = [...new Map(solved.map(s => [s.problem, s])).values()];

    const sCount = document.getElementById('solvedCount');
    if (sCount) sCount.textContent = unique.length;

    const grid = document.getElementById('solvedGrid');
    if (grid) {
      if (!unique.length) {
        grid.innerHTML = `<div class="empty-box"><div class="eico">📭</div>Chưa giải được bài nào.</div>`;
      } else {
        grid.innerHTML = unique.map(s =>
          `<a class="prob-chip" href="/frontend/html/problem/problem.html?code=${s.problem}">${s.problem}</a>`
        ).join('');
      }
    }

    const langFreq = {};
    allSubs.forEach(s => { langFreq[s.language] = (langFreq[s.language] || 0) + 1; });
    const sorted = Object.entries(langFreq).sort((a, b) => b[1] - a[1]);
    const tagList = document.getElementById('tagList');
    if (tagList) {
      tagList.innerHTML = sorted.map(([lang, cnt]) =>
        `<div class="tag-pill"><span>💻 ${lang}</span><span class="cnt">${cnt}</span></div>`
      ).join('') || '<div style="color:var(--color-text-muted);">Không có dữ liệu.</div>';
    }
  }

  function renderHeatmap() {
    const dateMap = {};
    allSubs.forEach(s => {
      if (!s.date) return;
      const d = s.date.slice(0, 10);
      dateMap[d] = (dateMap[d] || 0) + 1;
    });

    const now = new Date();
    const start = new Date(now);
    start.setFullYear(now.getFullYear() - 1);
    start.setDate(start.getDate() - start.getDay());

    const weeks = [];
    const cur = new Date(start);
    const monthPositions = [];
    let lastMonth = -1;
    let weekIdx = 0;

    while (cur <= now) {
      const week = [];
      for (let d = 0; d < 7; d++) {
        const iso = cur.toISOString().slice(0, 10);
        const count = dateMap[iso] || 0;
        const heatClass = count === 0 ? 'heat-0' : count === 1 ? 'heat-1' : count <= 3 ? 'heat-2' : count <= 6 ? 'heat-3' : 'heat-4';
        week.push({ iso, count, heatClass, inRange: cur <= now });
        if (cur.getMonth() !== lastMonth && d === 0) {
          monthPositions.push({ weekIdx, month: cur.getMonth() });
          lastMonth = cur.getMonth();
        }
        cur.setDate(cur.getDate() + 1);
      }
      weeks.push(week);
      weekIdx++;
    }

    const monthNames = ['Th1', 'Th2', 'Th3', 'Th4', 'Th5', 'Th6', 'Th7', 'Th8', 'Th9', 'Th10', 'Th11', 'Th12'];
    const monthDiv = document.getElementById('heatmapMonths');
    if (monthDiv) {
      monthDiv.innerHTML = '';
      let lastWeekRendered = 0;
      monthPositions.forEach(({ weekIdx: wi, month }) => {
        const gap = wi - lastWeekRendered;
        if (gap > 0) {
          const spacer = document.createElement('span');
          spacer.style.display = 'inline-block';
          spacer.style.width = (gap * 16) + 'px';
          monthDiv.appendChild(spacer);
        }
        const label = document.createElement('span');
        label.textContent = monthNames[month];
        label.style.display = 'inline-block';
        label.style.minWidth = '28px';
        monthDiv.appendChild(label);
        lastWeekRendered = wi + 1;
      });
    }

    const grid = document.getElementById('heatmapGrid');
    if (grid) {
      grid.innerHTML = '';
      weeks.forEach(week => {
        const col = document.createElement('div');
        col.style.display = 'flex';
        col.style.flexDirection = 'column';
        col.style.gap = '3px';
        week.forEach(day => {
          const cell = document.createElement('div');
          cell.className = 'heatmap-cell ' + (day.inRange ? day.heatClass : 'heat-0');
          if (day.count > 0) {
            cell.title = `${day.iso}: ${day.count} bài nộp`;
          }
          col.appendChild(cell);
        });
        grid.appendChild(col);
      });
    }

    const streak = calcStreak(dateMap);
    const hStreak = document.getElementById('heatmapStreak');
    if (hStreak) hStreak.textContent = streak ? `🔥 ${streak} ngày liên tiếp` : '';

    const langFreq = {};
    allSubs.forEach(s => { langFreq[s.language] = (langFreq[s.language] || 0) + 1; });
    const total = allSubs.length || 1;
    const langs = Object.entries(langFreq).sort((a, b) => b[1] - a[1]);
    const lStats = document.getElementById('langStats');
    if (lStats) {
      lStats.innerHTML = langs.map(([lang, cnt]) => {
        const pct = Math.round(cnt / total * 100);
        return `
          <div style="margin-bottom:.75rem;">
            <div style="display:flex;justify-content:space-between;font-size:.82rem;margin-bottom:.3rem;">
              <span style="font-weight:600;">${lang}</span>
              <span style="color:var(--color-text-muted);">${cnt} bài (${pct}%)</span>
            </div>
            <div style="height:8px;background:var(--color-border);border-radius:999px;overflow:hidden;">
              <div style="height:100%;width:${pct}%;background:var(--color-primary);border-radius:999px;transition:width 1s;"></div>
            </div>
          </div>
        `;
      }).join('') || '<div style="color:var(--color-text-muted);">Chưa có dữ liệu.</div>';
    }
  }

  function calcStreak(dateMap) {
    let streak = 0;
    const today = new Date();
    const d = new Date(today);
    while (true) {
      const iso = d.toISOString().slice(0, 10);
      if (!dateMap[iso]) break;
      streak++;
      d.setDate(d.getDate() - 1);
    }
    return streak;
  }

  function renderRatingChart() {
    const canvas = document.getElementById('ratingChart');
    if (!canvas || !canvas.parentElement) return;
    const ctx = canvas.getContext('2d');
    const W = canvas.parentElement.offsetWidth - 40;
    canvas.width = W;
    canvas.height = 150;

    const currentR = Number(profile.rating) || 0;
    const contestsCount = Number(profile.contest_count) || 0;

    const bigEl = document.getElementById('currentRatingBig');
    if (bigEl) bigEl.textContent = currentR;

    if (currentR <= 0 || contestsCount <= 0) {
      ctx.clearRect(0, 0, W, canvas.height);
      const padL = 45, padR = 15, padB = 30;
      const yZero = canvas.height - padB;

      // Draw 0 grid line
      ctx.strokeStyle = 'rgba(148,163,184,.3)';
      ctx.lineWidth = 1;
      ctx.beginPath();
      ctx.moveTo(padL, yZero);
      ctx.lineTo(W - padR, yZero);
      ctx.stroke();

      ctx.fillStyle = '#94a3b8';
      ctx.font = '11px sans-serif';
      ctx.textAlign = 'right';
      ctx.fillText('0', padL - 8, yZero + 4);

      // Draw 0 point
      ctx.beginPath();
      ctx.arc(padL + 25, yZero, 5, 0, Math.PI * 2);
      ctx.fillStyle = '#64748b';
      ctx.fill();
      ctx.strokeStyle = '#fff';
      ctx.lineWidth = 1.5;
      ctx.stroke();

      // Draw unrated text
      ctx.fillStyle = '#64748b';
      ctx.font = '12px sans-serif';
      ctx.textAlign = 'center';
      ctx.fillText('Chưa tham gia kỳ thi có tính rating (Rating: 0 - Unrated)', W / 2, canvas.height / 2);

      const deltaEl = document.getElementById('ratingDelta');
      if (deltaEl) {
        deltaEl.className = 'rating-change same';
        deltaEl.textContent = 'Unrated';
      }
      return;
    }

    const points = [
      Math.max(1200, currentR - 300),
      Math.max(1200, currentR - 150),
      Math.max(1200, currentR - 80),
      currentR
    ].map((v, i) => ({ x: i, y: v }));

    const minY = Math.min(...points.map(p => p.y)) - 50;
    const maxY = Math.max(...points.map(p => p.y)) + 50;
    const padL = 45, padR = 15, padT = 10, padB = 30;

    const toX = (i) => padL + (i / (points.length - 1 || 1)) * (W - padL - padR);
    const toY = (v) => padT + (1 - (v - minY) / (maxY - minY)) * (canvas.height - padT - padB);

    ctx.clearRect(0, 0, W, canvas.height);

    ctx.strokeStyle = 'rgba(148,163,184,.2)';
    ctx.lineWidth = 1;
    [minY + 50, (minY + maxY) / 2, maxY - 50].forEach(v => {
      const y = toY(v);
      ctx.beginPath(); ctx.moveTo(padL, y); ctx.lineTo(W - padR, y); ctx.stroke();
      ctx.fillStyle = '#94a3b8';
      ctx.font = '10px sans-serif';
      ctx.textAlign = 'right';
      ctx.fillText(Math.round(v), padL - 4, y + 3);
    });

    const grad = ctx.createLinearGradient(0, padT, 0, canvas.height - padB);
    grad.addColorStop(0, 'rgba(99,102,241,.5)');
    grad.addColorStop(1, 'rgba(99,102,241,.0)');

    ctx.beginPath();
    ctx.moveTo(toX(0), canvas.height - padB);
    points.forEach((p, i) => ctx.lineTo(toX(i), toY(p.y)));
    ctx.lineTo(toX(points.length - 1), canvas.height - padB);
    ctx.closePath();
    ctx.fillStyle = grad;
    ctx.fill();

    ctx.beginPath();
    ctx.strokeStyle = '#6366f1';
    ctx.lineWidth = 2;
    points.forEach((p, i) => { i === 0 ? ctx.moveTo(toX(i), toY(p.y)) : ctx.lineTo(toX(i), toY(p.y)); });
    ctx.stroke();

    points.forEach((p, i) => {
      const clr = ratingColor(p.y);
      ctx.beginPath();
      ctx.arc(toX(i), toY(p.y), 4, 0, Math.PI * 2);
      ctx.fillStyle = clr;
      ctx.fill();
      ctx.strokeStyle = '#fff';
      ctx.lineWidth = 1.5;
      ctx.stroke();
    });

    if (points.length >= 2) {
      const delta = points[points.length - 1].y - points[points.length - 2].y;
      const deltaEl = document.getElementById('ratingDelta');
      if (deltaEl) {
        deltaEl.className = 'rating-change ' + (delta > 0 ? 'up' : delta < 0 ? 'down' : 'same');
        deltaEl.textContent = (delta > 0 ? '▲ +' : delta < 0 ? '▼ ' : '→ ') + Math.abs(delta);
      }
    }
  }

  loadProfile();
  loadSubs();
})();
