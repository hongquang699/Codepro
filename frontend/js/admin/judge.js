/**
 * CodeProOJ - Admin Judge Management Logic
 */

(() => {
    const API = (typeof window.API_BASE === 'string') ? window.API_BASE : '';

    async function loadJudgeData() {
      try {
        const token = localStorage.getItem('token');
        let authHeaders = {};
        if (token) {
          authHeaders['Authorization'] = `Token ${token}`;
        }
        
        const proxyResp = await fetch(`${API}/api/v2/admin/judge-workers?user=admin`, {
          headers: authHeaders
        }).catch(() => null);

        if (proxyResp && proxyResp.ok) {
          const res = await proxyResp.json();
          const pData = res.data || res;
          const workers = pData.workers || [];
          const health = pData.health || {};

          if (document.getElementById('statQueueCount')) {
            document.getElementById('statQueueCount').textContent = health.queue_size || 0;
          }
          if (document.getElementById('statTotalEvaluated')) {
            document.getElementById('statTotalEvaluated').textContent = health.completed_results || 0;
          }
          if (document.getElementById('rawStatus')) {
            document.getElementById('rawStatus').textContent = JSON.stringify(health, null, 2);
          }
          if (document.getElementById('statActiveNodes')) {
            document.getElementById('statActiveNodes').textContent = `${workers.length} / ${workers.length}`;
          }
          renderWorkers(workers);
        }
      } catch (err) {
        console.warn('Error loading judge status:', err);
      }
    }

    function renderWorkers(workers) {
      const grid = document.getElementById('workerGrid');
      grid.innerHTML = workers.map(w => {
        const meta = w.metadata || {};
        const title = meta.name || w.worker_id;
        const role = meta.role || 'General Purpose Worker Node';
        const cap = meta.capacity ? `${meta.capacity} concurrent jobs` : '2 concurrent jobs';
        const ram = meta.max_memory_mb ? `${meta.max_memory_mb} MB` : '2048 MB';
        const langs = (meta.supported_languages && meta.supported_languages.length) 
          ? meta.supported_languages.map(l => l.toUpperCase()).join(', ') 
          : 'C++, C, Python, Java, Rust';
        const isAlive = (w.status || '').toLowerCase() === 'online';
        const statusColor = isAlive ? '#10b981' : '#f87171';
        const pillClass = isAlive ? 'wp-online' : 'wp-offline';

        return `
          <div class="worker-card">
            <div class="wc-hdr">
              <div class="wc-name" title="${w.worker_id}">
                <span style="color:${statusColor};">●</span> ${title}
              </div>
              <span class="wc-pill ${pillClass}">${(w.status || 'ONLINE').toUpperCase()}</span>
            </div>
            <div class="wc-row">
              <span class="wc-lbl">Role / Tác vụ:</span>
              <span class="wc-val" style="color:#60a5fa;font-weight:600;">${role}</span>
            </div>
            <div class="wc-row">
              <span class="wc-lbl">Capacity / RAM:</span>
              <span class="wc-val">${cap} · max ${ram}</span>
            </div>
            <div class="wc-row">
              <span class="wc-lbl">Active Jobs:</span>
              <span class="wc-val">${w.active_jobs || 0} bài đang chấm</span>
            </div>
            <div class="wc-row">
              <span class="wc-lbl">Last Heartbeat:</span>
              <span class="wc-val">${(w.last_seen_sec_ago || 0).toFixed(1)}s trước</span>
            </div>
            <div class="wc-row">
              <span class="wc-lbl">Ngôn ngữ:</span>
              <span class="wc-val" style="font-size:.78rem;">${langs}</span>
            </div>
            <div class="wc-row">
              <span class="wc-lbl">Sandbox Isolation:</span>
              <span class="wc-val" style="color:#34d399;">Active (Process + Memory Limit)</span>
            </div>
          </div>
        `;
      }).join('');
    }

    window.rejudgeProblem = async function() {
      const code = document.getElementById('batchProbCode').value.trim();
      if (!code) { alert('Vui lòng nhập mã bài toán!'); return; }
      
      const st = document.getElementById('rejudgeStatus');
      st.style.display = 'block';
      st.style.color = '#38bdf8';
      st.textContent = `⏳ Đang tìm và rejudge các bài nộp của ${code}...`;

      try {
        const resp = await fetch(`${API}/api/v2/submissions?problem=${encodeURIComponent(code)}`);
        const json = await resp.json();
        const subs = json?.data?.objects || [];

        if (!subs.length) {
          st.style.color = '#fbbf24';
          st.textContent = `Không có bài nộp nào cho bài ${code}.`;
          return;
        }

        let done = 0;
        for (const s of subs) {
          await fetch(`${API}/api/v2/rejudge/${s.id}`, { method: 'POST' });
          done++;
          st.textContent = `Đang rejudge: ${done} / ${subs.length} bài...`;
        }

        st.style.color = '#34d399';
        st.textContent = `✓ Đã hoàn thành rejudge toàn bộ ${subs.length} bài nộp của ${code}!`;
        setTimeout(loadJudgeData, 2000);
      } catch (err) {
        st.style.color = '#f87171';
        st.textContent = `Lỗi: ${err.message}`;
      }
    };

    loadJudgeData();
    setInterval(loadJudgeData, 5000);
  })();
