/**
 * CodeProOJ - Admin Dashboard Logic (CodeProOJ Standard Control Center)
 */

(() => {
  const API = (typeof window.API_BASE === 'string') ? window.API_BASE : '';
  let systemState = {};

  async function loadDashboard() {
    try {
      const token = (typeof Auth !== 'undefined' && Auth.getToken) ? Auth.getToken() : localStorage.getItem('token');
      const authHeaders = token ? { 'Authorization': `Token ${token}` } : {};

      // 1. Fetch overview stats
      const [overviewResp, subsResp, clarifResp, systemResp] = await Promise.all([
        fetch(`${API}/api/v2/admin/overview`, { headers: authHeaders }).catch(() => null),
        fetch(`${API}/api/v2/submissions`, { headers: authHeaders }).catch(() => null),
        fetch(`${API}/api/v2/clarifications`, { headers: authHeaders }).catch(() => null),
        fetch(`${API}/api/v2/admin/system`, { headers: authHeaders }).catch(() => null)
      ]);

      if (overviewResp && overviewResp.ok) {
        const oJson = await overviewResp.json();
        const d = oJson?.data || {};

        document.getElementById('statUsers').textContent = d.total_users ?? 0;
        document.getElementById('navUserCount').textContent = d.total_users ?? 0;

        document.getElementById('statProblems').textContent = d.total_problems ?? 0;
        document.getElementById('navProblemCount').textContent = d.total_problems ?? 0;
        document.getElementById('statProbSub').textContent = `${d.published_problems ?? 0} đã xuất bản &bull; ${(d.total_problems ?? 0) - (d.published_problems ?? 0)} nháp`;

        document.getElementById('statContests').textContent = d.active_contests ?? 0;
        document.getElementById('navContestCount').textContent = d.total_contests ?? 0;
        document.getElementById('statContestSub').textContent = `${d.total_contests ?? 0} kỳ thi trên hệ thống`;
        if (document.getElementById('navBlogCount')) {
          document.getElementById('navBlogCount').textContent = d.total_blogs ?? 0;
        }

        document.getElementById('statTodaySubs').textContent = d.today_submissions ?? 0;
        document.getElementById('statAcRate').textContent = `Tỉ lệ AC: ${d.ac_rate ?? 0}%`;
        document.getElementById('statTotalSubs').textContent = d.total_submissions ?? 0;

        document.getElementById('statWorkers').textContent = `${d.workers_count ?? 7} Nodes`;
        document.getElementById('navJudgeBadge').textContent = `${d.workers_count ?? 7} Online`;
        document.getElementById('statQueueSize').textContent = `${d.queue_size ?? 0} bài chờ`;
        document.getElementById('statQueueText').textContent = `Hàng đợi: ${d.queue_size ?? 0} bài chờ`;

        document.getElementById('statClarif').textContent = d.pending_clarifications ?? 0;
      }

      // 2. Fetch System State
      if (systemResp && systemResp.ok) {
        const sysJson = await systemResp.json();
        systemState = sysJson?.data || {};
        updateSystemUI();
      }

      // 3. Fetch submissions
      if (subsResp && subsResp.ok) {
        const sJson = await subsResp.json();
        const sList = sJson?.data?.objects || [];
        renderRecentSubs(sList.slice(0, 10));
      }

      // 4. Fetch Clarifications
      if (clarifResp && clarifResp.ok) {
        const cJson = await clarifResp.json();
        const cList = cJson?.data?.objects || [];
        renderClarifications(cList);
      }

      // 5. Fetch workers list
      fetch('/api/v1/admin/judge/workers', {
        headers: authHeaders
      }).then(r => r.json()).then(wData => {
        const workers = wData.workers || [];
        const listEl = document.getElementById('judgeNodesList');
        if (listEl) {
          listEl.replaceChildren();
          for (const w of workers) {
            const card = document.createElement('div'); card.className = 'node-card';
            const info = document.createElement('div'); info.className = 'node-info';
            const name = document.createElement('h4'); name.textContent = `${w.status === 'ONLINE' || w.status === 'BUSY' ? '🟢' : '🔴'} ${w.name}`;
            const meta = document.createElement('div'); meta.className = 'node-meta';
            meta.textContent = `${(w.supported_languages || []).slice(0, 3).join(', ') || '—'} · ${w.active_jobs || 0} active jobs · ${w.memory_limit || 0} MB`;
            const badge = document.createElement('span'); badge.className = 'badge-v'; badge.textContent = w.status;
            info.append(name, meta); card.append(info, badge); listEl.append(card);
          }
          if (!workers.length) listEl.textContent = 'Chưa có worker đang kết nối.';
        }
      }).catch(() => {});

    } catch (err) {
      console.warn('Dashboard load error:', err);
    }
  }

  function updateSystemUI() {
    const maintBtn = document.getElementById('maintToggleBtn');
    const maintInd = document.getElementById('maintIndicator');
    if (systemState.maintenance_mode) {
      if (maintBtn) {
        maintBtn.textContent = '🟢 Tắt Bảo trì';
        maintBtn.className = 'btn-act';
        maintBtn.style.background = '#065f46';
        maintBtn.style.color = '#34d399';
        maintBtn.style.borderColor = '#059669';
      }
      if (maintInd) {
        maintInd.textContent = 'BẢO TRÌ';
        maintInd.style.background = '#7f1d1d';
        maintInd.style.color = '#fca5a5';
      }
    } else {
      if (maintBtn) {
        maintBtn.textContent = '🛡️ Bật Bảo trì';
        maintBtn.className = 'btn-act btn-act-danger';
        maintBtn.style.background = 'rgba(239,68,68,0.1)';
        maintBtn.style.color = '#f87171';
        maintBtn.style.borderColor = 'rgba(239,68,68,0.3)';
      }
      if (maintInd) {
        maintInd.textContent = 'LIVE';
        maintInd.style.background = '#065f46';
        maintInd.style.color = '#34d399';
      }
    }
  }

  function renderRecentSubs(subs) {
    const tbody = document.getElementById('recentSubsTbody');
    if (!subs.length) {
      tbody.innerHTML = '<tr><td colspan="10" style="text-align:center;padding:2rem;color:#64748b;">Chưa có bài nộp nào.</td></tr>';
      return;
    }

    tbody.innerHTML = subs.map(s => {
      const isAC = s.result === 'AC';
      const vClass = isAC ? 'bv-AC' : (s.result === 'WA' ? 'bv-WA' : 'bv-other');
      const timeMs = s.time != null ? Math.round(parseFloat(s.time) * 1000) + ' ms' : '—';
      const memMB = s.memory != null ? parseFloat(s.memory).toFixed(1) + ' MB' : '—';
      const dateStr = s.date ? new Date(s.date).toLocaleTimeString('vi-VN', {hour:'2-digit', minute:'2-digit', second:'2-digit'}) : '—';

      return `
        <tr>
          <td><a href="/submissions/${s.id}" style="color:#60a5fa;font-family:monospace;font-weight:700;">#${s.id}</a></td>
          <td><a href="/profile/${s.user}" style="color:#fff;font-weight:600;text-decoration:none;">${s.user}</a></td>
          <td><a href="/problems/${s.problem}" style="color:#93c5fd;text-decoration:none;">${s.problem}</a></td>
          <td><span class="badge-v ${vClass}">${s.result || 'Pending'}</span></td>
          <td style="font-weight:700;color:${isAC ? '#34d399' : '#f87171'};">${s.points != null ? s.points : '—'}</td>
          <td style="font-family:monospace;color:#94a3b8;">${timeMs}</td>
          <td style="font-family:monospace;color:#94a3b8;">${memMB}</td>
          <td><span style="font-family:monospace;font-size:.78rem;background:rgba(255,255,255,.05);padding:.15rem .45rem;border-radius:4px;">${s.language}</span></td>
          <td style="color:#64748b;font-size:.78rem;">${dateStr}</td>
          <td style="text-align:center;display:flex;gap:.35rem;justify-content:center;">
            <button onclick="rejudgeSub(${s.id})" class="btn-act" title="Chấm lại">${window.CPIcons ? window.CPIcons.get('refresh', {size:'13px'}) : '🔄'}</button>
            <a href="/submissions/${s.id}" class="btn-act" title="Xem code">${window.CPIcons ? window.CPIcons.get('eye', {size:'13px'}) : '👁️'}</a>
          </td>
        </tr>
      `;
    }).join('');
  }

  function renderClarifications(clars) {
    const listEl = document.getElementById('clarifList');
    const pending = clars.filter(c => !c.answer);
    document.getElementById('clarifCountLabel').textContent = `${pending.length} câu hỏi chưa trả lời`;

    if (!pending.length) {
      listEl.innerHTML = '<div style="text-align:center;padding:1.5rem;color:#64748b;font-size:.85rem;">✓ Tất cả khiếu nại và thắc mắc của thí sinh đã được giải quyết!</div>';
      return;
    }

    listEl.innerHTML = pending.slice(0, 5).map(c => `
      <div style="background:#0b1120;border:1px solid #1e293b;border-radius:8px;padding:.85rem 1rem;">
        <div style="display:flex;justify-content:space-between;margin-bottom:.35rem;">
          <div style="font-weight:700;color:#fff;font-size:.88rem;display:inline-flex;align-items:center;gap:0.35rem;">
            ${window.CPIcons ? window.CPIcons.get('user', {size:'13px'}) : ''} ${c.user} <span style="font-size:.75rem;color:#94a3b8;font-weight:normal;">hỏi về [${c.problem || (c.contest ? 'Kỳ thi ' + c.contest : 'Chung')}]</span>
          </div>
          <span style="font-size:.75rem;color:#f87171;font-weight:700;">Chưa trả lời</span>
        </div>
        <div style="color:#cbd5e1;font-size:.84rem;margin-bottom:.65rem;background:rgba(255,255,255,.02);padding:.4rem .6rem;border-radius:4px;">
          "${c.question}"
        </div>
        <div style="display:flex;gap:.5rem;">
          <input type="text" id="clarifAns_${c.id}" placeholder="Nhập câu trả lời cho thí sinh..." style="flex:1;background:#090d16;border:1px solid #334155;border-radius:6px;color:#fff;padding:.35rem .65rem;font-size:.8rem;outline:none;">
          <button onclick="answerClarification(${c.id})" class="btn-top btn-top-primary" style="padding:.35rem .75rem;font-size:.78rem;">Trả lời</button>
        </div>
      </div>
    `).join('');
  }

  // Universal Rejudge Handlers
  window.handleRejudgeSingle = async function() {
    const id = document.getElementById('rejudgeInput').value.trim();
    if (!id) { alert('Vui lòng nhập ID bài nộp!'); return; }
    await rejudgeSub(id);
  };

  window.rejudgeSub = async function(id) {
    showRejudgeMsg(`⏳ Đang gửi yêu cầu rejudge bài #${id}...`, '#38bdf8');
    try {
      const resp = await fetch(`${API}/api/v2/rejudge/${id}`, { method: 'POST', headers: window.adminApiHeaders() });
      const json = await resp.json();
      if (resp.ok) {
        showRejudgeMsg(`✓ ${json?.data?.message || `Bài #${id} đã được chấm lại thành công!`}`, '#34d399');
        setTimeout(loadDashboard, 1500);
      } else {
        showRejudgeMsg(`Lỗi: ${json?.error?.message || 'Không thể rejudge'}`, '#f87171');
      }
    } catch (err) {
      showRejudgeMsg(`Lỗi kết nối: ${err.message}`, '#f87171');
    }
  };

  window.handleRejudgeProblem = async function() {
    const code = document.getElementById('rejudgeProbInput').value.trim().toUpperCase();
    if (!code) { alert('Vui lòng nhập mã bài tập!'); return; }
    if (!confirm(`Bạn có chắc chắn muốn rejudge TOÀN BỘ bài nộp của bài toán ${code}?`)) return;

    showRejudgeMsg(`⏳ Đang chạy rejudge toàn bộ bài ${code}...`, '#38bdf8');
    try {
      const resp = await fetch(`${API}/api/v2/rejudge/problem/${code}`, { method: 'POST' });
      const json = await resp.json();
      if (resp.ok) {
        showRejudgeMsg(`✓ ${json?.data?.message || `Đã rejudge thành công toàn bộ bài ${code}!`}`, '#34d399');
        setTimeout(loadDashboard, 1500);
      } else {
        showRejudgeMsg(`Lỗi: ${json?.error?.message || 'Không thể rejudge bài tập'}`, '#f87171');
      }
    } catch (err) {
      showRejudgeMsg(`Lỗi kết nối: ${err.message}`, '#f87171');
    }
  };

  window.handleRejudgeContest = async function() {
    const slug = document.getElementById('rejudgeContestInput').value.trim();
    if (!slug) { alert('Vui lòng nhập mã kỳ thi (slug)!'); return; }
    if (!confirm(`Bạn có chắc chắn muốn rejudge TOÀN BỘ bài nộp của kỳ thi ${slug}?`)) return;

    showRejudgeMsg(`⏳ Đang chạy rejudge toàn bộ kỳ thi ${slug}...`, '#38bdf8');
    try {
      const resp = await fetch(`${API}/api/v2/rejudge/contest/${slug}`, { method: 'POST' });
      const json = await resp.json();
      if (resp.ok) {
        showRejudgeMsg(`✓ ${json?.data?.message || `Đã rejudge thành công toàn bộ kỳ thi ${slug}!`}`, '#34d399');
        setTimeout(loadDashboard, 1500);
      } else {
        showRejudgeMsg(`Lỗi: ${json?.error?.message || 'Không thể rejudge kỳ thi'}`, '#f87171');
      }
    } catch (err) {
      showRejudgeMsg(`Lỗi kết nối: ${err.message}`, '#f87171');
    }
  };

  function showRejudgeMsg(txt, color) {
    const el = document.getElementById('rejudgeMsg');
    el.style.display = 'block';
    el.style.color = color;
    el.style.background = 'rgba(0,0,0,0.3)';
    el.textContent = txt;
  }

  // Answer Clarification
  window.answerClarification = async function(id) {
    const inp = document.getElementById(`clarifAns_${id}`);
    const ans = inp ? inp.value.trim() : '';
    if (!ans) { alert('Vui lòng nhập nội dung câu trả lời!'); return; }

    try {
      const resp = await fetch(`${API}/api/v2/clarification/${id}/answer`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ answer: ans, is_public: true })
      });
      if (resp.ok) {
        alert('Đã trả lời khiếu nại thành công!');
        loadDashboard();
      } else {
        alert('Không thể trả lời câu hỏi');
      }
    } catch (err) {
      alert(`Lỗi: ${err.message}`);
    }
  };

  // Maintenance Toggle
  window.toggleMaintenance = async function() {
    const nextState = !systemState.maintenance_mode;
    const actionText = nextState ? 'BẬT chế độ bảo trì toàn hệ thống' : 'TẮT bảo trì và mở lại sàn thi';
    if (!confirm(`Bạn có chắc chắn muốn ${actionText}?`)) return;

    try {
      const resp = await fetch(`${API}/api/v2/admin/system`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ action: 'toggle_maintenance', enabled: nextState })
      });
      const json = await resp.json();
      if (resp.ok) {
        systemState = json?.data?.state || {};
        updateSystemUI();
        alert(json?.data?.message || 'Thành công!');
      }
    } catch (err) {
      alert(`Lỗi: ${err.message}`);
    }
  };

  // Announcement Modal
  window.openAnnounceModal = function() {
    document.getElementById('announceText').value = systemState.global_announcement || '';
    document.getElementById('announceActive').checked = systemState.announcement_active !== false;
    document.getElementById('announceModal').style.display = 'flex';
  };

  window.closeAnnounceModal = function() {
    document.getElementById('announceModal').style.display = 'none';
  };

  window.saveAnnouncement = async function() {
    const text = document.getElementById('announceText').value.trim();
    const active = document.getElementById('announceActive').checked;
    try {
      const resp = await fetch(`${API}/api/v2/admin/system`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ action: 'set_announcement', message: text, active: active })
      });
      if (resp.ok) {
        alert('Đã cập nhật và phát sóng thông báo toàn sàn!');
        closeAnnounceModal();
        loadDashboard();
      }
    } catch (err) {
      alert(`Lỗi: ${err.message}`);
    }
  };

  // Flush Cache
  window.flushSystemCache = async function() {
    if (!confirm('Bạn có chắc muốn dọn dẹp sạch cache và hàng đợi hệ thống?')) return;
    try {
      const resp = await fetch(`${API}/api/v2/admin/system`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ action: 'flush_cache' })
      });
      const json = await resp.json();
      alert(json?.data?.message || 'Đã xóa cache thành công!');
    } catch (err) {
      alert(`Lỗi: ${err.message}`);
    }
  };

  loadDashboard();
  setInterval(loadDashboard, 10000);
})();
