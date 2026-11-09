/**
 * CodeProOJ - My Submissions Logic
 */

const API = (typeof window.API_BASE === 'string')
  ? window.API_BASE
  : (window.location.origin && window.location.origin.startsWith('http') ? '' : 'http://localhost:8000');
const escapeMineHtml = value => String(value ?? '').replace(/[&<>"']/g, char => ({
  '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;'
})[char]);

    const verdictLabel = { 'AC':'✅ AC','WA':'❌ WA','TLE':'⏱ TLE','MLE':'💾 MLE','RTE':'💥 RE','CE':'🔧 CE','G':'⏳','QU':'📥' };
    const verdictClass = { 'AC':'verdict-AC','WA':'verdict-WA','TLE':'verdict-TLE','MLE':'verdict-MLE','RTE':'verdict-RE','CE':'verdict-CE','G':'verdict-G','QU':'verdict-G' };

    function formatTime(t) { return t != null ? Math.round(parseFloat(t)*1000)+' ms' : '—'; }
    function formatMem(m) { return m != null ? parseFloat(m).toFixed(1)+' MB' : '—'; }
    function formatDate(d) { if (!d) return '—'; return new Date(d).toLocaleString('vi'); }

    function computeStats(subs) {
      document.getElementById('sTotalSubs').textContent = subs.length;
      const acProbs = new Set(subs.filter(s=>s.result==='AC').map(s=>s.problem));
      document.getElementById('sAcProbs').textContent = acProbs.size;
      const ac = subs.filter(s=>s.result==='AC').length;
      document.getElementById('sAcRate').textContent = subs.length ? Math.round(ac/subs.length*100)+'%' : '0%';
      // Most used language
      const langFreq = Object.create(null);
      subs.forEach(s => langFreq[s.language] = (langFreq[s.language]||0)+1);
      const bestLang = Object.entries(langFreq).sort((a,b)=>b[1]-a[1])[0];
      document.getElementById('sBestLang').textContent = bestLang ? bestLang[0] : '—';
    }

    async function loadMine() {
      const user = localStorage.getItem('username');
      if (!user) {
        document.getElementById('mainContent').style.display = 'none';
        document.getElementById('notLoggedState').style.display = 'block';
        return;
      }
      document.getElementById('currentUserLabel').textContent = user;

      const filterProb = document.getElementById('filterProblem').value.trim();
      const filterVerdict = document.getElementById('filterVerdict').value;

      let url = `${API}/api/v2/submissions?user=${encodeURIComponent(user)}`;
      if (filterProb) url += `&problem=${encodeURIComponent(filterProb)}`;

      try {
        const resp = await fetch(url);
        const json = await resp.json();
        let subs = json?.data?.objects || [];
        computeStats(subs);

        if (filterVerdict) subs = subs.filter(s => (s.result||'').startsWith(filterVerdict));

        const tbody = document.getElementById('mineBody');
        if (!subs.length) {
          tbody.innerHTML = `<tr><td colspan="8" class="empty-state">Chưa có bài nộp nào.</td></tr>`;
          return;
        }

        tbody.innerHTML = subs.map(s => {
          const v = s.result || s.status || 'QU';
          const cls = verdictClass[v] || 'verdict-WA';
          const lbl = verdictLabel[v] || v;
          return `<tr>
            <td><a href="/frontend/html/submission/submission.html?id=${Number.isSafeInteger(Number(s.id)) ? Number(s.id) : 0}" class="sub-link">#${escapeMineHtml(s.id)}</a></td>
            <td><a href="/frontend/html/problem/problem.html?code=${encodeURIComponent(s.problem)}" class="prob-link">${escapeMineHtml(s.problem)}</a></td>
            <td><span class="verdict-badge ${cls}">${escapeMineHtml(lbl)}</span></td>
            <td style="font-weight:700;color:var(--color-primary);">${escapeMineHtml(s.points != null ? s.points : '—')}</td>
            <td style="font-family:monospace;font-size:.8rem;">${formatTime(s.time)}</td>
            <td style="font-family:monospace;font-size:.8rem;">${formatMem(s.memory)}</td>
            <td><span class="lang-badge">${escapeMineHtml(s.language||'—')}</span></td>
            <td style="font-size:.8rem;color:var(--color-text-muted);">${formatDate(s.date)}</td>
          </tr>`;
        }).join('');

      } catch(e) {
        document.getElementById('mineBody').innerHTML =
          `<tr><td colspan="8" class="empty-state" style="color:#ef4444;">⚠ Lỗi kết nối: ${escapeMineHtml(e.message)}</td></tr>`;
      }
    }

    ['filterVerdict','filterLang'].forEach(id => document.getElementById(id).addEventListener('change', loadMine));
    document.getElementById('filterProblem').addEventListener('keydown', e => { if (e.key === 'Enter') loadMine(); });

    loadMine();

// Window exports for inline event handlers
window.loadMine = loadMine;
