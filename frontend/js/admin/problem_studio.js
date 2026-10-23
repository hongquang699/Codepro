/**
 * CodeProOJ - Problem Setter Studio Logic
 */

let activeCode = '';
    let currentProblem = null;
    const escapeCell = value => String(value ?? '').replace(/[&<>"']/g, ch => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[ch]));

    // Tab Switching
    function switchTab(tabId) {
      document.querySelectorAll('.studio-tab-btn').forEach(b => b.classList.remove('active'));
      document.querySelectorAll('.studio-section').forEach(s => s.classList.remove('active'));

      const btn = document.getElementById(`tab-${tabId}`);
      const sec = document.getElementById(`section-${tabId}`);
      if (btn) btn.classList.add('active');
      if (sec) sec.classList.add('active');

      if (tabId === 'statement') renderStatementPreview();
      if (tabId === 'testcases') loadTestcases();
      if (tabId === 'judge') loadJudgeConfigs();
      if (tabId === 'solution') loadSolutions();
      if (tabId === 'publish') loadPublishTab();
    }

    // Initialize Page
    async function initStudio() {
      const urlParams = new URLSearchParams(window.location.search);
      activeCode = urlParams.get('code') || urlParams.get('id') || '';

      if (activeCode) {
        await loadExistingProblem(activeCode);
      } else {
        // New Problem default starter
        document.getElementById('probCode').value = '';
        document.getElementById('probTitle').value = '';
        setTemplateMarkdown('NEW_PROBLEM', 'Tên bài tập');
      }
    }

    async function loadExistingProblem(code) {
      try {
        const res = await fetch(`/api/v1/problems/${encodeURIComponent(code)}`).then(r => r.json());
        if (res.status === 200 && res.data) {
          currentProblem = res.data;
          activeCode = currentProblem.code;

          // Banner
          document.getElementById('bannerTitle').innerText = `${currentProblem.code} - ${currentProblem.title}`;
          const isPub = currentProblem.is_public === true;
          const badgeEl = document.getElementById('bannerStatus');
          badgeEl.className = isPub ? 'badge badge-ac' : 'badge badge-pending';
          badgeEl.innerText = isPub ? 'CÔNG KHAI' : (currentProblem.status === 'draft' ? 'BẢN NHÁP' : 'ẨN TẠM THỜI');
          document.getElementById('bannerSub').innerText = `Gói bài tập problem-data/problems/${currentProblem.code}/`;

          const quickPub = document.getElementById('quickPublishBtn');
          quickPub.style.display = isPub ? 'none' : 'block';
          const prevBtn = document.getElementById('previewStudentBtn');
          prevBtn.style.display = 'block';
          prevBtn.href = `/frontend/html/problems/problem.html?code=${currentProblem.code}`;

          // Form fields
          document.getElementById('probCode').value = currentProblem.code;
          document.getElementById('probCode').disabled = true; // Code immutable once package created
          document.getElementById('probTitle').value = currentProblem.title;
          document.getElementById('probTime').value = currentProblem.time_limit;
          document.getElementById('probMemory').value = currentProblem.memory_limit;
          document.getElementById('probDifficulty').value = currentProblem.difficulty || 'medium';
          document.getElementById('probPoints').value = currentProblem.points || 100;
          document.getElementById('probTags').value = (currentProblem.tags || []).join(', ');
          document.getElementById('saveBasicBtn').innerText = '💾 Cập nhật Thông tin Cơ bản';

          // Statement
          if (currentProblem.statement && currentProblem.statement.markdown) {
            document.getElementById('statementMarkdown').value = currentProblem.statement.markdown;
          } else {
            setTemplateMarkdown(currentProblem.code, currentProblem.title);
          }
          renderStatementPreview();

        } else {
          alert('Không tìm thấy bài tập: ' + code);
        }
      } catch (e) {
        console.error('Error loading problem:', e);
      }
    }

    function setTemplateMarkdown(code, title) {
      document.getElementById('statementMarkdown').value = `# ${title || code}

## Đề bài
Cho hai số nguyên $A$ và $B$. Hãy tính và in ra tổng $A + B$.

## Dữ liệu vào
Gồm một dòng duy nhất chứa hai số nguyên $A$ và $B$ ($1 \\le A, B \\le 10^9$).

## Dữ liệu ra
In ra một số nguyên duy nhất là kết quả $A + B$.

## Ví dụ
### Input
\`\`\`
2 3
\`\`\`
### Output
\`\`\`
5
\`\`\`

## Giới hạn
- Thời gian chạy: 1.0s
- Bộ nhớ tối đa: 256MB
`;
    }

    function renderStatementPreview() {
      const md = document.getElementById('statementMarkdown').value;
      const preview = document.getElementById('statementPreview');
      if (preview) {
        // Simple client-side Markdown styling converter
        let html = md
          .replace(/^# (.*$)/gim, '<h1 style="color: #60a5fa; margin-bottom: 0.5rem;">$1</h1>')
          .replace(/^## (.*$)/gim, '<h3 style="color: #93c5fd; margin-top: 1.25rem; margin-bottom: 0.4rem;">$1</h3>')
          .replace(/^### (.*$)/gim, '<h4 style="color: #cbd5e1; margin-top: 0.75rem; margin-bottom: 0.2rem;">$1</h4>')
          .replace(/```([^`]+)```/gim, '<pre style="background: #1e293b; padding: 0.75rem; border-radius: 6px; overflow-x: auto; color: #f8fafc; font-family: monospace;">$1</pre>')
          .replace(/\$([^\$]+)\$/gim, '<code style="background: rgba(255,255,255,0.1); padding: 1px 4px; border-radius: 4px; color: #f472b6;">$1</code>')
          .replace(/\n/gim, '<br>');
        preview.innerHTML = html;
      }
    }

    document.getElementById('statementMarkdown').addEventListener('input', renderStatementPreview);

    // SAVE BASIC INFO
    document.getElementById('basicForm').addEventListener('submit', async function(e) {
      e.preventDefault();
      const code = document.getElementById('probCode').value.trim().toUpperCase();
      const title = document.getElementById('probTitle').value.trim();
      const time_limit = parseFloat(document.getElementById('probTime').value);
      const memory_limit = parseInt(document.getElementById('probMemory').value);
      const difficulty = document.getElementById('probDifficulty').value;
      const points = parseFloat(document.getElementById('probPoints').value);
      const tags = document.getElementById('probTags').value.split(',').map(t => t.trim()).filter(Boolean);

      const btn = document.getElementById('saveBasicBtn');
      btn.disabled = true;
      btn.innerText = 'Đang lưu...';

      try {
        if (!activeCode) {
          // POST create
          const res = await fetch('/api/v1/problems', {
            method: 'POST',
            headers: window.adminApiHeaders('application/json'),
            body: JSON.stringify({ code, title, time_limit, memory_limit, difficulty, points, tags })
          }).then(r => r.json());

          if (res.status === 201) {
            alert(`Tạo bài tập ${code} và cấu trúc Package thành công!`);
            window.location.href = `/admin/problems/create?code=${code}`;
          } else {
            alert((res.error && res.error.message) || 'Lỗi khi tạo bài tập');
            btn.disabled = false;
            btn.innerText = '💾 Lưu thông tin & Khởi tạo Package';
          }
        } else {
          // PATCH update
          const res = await fetch(`/api/v1/problems/${encodeURIComponent(activeCode)}`, {
            method: 'PATCH',
            headers: window.adminApiHeaders('application/json'),
            body: JSON.stringify({ title, time_limit, memory_limit, difficulty, points })
          }).then(r => r.json());

          if (res.status === 200) {
            alert('Cập nhật thông tin thành công!');
            btn.disabled = false;
            btn.innerText = '💾 Cập nhật Thông tin Cơ bản';
            loadExistingProblem(activeCode);
          } else {
            alert((res.error && res.error.message) || 'Lỗi cập nhật');
            btn.disabled = false;
          }
        }
      } catch (err) {
        alert('Lỗi: ' + err.message);
        btn.disabled = false;
      }
    });

    // SAVE STATEMENT
    async function saveStatement() {
      if (!activeCode) return alert('Vui lòng khởi tạo thông tin cơ bản trước!');
      const markdown = document.getElementById('statementMarkdown').value;
      const html = document.getElementById('statementPreview').innerHTML;

      try {
        const res = await fetch(`/api/v1/problems/${encodeURIComponent(activeCode)}/statement`, {
          method: 'PUT',
          headers: window.adminApiHeaders('application/json'),
          body: JSON.stringify({ markdown, html })
        }).then(r => r.json());

        if (res.status === 200) {
          alert('Đã lưu đề bài vào statement/statement.md thành công!');
        } else {
          alert('Lỗi: ' + (res.error?.message || 'Không thể lưu'));
        }
      } catch (e) {
        alert('Lỗi kết nối: ' + e.message);
      }
    }

    // TESTCASES TAB
    async function loadTestcases() {
      if (!activeCode) return;
      const tbody = document.getElementById('testcasesTableBody');
      try {
        const res = await fetch(`/api/v1/problems/${encodeURIComponent(activeCode)}/testcases`).then(r => r.json());
        if (res.status === 200 && res.data) {
          const tests = res.data.testcases || [];
          document.getElementById('testcasesTotalBadge').innerText = `${tests.length} tests`;
          if (tests.length === 0) {
            tbody.innerHTML = `<tr><td colspan="6" style="text-align: center; color: var(--color-text-muted); padding: 2rem;">Chưa có testcase nào.</td></tr>`;
            return;
          }

          tbody.innerHTML = tests.map(t => `
            <tr>
              <td style="font-family: monospace; font-weight: 700;">${escapeCell(t.id)}</td>
              <td><pre style="margin: 0; font-size: 0.8rem; max-height: 50px; overflow: hidden; background: #0f172a; padding: 4px 8px; border-radius: 4px;">${escapeCell(t.in_preview || '(rỗng)')}</pre></td>
              <td><pre style="margin: 0; font-size: 0.8rem; max-height: 50px; overflow: hidden; background: #0f172a; padding: 4px 8px; border-radius: 4px;">${escapeCell(t.out_preview || '(rỗng)')}</pre></td>
              <td style="font-size: 0.8rem; color: var(--color-text-muted);">${t.in_size}B / ${t.out_size}B</td>
              <td style="font-size: 0.8rem;">${escapeCell(t.points)} điểm · ST ${escapeCell(t.subtask)}${t.sample ? ' · Sample' : ''}</td>
              <td style="text-align: right;">
                <button onclick="deleteSingleTest('${escapeCell(t.id)}')" class="btn btn-secondary" style="padding: 0.2rem 0.5rem; font-size: 0.75rem; color: #ef4444; border-color: #ef4444;">✕</button>
              </td>
            </tr>
          `).join('');
        }
      } catch (e) {
        tbody.innerHTML = `<tr><td colspan="5" style="color: #ef4444;">Lỗi tải testcases: ${e.message}</td></tr>`;
      }
    }

    async function addManualTestcase() {
      if (!activeCode) return alert('Vui lòng khởi tạo thông tin cơ bản trước!');
      const id = document.getElementById('manualTestId').value.trim() || undefined;
      const input = document.getElementById('manualTestIn').value;
      const output = document.getElementById('manualTestOut').value;
      const points = Number(document.getElementById('manualTestPoints').value || 10);
      const subtask = Number(document.getElementById('manualTestSubtask').value || 1);
      const sample = document.getElementById('manualTestSample').checked;

      try {
        const res = await fetch(`/api/v1/problems/${encodeURIComponent(activeCode)}/testcases`, {
          method: 'POST',
          headers: window.adminApiHeaders('application/json'),
          body: JSON.stringify({ id, input, output, points, subtask, sample })
        }).then(r => r.json());

        if (res.status === 201) {
          alert('Đã lưu testcase thành công!');
          document.getElementById('manualTestId').value = '';
          document.getElementById('manualTestIn').value = '';
          document.getElementById('manualTestOut').value = '';
          loadTestcases();
        } else {
          alert('Lỗi: ' + (res.error?.message || 'Không thể lưu test'));
        }
      } catch (e) {
        alert('Lỗi: ' + e.message);
      }
    }

    async function deleteSingleTest(tid) {
      if (!confirm(`Xóa testcase ${tid}?`)) return;
      try {
        await fetch(`/api/v1/problems/${encodeURIComponent(activeCode)}/testcases/${tid}`, { method: 'DELETE', headers: window.adminApiHeaders() });
        loadTestcases();
      } catch (e) {
        alert('Lỗi: ' + e.message);
      }
    }

    async function uploadZipTestcases() {
      if (!activeCode) return alert('Vui lòng khởi tạo thông tin cơ bản trước!');
      const input = document.getElementById('zipUploadInput');
      if (!input.files || !input.files[0]) return alert('Vui lòng chọn file .zip!');

      const formData = new FormData();
      formData.append('file', input.files[0]);

      try {
        const res = await fetch(`/api/v1/problems/${encodeURIComponent(activeCode)}/testcases/upload`, {
          method: 'POST',
          headers: window.adminApiHeaders(),
          body: formData
        }).then(r => r.json());

        if (res.status === 200) {
          alert(res.data.message);
          input.value = '';
          loadTestcases();
        } else {
          alert('Lỗi upload: ' + (res.error?.message || 'Thất bại'));
        }
      } catch (e) {
        alert('Lỗi: ' + e.message);
      }
    }

    // CHECKER & VALIDATOR TAB
    async function loadJudgeConfigs() {
      if (!activeCode) return;
      try {
        const [chkRes, valRes] = await Promise.all([
          fetch(`/api/v1/problems/${encodeURIComponent(activeCode)}/checker`).then(r => r.json()),
          fetch(`/api/v1/problems/${encodeURIComponent(activeCode)}/validator`).then(r => r.json())
        ]);

        if (chkRes.data) {
          document.getElementById('checkerCode').value = chkRes.data.code || '// Standard White-space Agnostic Checker';
        }
        if (valRes.data) {
          document.getElementById('validatorCode').value = valRes.data.code || '// Standard Non-empty Validator';
        }
      } catch (e) {
        console.error('Error loading judge configs:', e);
      }
    }

    async function saveChecker() {
      if (!activeCode) return alert('Vui lòng khởi tạo bài tập trước!');
      const code = document.getElementById('checkerCode').value;
      await fetch(`/api/v1/problems/${encodeURIComponent(activeCode)}/checker`, {
        method: 'POST',
        headers: window.adminApiHeaders('application/json'),
        body: JSON.stringify({ code, filename: 'checker.cpp' })
      });
      alert('Đã lưu checker thành công!');
    }

    async function saveValidator() {
      if (!activeCode) return alert('Vui lòng khởi tạo bài tập trước!');
      const code = document.getElementById('validatorCode').value;
      await fetch(`/api/v1/problems/${encodeURIComponent(activeCode)}/validator`, {
        method: 'POST',
        headers: window.adminApiHeaders('application/json'),
        body: JSON.stringify({ code, filename: 'validator.cpp' })
      });
      alert('Đã lưu validator thành công!');
    }

    function onCheckerTypeChange() {
      const type = document.getElementById('checkerType').value;
      if (type === 'standard') {
        document.getElementById('checkerCode').value = `// Standard CodeProOJ/DMOJ White-space Agnostic Token Checker\n// Tokens are compared ignoring whitespace and newlines.`;
      } else if (type === 'float') {
        document.getElementById('checkerCode').value = `// Floating Point Checker with absolute or relative error <= 1e-6\n#include "testlib.h"\n\nint main(int argc, char* argv[]) {\n    registerTestlibCmd(argc, argv);\n    double jans = ans.readDouble();\n    double pans = ouf.readDouble();\n    if (!doubleCompare(jans, pans, 1e-6)) quitf(_wa, "Difference exceeds 1e-6");\n    quitf(_ok, "Correct answer");\n}`;
      }
    }

    // SOLUTION TAB
    async function loadSolutions() {
      if (!activeCode) return;
      try {
        const res = await fetch(`/api/v1/problems/${encodeURIComponent(activeCode)}/solutions`).then(r => r.json());
        if (res.status === 200 && res.data && res.data.solutions && res.data.solutions.length > 0) {
          const first = res.data.solutions[0];
          document.getElementById('solutionFilename').value = first.filename;
          document.getElementById('solutionCode').value = first.code;
        } else {
          // Default starter
          document.getElementById('solutionCode').value = `# Solution chuẩn cho bài toán ${activeCode}
import sys

def main():
    data = sys.stdin.read().split()
    if not data:
        return
    a, b = int(data[0]), int(data[1])
    print(a + b)

if __name__ == '__main__':
    main()
`;
        }
      } catch (e) {
        console.error('Error loading solution:', e);
      }
    }

    function onSolutionFileChange() {
      const f = document.getElementById('solutionFilename').value;
      if (f.endsWith('.cpp')) {
        document.getElementById('solutionCode').value = `#include <iostream>
using namespace std;

int main() {
    ios_base::sync_with_stdio(false);
    cin.tie(NULL);
    
    long long a, b;
    if (cin >> a >> b) {
        cout << a + b << "\\n";
    }
    return 0;
}
`;
      } else {
        document.getElementById('solutionCode').value = `import sys

def main():
    data = sys.stdin.read().split()
    if not data:
        return
    a, b = int(data[0]), int(data[1])
    print(a + b)

if __name__ == '__main__':
    main()
`;
      }
    }

    async function saveSolution() {
      if (!activeCode) return alert('Vui lòng khởi tạo bài tập trước!');
      const filename = document.getElementById('solutionFilename').value;
      const code = document.getElementById('solutionCode').value;

      try {
        const res = await fetch(`/api/v1/problems/${encodeURIComponent(activeCode)}/solutions`, {
          method: 'POST',
          headers: window.adminApiHeaders('application/json'),
          body: JSON.stringify({ filename, code })
        }).then(r => r.json());

        if (res.status === 200) {
          alert(`Đã lưu solution ${filename} vào thư mục solutions/ thành công!`);
        } else {
          alert('Lỗi lưu: ' + res.error?.message);
        }
      } catch (e) {
        alert('Lỗi: ' + e.message);
      }
    }

    async function runSolutionVerification() {
      if (!activeCode) return alert('Vui lòng khởi tạo bài tập trước!');
      await saveSolution();

      const btn = document.getElementById('runSolBtn');
      btn.disabled = true;
      btn.innerText = '⏳ Đang chấm thử toàn bộ testcases...';

      const resultsCard = document.getElementById('solutionResultsCard');
      const tbody = document.getElementById('solutionResultsBody');
      const overallBadge = document.getElementById('solutionOverallBadge');

      resultsCard.style.display = 'block';
      tbody.innerHTML = `<tr><td colspan="4" style="text-align: center; padding: 1.5rem; color: #60a5fa;">Đang gửi solution tới Judge Manager...</td></tr>`;

      try {
        const filename = document.getElementById('solutionFilename').value;
        let res = await fetch(`/api/v1/problems/${encodeURIComponent(activeCode)}/solutions/test`, {
          method: 'POST',
          headers: window.adminApiHeaders('application/json'),
          body: JSON.stringify({ filename })
        }).then(async response => ({ status: response.status, ...(await response.json()) }));

        if (res.status === 202 && res.data?.job_id) {
          const jobId = res.data.job_id;
          let result = null;
          for (let attempt = 0; attempt < 90; attempt++) {
            await new Promise(resolve => setTimeout(resolve, 1000));
            const poll = await fetch(`/api/v1/problems/${encodeURIComponent(activeCode)}/solutions/test?job_id=${encodeURIComponent(jobId)}`, {
              headers: window.adminApiHeaders('application/json')
            }).then(response => response.json());
            const submission = poll.data?.result;
            if (submission && ['Completed', 'Failed', 'Cancelled'].includes(submission.status)) {
              result = submission;
              break;
            }
          }
          if (!result) throw new Error('Judge Worker chưa trả kết quả sau 90 giây. Có thể kiểm tra trạng thái trong Judge Admin.');
          const cases = result.testcases || [];
          const d = {
            all_ac: result.verdict === 'AC',
            passed: cases.filter(test => test.verdict === 'AC').length,
            total: cases.length,
            details: cases.map(test => ({
              case: test.name || test.id,
              status: test.verdict,
              time: (test.time_ms || 0) / 1000,
              feedback: test.message || '-'
            }))
          };
          overallBadge.className = d.all_ac ? 'badge badge-ac' : 'badge badge-wa';
          overallBadge.innerText = d.all_ac ? `100% ACCEPTED (${d.passed}/${d.total} tests)` : `CHƯA ĐẠT (${d.passed}/${d.total} tests)`;

          tbody.innerHTML = d.details.map(r => {
            const isAC = r.status === 'AC';
            const col = isAC ? '#10b981' : '#ef4444';
            return `
              <tr>
                <td style="font-family: monospace; font-weight: 700;">#${r.case}</td>
                <td><span style="display: inline-block; padding: 2px 8px; border-radius: 4px; font-weight: 700; font-size: 0.8rem; background: ${col}22; color: ${col}; border: 1px solid ${col}44;">${r.status}</span></td>
                <td style="color: var(--color-text-muted); font-size: 0.85rem;">${(r.time || 0).toFixed(4)}s</td>
                <td style="font-size: 0.85rem;">${r.feedback || '-'}</td>
              </tr>
            `;
          }).join('');

          if (isAllAC) {
            alert(`XÁC THỰC THÀNH CÔNG: Solution mẫu đạt 100% AC trên toàn bộ ${d.total} testcase! Đề bài đã đủ điều kiện Publish.`);
          } else {
            alert(`CẢNH BÁO: Solution chỉ vượt qua ${d.passed}/${d.total} testcase. Vui lòng kiểm tra lại testcase hoặc code giải trước khi publish!`);
          }

        } else {
          overallBadge.className = 'badge badge-wa';
          overallBadge.innerText = 'LỖI THỰC THI';
          tbody.innerHTML = `<tr><td colspan="4" style="color: #ef4444; padding: 1rem;">${res.error?.message || res.data?.message || 'Lỗi kiểm thử solution'}</td></tr>`;
        }
        btn.disabled = false;
        btn.innerText = '⚡ Chạy kiểm thử với toàn bộ testcases';
      } catch (e) {
        btn.disabled = false;
        btn.innerText = '⚡ Chạy kiểm thử với toàn bộ testcases';
        alert('Lỗi: ' + e.message);
      }
    }

    // PUBLISH TAB
    async function loadPublishTab() {
      if (!activeCode) return;
      try {
        const res = await fetch(`/api/v1/problems/${encodeURIComponent(activeCode)}`).then(r => r.json());
        if (res.status === 200 && res.data) {
          const d = res.data;
          document.getElementById('prevHeadTitle').innerText = `${d.code}: ${d.title}`;
          document.getElementById('prevHeadTime').innerText = `${d.time_limit}s`;
          document.getElementById('prevHeadMem').innerText = `${d.memory_limit} MB`;
          document.getElementById('prevHeadPoints').innerText = d.points;
          document.getElementById('prevContent').innerHTML = (d.statement && d.statement.html) ? d.statement.html : 'Chưa có nội dung đề bài';

          // Checklist
          const listEl = document.getElementById('publishChecklist');
          listEl.innerHTML = (d.checklist || []).map(c => `
            <li style="display: flex; align-items: center; gap: 0.5rem;">
              <span style="font-size: 1.1rem; color: ${c.ok ? '#10b981' : '#ef4444'};">${c.ok ? '✓' : '✗'}</span>
              <div>
                <strong>${c.name}</strong>: 
                <span style="color: var(--color-text-muted);">${c.desc}</span>
              </div>
            </li>
          `).join('');

          const pubBtn = document.getElementById('finalPublishBtn');
          const unpubBtn = document.getElementById('finalUnpublishBtn');

          if (d.is_public === true) {
            pubBtn.style.display = 'none';
            unpubBtn.style.display = 'block';
          } else {
            pubBtn.style.display = 'block';
            unpubBtn.style.display = 'none';
          }
        }
      } catch (e) {
        console.error('Error loading publish tab:', e);
      }
    }

    async function executePublish() {
      if (!activeCode) return;
      try {
        const res = await fetch(`/api/v1/problems/${encodeURIComponent(activeCode)}/publish`, {
          method: 'POST',
          headers: window.adminApiHeaders('application/json')
        }).then(r => r.json());

        if (res.status === 200) {
          alert('🎉 XUẤT BẢN THÀNH CÔNG!\nBài tập hiện đã xuất hiện trên trang chủ và kho bài tập cho toàn bộ thí sinh làm bài.');
          window.location.reload();
        } else {
          let err = (res.error && res.error.message) || 'Chưa đủ điều kiện xuất bản';
          if (res.error && res.error.checklist) {
            err += '\n\n' + res.error.checklist.map(c => `${c.ok ? '✓' : '✗'} ${c.name}: ${c.desc}`).join('\n');
          }
          alert(err);
        }
      } catch (e) {
        alert('Lỗi: ' + e.message);
      }
    }

    async function executeUnpublish() {
      if (!activeCode) return;
      try {
        const res = await fetch(`/api/v1/problems/${encodeURIComponent(activeCode)}/unpublish`, {
          method: 'POST',
          headers: window.adminApiHeaders('application/json')
        }).then(r => r.json());

        if (res.status === 200) {
          alert('Đã ẩn tạm thời bài tập khỏi kho công khai. Có thể công khai lại khi cần.');
          window.location.reload();
        } else {
          alert((res.error && res.error.message) || 'Không thể ẩn bài tập.');
        }
      } catch (e) {
        alert('Lỗi: ' + e.message);
      }
    }

    function quickPublish() {
      switchTab('publish');
      executePublish();
    }

    document.addEventListener('DOMContentLoaded', initStudio);
