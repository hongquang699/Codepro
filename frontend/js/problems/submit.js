/**
 * CodeProOJ - Problem Submit Logic
 * Handles problem selection, starter templates, Tab indentation,
 * and sending code directly to the Judge Server via /api/v2/submit.
 */

(() => {
  const API = (typeof window.API_BASE === 'string')
    ? window.API_BASE
    : (window.location.origin && window.location.origin.startsWith('http') ? '' : 'http://localhost:8000');
  const urlParams = new URLSearchParams(window.location.search);
  const preCode = urlParams.get('code') || '';
  function getCurrentUser() {
    try {
      const u = JSON.parse(localStorage.getItem('user'));
      if (u && u.username) return u.username;
    } catch (e) {}
    return localStorage.getItem('username') || '';
  }

  const templates = {
    CPP17: `#include <bits/stdc++.h>\nusing namespace std;\n\nint main() {\n    ios_base::sync_with_stdio(false);\n    cin.tie(NULL);\n    \n    // Viết lời giải ở đây\n    \n    return 0;\n}`,
    CPP14: `#include <iostream>\nusing namespace std;\n\nint main() {\n    return 0;\n}`,
    PY3: `import sys\n\ndef main():\n    input = sys.stdin.readline\n    # Viết lời giải ở đây\n    pass\n\nif __name__ == '__main__':\n    main()`,
    JAVA: `import java.util.*;\nimport java.io.*;\n\npublic class Main {\n    public static void main(String[] args) throws IOException {\n        // Viết lời giải ở đây\n    }\n}`,
    RUST: `use std::io::{self, BufRead};\n\nfn main() {\n    let stdin = io::stdin();\n}`,
    GO: `package main\n\nimport "fmt"\n\nfunc main() {\n}`,
    PAS: `program Solution;\nbegin\nend.`
  };

  const problemSelect = document.getElementById('problemSelect');
  const langSelect = document.getElementById('langSelect');
  const sourceCode = document.getElementById('sourceCode');
  const charCount = document.getElementById('charCount');

  if (sourceCode) {
    sourceCode.value = templates.CPP17;
    if (charCount) charCount.textContent = `${sourceCode.value.length} ký tự`;

    sourceCode.addEventListener('input', () => {
      if (charCount) charCount.textContent = `${sourceCode.value.length} ký tự`;
    });

    // Tab key support
    sourceCode.addEventListener('keydown', e => {
      if (e.key === 'Tab') {
        e.preventDefault();
        const start = sourceCode.selectionStart;
        const end = sourceCode.selectionEnd;
        sourceCode.value = sourceCode.value.substring(0, start) + '    ' + sourceCode.value.substring(end);
        sourceCode.selectionStart = sourceCode.selectionEnd = start + 4;
        if (charCount) charCount.textContent = `${sourceCode.value.length} ký tự`;
      }
    });
  }

  if (langSelect) {
    langSelect.addEventListener('change', () => {
      const l = langSelect.value;
      if (!sourceCode.value.trim() || confirm('Đổi template sang ngôn ngữ ' + l + '?')) {
        sourceCode.value = templates[l] || '';
        if (charCount) charCount.textContent = `${sourceCode.value.length} ký tự`;
      }
    });
  }

  async function loadProblems() {
    if (!problemSelect) return;
    try {
      const resp = await fetch(`${API}/api/v2/problems`);
      const json = await resp.json();
      const probs = json?.data?.objects || [];
      
      problemSelect.innerHTML = probs.map(p => `
        <option value="${p.code}" ${p.code === preCode ? 'selected' : ''}>
          ${p.code} - ${p.name}
        </option>
      `).join('');
    } catch (err) {
      problemSelect.innerHTML = '<option value="">Lỗi tải danh sách bài</option>';
    }
  }

  window.doSubmit = async function() {
    const problem = problemSelect ? problemSelect.value : '';
    const lang = langSelect ? langSelect.value : 'CPP17';
    const source = sourceCode ? sourceCode.value.trim() : '';

    if (!problem) { alert('Vui lòng chọn bài tập!'); return; }
    if (!source) { alert('Vui lòng nhập mã nguồn!'); return; }

    const user = getCurrentUser();
    if (!user) {
      alert('Vui lòng đăng nhập để nộp bài!');
      window.location.href = `/frontend/html/auth/login.html?next=${encodeURIComponent(window.location.pathname + window.location.search)}`;
      return;
    }

    const btn = document.getElementById('btnSubmit');
    const box = document.getElementById('resultAlert');

    if (btn) {
      btn.disabled = true;
      btn.innerHTML = '⏳ Đang chấm bài...';
    }
    if (box) {
      box.className = 'result-alert show ra-other';
      document.getElementById('resTitle').textContent = '⏳ Đang gửi bài đến Judge Server...';
      document.getElementById('resDetails').textContent = 'Hệ thống đang biên dịch và thực thi test cases...';
      document.getElementById('resLink').style.display = 'none';
    }

    try {
      const csrfMatch = document.cookie.match(/(?:^|;\s*)(?:csrftoken|csrf_token)=([^;]+)/);
      const csrf = csrfMatch ? decodeURIComponent(csrfMatch[1]) : '';
      const token = localStorage.getItem('token');

      const resp = await fetch(`${API}/api/v2/submit`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          ...(csrf ? { 'X-CSRFToken': csrf } : {}),
          ...(token ? { 'Authorization': `Bearer ${token}` } : {})
        },
        body: JSON.stringify({
          problem: problem,
          language: lang,
          source: source,
          user: user
        })
      });

      const json = await resp.json();
      if (!resp.ok) throw new Error(json?.error?.message || 'Lỗi khi nộp bài');

      const d = json.data;
      const res = d.result || 'WA';
      const subId = d.submission_id;

      const isAC = res === 'AC';
      if (box) {
        box.className = `result-alert show ${isAC ? 'ra-AC' : (res === 'WA' ? 'ra-WA' : 'ra-other')}`;
        document.getElementById('resTitle').textContent = isAC ? '🎉 ACCEPTED (Chính xác)' : `Phán quyết: ${res}`;
        document.getElementById('resDetails').textContent = `Điểm: ${d.points} | Thời gian: ${Math.round((d.time||0)*1000)} ms | Bộ nhớ: ${(d.memory||0).toFixed(1)} MB`;

        if (subId) {
          const lk = document.getElementById('resLink');
          lk.href = `/frontend/html/submission/submission.html?id=${subId}`;
          lk.style.display = 'inline-block';
        }
      }

    } catch (err) {
      if (box) {
        box.className = 'result-alert show ra-WA';
        document.getElementById('resTitle').textContent = '⚠ Lỗi nộp bài';
        document.getElementById('resDetails').textContent = err.message;
      }
    } finally {
      if (btn) {
        btn.disabled = false;
        btn.innerHTML = '🚀 Nộp bài ngay (Submit)';
      }
    }
  };

  loadProblems();
})();
