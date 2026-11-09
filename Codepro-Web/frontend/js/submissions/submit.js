/**
 * TMathCoding-Style Direct Submit & Judge Controller
 */
document.addEventListener('DOMContentLoaded', () => {
  const problemSelect = document.getElementById('problemSelect');
  const languageSelect = document.getElementById('languageSelect');
  const contestInput = document.getElementById('contestInput');
  const codeArea = document.getElementById('codeArea');
  const charCount = document.getElementById('charCount');
  const editorLangLabel = document.getElementById('editorLangLabel');
  const btnSubmit = document.getElementById('btnSubmit');
  const btnCustomTest = document.getElementById('btnCustomTest');
  const feedbackBox = document.getElementById('feedbackBox');
  const feedbackText = document.getElementById('feedbackText');
  const btnClearCode = document.getElementById('btnClearCode');
  const btnResetTemplate = document.getElementById('btnResetTemplate');

  // Specs Elements
  const sbTime = document.getElementById('sbTime');
  const sbMem = document.getElementById('sbMem');
  const sbAuthor = document.getElementById('sbAuthor');

  // Custom Test Modal Elements
  const customTestModal = document.getElementById('customTestModal');
  const btnCloseModal = document.getElementById('btnCloseModal');
  const btnRunTest = document.getElementById('btnRunTest');
  const customStdin = document.getElementById('customStdin');
  const customStdout = document.getElementById('customStdout');

  // Language Templates matching TMathCoding
  const TEMPLATES = {
    JAVA: `import java.util.*;
import java.io.*;

public class Main {
    public static void main(String[] args) throws IOException {
        BufferedReader br = new BufferedReader(new InputStreamReader(System.in));
        // TODO: Viết lời giải thuật toán ở đây
    }
}`,
    CPP17: `#include <bits/stdc++.h>
using namespace std;

int main() {
    ios_base::sync_with_stdio(false);
    cin.tie(NULL);

    // TODO: Viết lời giải thuật toán ở đây

    return 0;
}`,
    CPP20: `#include <iostream>
#include <vector>
using namespace std;

int main() {
    ios_base::sync_with_stdio(false);
    cin.tie(NULL);

    // TODO: Viết lời giải thuật toán ở đây

    return 0;
}`,
    C: `#include <stdio.h>

int main() {
    // TODO: Viết lời giải thuật toán ở đây
    return 0;
}`,
    PY3: `import sys

def main():
    input = sys.stdin.readline
    # TODO: Viết lời giải thuật toán ở đây
    pass

if __name__ == '__main__':
    main()`,
    PYPY3: `def main():
    # TODO: Viết lời giải thuật toán ở đây
    pass

if __name__ == '__main__':
    main()`,
    RUST: `use std::io::{self, BufRead};

fn main() {
    let stdin = io::stdin();
    // TODO: Viết lời giải thuật toán ở đây
}`,
    GO: `package main

import (
    "bufio"
    "fmt"
    "os"
)

func main() {
    // TODO: Viết lời giải thuật toán ở đây
}`,
    PAS: `program Solution;
begin
    // TODO: Viết lời giải thuật toán ở đây
end.`
  };

  const LANG_LABELS = {
    JAVA: 'Java 17 (OpenJDK)',
    CPP17: 'C++17 (GNU G++)',
    CPP20: 'C++20 (GNU G++)',
    C: 'C (GCC)',
    PY3: 'Python 3 (CPython)',
    PYPY3: 'PyPy 3',
    RUST: 'Rust 2021',
    GO: 'Go 1.22',
    PAS: 'Free Pascal (FPC)'
  };

  // Extract problem from URL (/submit/SUMA or ?problem=SUMA or /problems/SUMA/submit)
  const urlParams = new URLSearchParams(window.location.search);
  let problemCode = urlParams.get('problem') || urlParams.get('code') || '';
  const contestCode = urlParams.get('contest') || '';

  const pathParts = window.location.pathname.split('/').filter(Boolean);
  if (!problemCode) {
    if (pathParts[0] === 'submit' && pathParts[1]) {
      problemCode = pathParts[1];
    } else if (pathParts[0] === 'problems' && pathParts[2] === 'submit') {
      problemCode = pathParts[1];
    }
  }

  if (!problemCode) problemCode = 'SUMA';
  if (problemSelect) problemSelect.value = problemCode.toUpperCase();
  if (contestInput && contestCode) contestInput.value = contestCode;

  // Initialize Language Select
  const initialLang = localStorage.getItem('tmath_lang') || 'JAVA';
  if (languageSelect) {
    let opts = '';
    for (const [key, label] of Object.entries(LANG_LABELS)) {
      opts += `<option value="${key}" ${key === initialLang ? 'selected' : ''}>${label}</option>`;
    }
    languageSelect.innerHTML = opts;

    if (editorLangLabel) editorLangLabel.textContent = LANG_LABELS[initialLang] || initialLang;
    if (codeArea) {
      codeArea.value = TEMPLATES[initialLang] || '';
      updateCharCount();
    }

    languageSelect.addEventListener('change', () => {
      const selected = languageSelect.value;
      localStorage.setItem('tmath_lang', selected);
      if (editorLangLabel) editorLangLabel.textContent = LANG_LABELS[selected] || selected;

      const current = (codeArea ? codeArea.value : '').trim();
      const isDefaultTemplate = Object.values(TEMPLATES).some(t => t.trim() === current);
      if (!current || isDefaultTemplate) {
        if (codeArea) {
          codeArea.value = TEMPLATES[selected] || '';
          updateCharCount();
        }
      }
    });
  }

  // Character counter & Tab indentation
  if (codeArea) {
    codeArea.addEventListener('input', updateCharCount);
    codeArea.addEventListener('keydown', (e) => {
      if (e.key === 'Tab') {
        e.preventDefault();
        const start = codeArea.selectionStart;
        const end = codeArea.selectionEnd;
        codeArea.value = codeArea.value.substring(0, start) + '    ' + codeArea.value.substring(end);
        codeArea.selectionStart = codeArea.selectionEnd = start + 4;
        updateCharCount();
      } else if ((e.ctrlKey || e.metaKey) && e.key === 'Enter') {
        e.preventDefault();
        if (btnSubmit) btnSubmit.click();
      }
    });
  }

  function updateCharCount() {
    if (charCount && codeArea) {
      charCount.textContent = `${codeArea.value.length} ký tự`;
    }
  }

  // Clear code
  if (btnClearCode) {
    btnClearCode.addEventListener('click', () => {
      if (codeArea && confirm('Bạn có chắc chắn muốn xóa mã nguồn hiện tại?')) {
        codeArea.value = '';
        updateCharCount();
      }
    });
  }

  // Reset template / paste
  if (btnResetTemplate) {
    btnResetTemplate.addEventListener('click', () => {
      const selected = languageSelect ? languageSelect.value : 'JAVA';
      if (codeArea) {
        codeArea.value = TEMPLATES[selected] || '';
        updateCharCount();
      }
    });
  }

  // Fetch problem details for technical specifications
  loadProblemSpecs(problemCode);

  if (problemSelect) {
    problemSelect.addEventListener('change', () => {
      loadProblemSpecs(problemSelect.value.trim().toUpperCase());
    });
  }

  async function loadProblemSpecs(code) {
    if (!code) return;
    try {
      const res = await fetch(`/api/v2/problem/${encodeURIComponent(code)}`);
      if (res.ok) {
        const json = await res.json();
        const p = json?.data || json;
        if (sbTime) sbTime.textContent = p.time_limit ? `${p.time_limit}s` : '1.0s';
        if (sbMem) sbMem.textContent = p.memory_limit ? `${p.memory_limit} MB` : '64 MB';
        if (sbAuthor && p.author) sbAuthor.textContent = p.author;
      }
    } catch (e) {
      // Keep defaults
    }
  }

  // Submit Handler
  const submitForm = document.getElementById('submitForm');
  if (submitForm) {
    submitForm.addEventListener('submit', async (e) => {
      e.preventDefault();
      showFeedback('', false);

      const problem = (problemSelect ? problemSelect.value : '').trim().toUpperCase();
      const language = languageSelect ? languageSelect.value : 'JAVA';
      const contest = contestInput ? contestInput.value.trim() : null;
      const source = codeArea ? codeArea.value : '';

      if (!problem) {
        showFeedback('Vui lòng chọn hoặc nhập mã bài tập!', true);
        return;
      }
      if (!source.trim()) {
        showFeedback('Mã nguồn không được để trống!', true);
        return;
      }

      setSubmitLoading(true);

      try {
        const payload = {
          problem: problem,
          language: language,
          source_code: source,
          contest: contest || undefined
        };

        const res = await fetch('/api/v1/submissions/submit/', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            ...(localStorage.getItem('token') ? { 'Authorization': `Token ${localStorage.getItem('token')}` } : {})
          },
          body: JSON.stringify(payload)
        });

        const data = await res.json();

        if (res.ok && (data.success || data.id)) {
          const subId = data.submission_id || data.id;
          showFeedback(`Nộp bài thành công (#${subId})! Đang mở trang kết quả...`, false, true);
          setTimeout(() => {
            window.location.href = `/submissions/${subId}`;
          }, 600);
        } else {
          setSubmitLoading(false);
          showFeedback(data.error || 'Nộp bài thất bại. Vui lòng kiểm tra lại.', true);
        }
      } catch (err) {
        setSubmitLoading(false);
        showFeedback('Lỗi kết nối máy chủ. Vui lòng thử lại sau.', true);
      }
    });
  }

  function setSubmitLoading(isLoading) {
    if (!btnSubmit) return;
    btnSubmit.disabled = isLoading;
    if (isLoading) {
      btnSubmit.innerHTML = `<i class="fi fi-rr-spinner spin-icon"></i> Đang nộp bài...`;
    } else {
      btnSubmit.innerHTML = `🚀 Nộp bài (Submit)`;
    }
  }

  function showFeedback(msg, isError = true, isSuccess = false) {
    if (!feedbackBox) return;
    if (!msg) {
      feedbackBox.style.display = 'none';
      return;
    }
    feedbackBox.className = `tmath-feedback-box ${isError ? 'error' : (isSuccess ? 'success' : '')}`;
    if (feedbackText) feedbackText.textContent = msg;
    feedbackBox.style.display = 'flex';
  }

  // Custom Test Modal
  if (btnCustomTest && customTestModal) {
    btnCustomTest.addEventListener('click', () => {
      customTestModal.style.display = 'flex';
    });
  }

  if (btnCloseModal && customTestModal) {
    btnCloseModal.addEventListener('click', () => {
      customTestModal.style.display = 'none';
    });
  }

  if (customTestModal) {
    customTestModal.addEventListener('click', (e) => {
      if (e.target === customTestModal) {
        customTestModal.style.display = 'none';
      }
    });
  }

  // A public custom-input runner is not available yet; do not create a real
  // submission and present its verdict as if it used the supplied stdin.
  if (btnRunTest) {
    btnRunTest.disabled = true;
    btnRunTest.textContent = 'Chưa hỗ trợ';
    if (customStdin) customStdin.disabled = true;
    if (customStdout) customStdout.textContent = 'Chạy thử với đầu vào tùy chỉnh chưa được hỗ trợ.';
  }
});
