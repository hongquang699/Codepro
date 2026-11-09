/**
 * CodeProOJ - Professional Online IDE Engine
 * Powered by Microsoft Monaco Editor (VS Code) with High-Performance Fallback
 */

(function(window) {
  'use strict';

  const DEFAULT_TEMPLATES = {
    CPP17: `#include <iostream>
#include <vector>
#include <string>
#include <algorithm>

using namespace std;

int main() {
    ios_base::sync_with_stdio(false);
    cin.tie(NULL);

    // TODO: Viết thuật toán giải bài tập tại đây
    long long a, b;
    if (cin >> a >> b) {
        cout << a + b << "\\n";
    }

    return 0;
}`,
    CPP20: `#include <iostream>
#include <vector>
#include <ranges>
#include <algorithm>

using namespace std;

int main() {
    ios_base::sync_with_stdio(false);
    cin.tie(NULL);

    // C++20 Solution
    long long a, b;
    if (cin >> a >> b) {
        cout << a + b << "\\n";
    }

    return 0;
}`,
    C11: `#include <stdio.h>

int main() {
    long long a, b;
    if (scanf("%lld %lld", &a, &b) == 2) {
        printf("%lld\\n", a + b);
    }
    return 0;
}`,
    PY3: `import sys

def solve():
    input_data = sys.stdin.read().split()
    if not input_data:
        return
    a = int(input_data[0])
    b = int(input_data[1])
    print(a + b)

if __name__ == '__main__':
    solve()`,
    JAVA17: `import java.util.Scanner;

public class Main {
    public static void main(String[] args) {
        Scanner sc = new Scanner(System.in);
        if (sc.hasNextLong()) {
            long a = sc.nextLong();
            long b = sc.nextLong();
            System.out.println(a + b);
        }
        sc.close();
    }
}`,
    RUST: `use std::io::{self, Read};

fn main() {
    let mut buffer = String::new();
    io::stdin().read_to_string(&mut buffer).unwrap();
    let mut words = buffer.split_whitespace();
    
    if let (Some(a_str), Some(b_str)) = (words.next(), words.next()) {
        let a: i64 = a_str.parse().unwrap();
        let b: i64 = b_str.parse().unwrap();
        println!("{}", a + b);
    }
}`,
    GO: `package main

import (
    "fmt"
)

func main() {
    var a, b int64
    if _, err := fmt.Scan(&a, &b); err == nil {
        fmt.Println(a + b)
    }
}`,
    PAS: `program Solution;
var
    a, b: Int64;
begin
    if not SeekEof then
    begin
        ReadLn(a, b);
        WriteLn(a + b);
    end;
end.`
  };

  DEFAULT_TEMPLATES.PYPY3 = `a, b = map(int, input().split())
print(a + b)`;

  const MONACO_LANG_MAP = {
    CPP17: 'cpp',
    CPP20: 'cpp',
    C11: 'c',
    PY3: 'python',
    PYPY3: 'python',
    JAVA17: 'java',
    RUST: 'rust',
    GO: 'go',
    PAS: 'pascal'
  };

  const LANG_DISPLAY_NAMES = {
    CPP17: 'C++17 (GNU G++ 11.2)',
    CPP20: 'C++20 (GNU G++ 13)',
    C11: 'C11 (GNU GCC)',
    PY3: 'Python 3 (CPython 3.12)',
    PYPY3: 'PyPy 3',
    JAVA17: 'Java 17 (OpenJDK)',
    RUST: 'Rust 2021',
    GO: 'Go 1.22',
    PAS: 'Free Pascal 3.2'
  };

  class CodeIDE {
    constructor() {
      this.editor = null;
      this.isMonacoReady = false;
      this.currentLang = 'CPP17';
      this.currentTheme = 'vs-dark';
      this.currentFontSize = 14;
      this.isFullscreen = false;
      this.problemCode = '';
      this.options = {};
    }

    /**
     * Khởi tạo IDE code editor
     */
    init(config = {}) {
      this.options = Object.assign({
        containerId: 'monacoEditor',
        fallbackTextareaId: 'sourceCodeArea',
        fallbackGutterId: 'editorGutter',
        languageSelectId: 'selectLanguage',
        problemCode: 'SUMA',
        initialCode: '',
        onCodeChange: null,
        onSubmit: null
      }, config);

      this.problemCode = this.options.problemCode || 'DEFAULT';
      this.currentLang = this.options.defaultLang || 'CPP17';

      // Load saved user preferences
      this.loadPreferences();

      // Check draft in localStorage
      const draftKey = `draft_${this.problemCode}_${this.currentLang}`;
      const savedDraft = localStorage.getItem(draftKey);
      this.initialCode = savedDraft || this.options.initialCode || DEFAULT_TEMPLATES[this.currentLang] || '';

      // Initialize UI controls
      this.bindToolbarEvents();

      // Immediately activate Fallback Textarea so user can see & type code without waiting
      this.setupFallbackEditor();

      // Try load Monaco Editor from CDN
      this.loadMonacoEditor();
    }

    loadPreferences() {
      const savedTheme = localStorage.getItem('ide_theme');
      if (savedTheme) this.currentTheme = savedTheme;

      const savedFontSize = localStorage.getItem('ide_font_size');
      if (savedFontSize) this.currentFontSize = parseInt(savedFontSize, 10) || 14;

      // Sync select boxes if present
      const themeSelect = document.getElementById('ideThemeSelect');
      if (themeSelect) themeSelect.value = this.currentTheme;

      const fontSelect = document.getElementById('ideFontSizeSelect');
      if (fontSelect) fontSelect.value = this.currentFontSize;
    }

    loadMonacoEditor() {
      const container = document.getElementById(this.options.containerId);
      if (!container) return;

      if (window.monaco) {
        this.createMonacoInstance();
        return;
      }

      // Check if loader script is already in document
      if (!window.require) {
        const loaderScript = document.createElement('script');
        loaderScript.src = 'https://cdn.jsdelivr.net/npm/monaco-editor@0.45.0/min/vs/loader.js';
        loaderScript.async = true;
        loaderScript.onload = () => {
          this.configureMonacoRequire();
        };
        loaderScript.onerror = () => {
          console.warn('Không thể tải Monaco Editor từ CDN chính, giữ nguyên trình soạn thảo mặc định');
          this.setupFallbackEditor();
        };
        document.head.appendChild(loaderScript);
      } else {
        this.configureMonacoRequire();
      }
    }

    configureMonacoRequire() {
      try {
        window.require.config({
          paths: { vs: 'https://cdn.jsdelivr.net/npm/monaco-editor@0.45.0/min/vs' }
        });

        // Add a safety timeout in case CDN hangs
        let loaded = false;
        const timer = setTimeout(() => {
          if (!loaded) {
            console.info('Monaco CDN loading timeout, continuing with native editor');
          }
        }, 6000);

        window.require(['vs/editor/editor.main'], () => {
          loaded = true;
          clearTimeout(timer);
          this.createMonacoInstance();
        }, (err) => {
          console.warn('Lỗi tải vs/editor/editor.main:', err);
          this.setupFallbackEditor();
        });
      } catch (err) {
        console.warn('Lỗi khởi tạo require Monaco:', err);
        this.setupFallbackEditor();
      }
    }

    createMonacoInstance() {
      const container = document.getElementById(this.options.containerId);
      if (!container) return;

      const monacoLang = MONACO_LANG_MAP[this.currentLang] || 'cpp';
      const currentCode = this.getValue() || this.initialCode;

      try {
        if (container) container.style.display = 'block';
        this.editor = window.monaco.editor.create(container, {
          value: currentCode,
          language: monacoLang,
          theme: this.currentTheme,
          fontSize: this.currentFontSize,
          fontFamily: "'JetBrains Mono', 'Fira Code', 'Cascadia Code', Consolas, 'Courier New', monospace",
          fontLigatures: true,
          automaticLayout: true,
          tabSize: 4,
          insertSpaces: true,
          lineNumbers: 'on',
          roundedSelection: true,
          scrollBeyondLastLine: false,
          minimap: { enabled: true, maxColumn: 72 },
          bracketPairColorization: { enabled: true },
          cursorBlinking: 'smooth',
          cursorSmoothCaretAnimation: 'on',
          renderWhitespace: 'selection',
          padding: { top: 12, bottom: 12 },
          folding: true,
          matchBrackets: 'always',
          autoClosingBrackets: 'always',
          autoClosingQuotes: 'always',
          formatOnPaste: true
        });

        this.isMonacoReady = true;

        // Hide fallback textarea wrapper if visible
        const fallback = document.getElementById('ideFallbackWrapper');
        if (fallback) fallback.style.display = 'none';

        // Update Status Bar on change
        this.editor.onDidChangeCursorPosition((e) => {
          this.updateCursorStatus(e.position.lineNumber, e.position.column);
        });

        this.editor.onDidChangeModelContent(() => {
          const code = this.editor.getValue();
          this.updateDocumentStats(code);
          this.saveDraftDebounced(code);
          if (typeof this.options.onCodeChange === 'function') {
            this.options.onCodeChange(code);
          }
        });

        // Hotkeys inside Monaco
        this.editor.addCommand(window.monaco.KeyMod.CtrlCmd | window.monaco.KeyCode.Enter, () => {
          if (typeof this.options.onSubmit === 'function') {
            this.options.onSubmit();
          } else {
            const submitBtn = document.getElementById('btnSubmitSolution');
            if (submitBtn) submitBtn.click();
          }
        });

        this.editor.addCommand(window.monaco.KeyMod.CtrlCmd | window.monaco.KeyCode.KeyS, () => {
          this.saveDraft(this.editor.getValue());
        });

        // Trigger initial stats
        this.updateDocumentStats(this.editor.getValue());
        this.updateCursorStatus(1, 1);
        this.updateLanguageBadge(this.currentLang);

      } catch (err) {
        console.error('Lỗi khởi tạo Monaco Editor:', err);
        this.setupFallbackEditor();
      }
    }

    setupFallbackEditor() {
      this.isMonacoReady = false;
      const fallback = document.getElementById(this.options.fallbackTextareaId ? 'ideFallbackWrapper' : '');
      const monacoBox = document.getElementById(this.options.containerId);
      if (monacoBox && !this.editor) monacoBox.style.display = 'none';
      if (fallback) fallback.style.display = 'flex';

      const textarea = document.getElementById(this.options.fallbackTextareaId);
      if (textarea) {
        if (!textarea.value || textarea.value.trim() === '') {
          textarea.value = this.initialCode;
        }
        textarea.oninput = () => {
          this.updateFallbackGutter();
          this.updateDocumentStats(textarea.value);
          this.saveDraftDebounced(textarea.value);
          if (typeof this.options.onCodeChange === 'function') {
            this.options.onCodeChange(textarea.value);
          }
        };
        textarea.onkeydown = (e) => {
          if (e.key === 'Tab') {
            e.preventDefault();
            const start = textarea.selectionStart;
            const end = textarea.selectionEnd;
            textarea.value = textarea.value.substring(0, start) + '    ' + textarea.value.substring(end);
            textarea.selectionStart = textarea.selectionEnd = start + 4;
            this.updateFallbackGutter();
            this.updateDocumentStats(textarea.value);
          } else if (e.key === 'Enter' && (e.ctrlKey || e.metaKey)) {
            e.preventDefault();
            if (typeof this.options.onSubmit === 'function') this.options.onSubmit();
          }
        };
        this.updateFallbackGutter();
        this.updateDocumentStats(textarea.value);
        if (typeof this.options.onCodeChange === 'function') {
          this.options.onCodeChange(textarea.value);
        }
      }
    }

    updateFallbackGutter() {
      const textarea = document.getElementById(this.options.fallbackTextareaId);
      const gutter = document.getElementById(this.options.fallbackGutterId);
      if (!textarea || !gutter) return;
      const lines = textarea.value.split('\n').length;
      let html = '';
      for (let i = 1; i <= Math.max(lines, 1); i++) {
        html += `${i}<br>`;
      }
      gutter.innerHTML = html;
    }

    bindToolbarEvents() {
      // Language Change
      const langSelect = document.getElementById(this.options.languageSelectId);
      if (langSelect) {
        langSelect.addEventListener('change', () => {
          this.setLanguage(langSelect.value);
        });
      }

      // Theme Selector
      const themeSelect = document.getElementById('ideThemeSelect');
      if (themeSelect) {
        themeSelect.addEventListener('change', () => {
          this.setTheme(themeSelect.value);
        });
      }

      // Font Size Selector
      const fontSelect = document.getElementById('ideFontSizeSelect');
      if (fontSelect) {
        fontSelect.addEventListener('change', () => {
          this.setFontSize(parseInt(fontSelect.value, 10));
        });
      }

      // Format Button
      const btnFormat = document.getElementById('btnIdeFormat');
      if (btnFormat) {
        btnFormat.addEventListener('click', () => this.formatDocument());
      }

      // Template Button
      const btnTemplate = document.getElementById('btnIdeTemplate');
      if (btnTemplate) {
        btnTemplate.addEventListener('click', () => this.loadTemplateWithPrompt());
      }

      // Copy Button
      const btnCopy = document.getElementById('btnIdeCopy');
      if (btnCopy) {
        btnCopy.addEventListener('click', () => this.copyCode());
      }

      // Clear Button
      const btnClear = document.getElementById('btnIdeClear');
      if (btnClear) {
        btnClear.addEventListener('click', () => this.clearCode());
      }

      // Fullscreen Button
      const btnFullscreen = document.getElementById('btnIdeFullscreen');
      if (btnFullscreen) {
        btnFullscreen.addEventListener('click', () => this.toggleFullscreen());
      }

      // Keyboard Esc to exit fullscreen
      document.addEventListener('keydown', (e) => {
        if (e.key === 'Escape' && this.isFullscreen) {
          this.toggleFullscreen(false);
        }
      });
    }

    getValue() {
      if (this.isMonacoReady && this.editor) {
        try {
          return this.editor.getValue();
        } catch (e) {}
      }
      const textarea = document.getElementById(this.options.fallbackTextareaId);
      if (textarea && textarea.value) return textarea.value;
      return this.initialCode || '';
    }

    setValue(code) {
      if (this.isMonacoReady && this.editor) {
        this.editor.setValue(code);
      } else {
        const textarea = document.getElementById(this.options.fallbackTextareaId);
        if (textarea) {
          textarea.value = code;
          this.updateFallbackGutter();
        }
      }
      this.updateDocumentStats(code);
    }

    setLanguage(langKey) {
      this.currentLang = langKey;
      const monacoLang = MONACO_LANG_MAP[langKey] || 'cpp';

      if (this.isMonacoReady && this.editor) {
        const model = this.editor.getModel();
        if (model && window.monaco) {
          window.monaco.editor.setModelLanguage(model, monacoLang);
        }
      }

      this.updateLanguageBadge(langKey);

      // Check if current code is template or empty -> replace with new lang template
      const currentCode = this.getValue().trim();
      const isDefault = !currentCode || Object.values(DEFAULT_TEMPLATES).some(t => t.trim() === currentCode);
      if (isDefault) {
        this.setValue(DEFAULT_TEMPLATES[langKey] || '');
      }
    }

    setTheme(themeName) {
      this.currentTheme = themeName;
      localStorage.setItem('ide_theme', themeName);

      const ideFrame = document.querySelector('.ide-frame');
      if (ideFrame) {
        ideFrame.classList.remove('theme-light', 'theme-hc-black');
        if (themeName === 'vs') ideFrame.classList.add('theme-light');
        if (themeName === 'hc-black') ideFrame.classList.add('theme-hc-black');
      }

      if (this.isMonacoReady && window.monaco) {
        window.monaco.editor.setTheme(themeName);
      }
    }

    setFontSize(size) {
      this.currentFontSize = size;
      localStorage.setItem('ide_font_size', size);

      if (this.isMonacoReady && this.editor) {
        this.editor.updateOptions({ fontSize: size });
      } else {
        const textarea = document.getElementById(this.options.fallbackTextareaId);
        if (textarea) textarea.style.fontSize = `${size}px`;
      }
    }

    formatDocument() {
      if (this.isMonacoReady && this.editor) {
        const action = this.editor.getAction('editor.action.formatDocument');
        if (action) {
          action.run();
          this.showToast('Đã định dạng mã nguồn!');
        } else {
          this.showToast('Không có formatter tích hợp cho ngôn ngữ này.');
        }
      } else {
        this.showToast('Chức năng chỉ hỗ trợ trên trình soạn thảo Monaco.');
      }
    }

    toggleFullscreen(forceState) {
      this.isFullscreen = forceState !== undefined ? forceState : !this.isFullscreen;
      const ideFrame = document.querySelector('.ide-frame');
      const btnFullscreen = document.getElementById('btnIdeFullscreen');

      if (!ideFrame) return;

      if (this.isFullscreen) {
        ideFrame.classList.add('fullscreen-mode');
        document.body.classList.add('ide-fullscreen-active');
        if (btnFullscreen) {
          btnFullscreen.innerHTML = '⛶ Thu nhỏ (Esc)';
          btnFullscreen.classList.add('ide-fullscreen-exit-btn');
        }
      } else {
        ideFrame.classList.remove('fullscreen-mode');
        document.body.classList.remove('ide-fullscreen-active');
        if (btnFullscreen) {
          btnFullscreen.innerHTML = '⛶ Toàn màn hình';
          btnFullscreen.classList.remove('ide-fullscreen-exit-btn');
        }
      }

      if (this.isMonacoReady && this.editor) {
        setTimeout(() => this.editor.layout(), 100);
      }
    }

    loadTemplateWithPrompt() {
      const template = DEFAULT_TEMPLATES[this.currentLang] || '';
      if (!template) return;

      const current = this.getValue().trim();
      if (current && !confirm('Bạn có muốn tải lại code mẫu? Mã hiện tại sẽ được thay thế.')) {
        return;
      }
      this.setValue(template);
      this.showToast('Đã tải mã mẫu ' + (LANG_DISPLAY_NAMES[this.currentLang] || this.currentLang));
    }

    copyCode() {
      const code = this.getValue();
      navigator.clipboard.writeText(code).then(() => {
        this.showToast('Đã sao chép mã nguồn vào clipboard!');
      }).catch(() => {
        this.showToast('Không thể sao chép tự động.');
      });
    }

    clearCode() {
      if (confirm('Bạn có chắc chắn muốn xóa toàn bộ mã nguồn đang soạn thảo?')) {
        this.setValue('');
        this.showToast('Đã xóa trắng mã nguồn.');
      }
    }

    updateCursorStatus(line, col) {
      const el = document.getElementById('ideCursorPos');
      if (el) el.textContent = `Ln ${line}, Col ${col}`;
    }

    updateDocumentStats(text) {
      const lines = text ? text.split('\n').length : 1;
      const chars = text ? text.length : 0;

      const lineEl = document.getElementById('ideLineCount');
      if (lineEl) lineEl.textContent = `${lines} dòng`;

      const charEl = document.getElementById('ideCharCount');
      if (charEl) charEl.textContent = `${chars} ký tự`;

      const statsBar = document.getElementById('ideStatsStatus');
      if (statsBar) statsBar.textContent = `${lines} dòng, ${chars} ký tự`;
    }

    updateLanguageBadge(langKey) {
      const label = LANG_DISPLAY_NAMES[langKey] || langKey;
      const pill = document.getElementById('activeLangLabel');
      if (pill) pill.textContent = label;

      const statusLang = document.getElementById('ideStatusLang');
      if (statusLang) statusLang.textContent = label;
    }

    saveDraftDebounced(code) {
      clearTimeout(this._saveTimer);
      this._saveTimer = setTimeout(() => {
        this.saveDraft(code);
      }, 800);
    }

    saveDraft(code) {
      const draftKey = `draft_${this.problemCode}_${this.currentLang}`;
      try {
        localStorage.setItem(draftKey, code);
        const badge = document.getElementById('ideAutosaveBadge');
        if (badge) {
          badge.innerHTML = '<span class="ide-autosave-dot"></span> Đã lưu nháp';
        }
      } catch (e) {
        console.warn('Lỗi lưu nháp vào LocalStorage:', e);
      }
    }

    showToast(msg) {
      let toast = document.getElementById('ideToast');
      if (!toast) {
        toast = document.createElement('div');
        toast.id = 'ideToast';
        toast.style.cssText = `
          position: fixed;
          bottom: 2rem;
          right: 2rem;
          background: var(--color-bg-secondary);
          color: #38bdf8;
          border: 1px solid var(--color-border);
          padding: 0.65rem 1.25rem;
          border-radius: 8px;
          box-shadow: 0 10px 25px rgba(0,0,0,0.5);
          font-size: 0.85rem;
          font-weight: 600;
          z-index: 9999999;
          transition: opacity 0.3s ease;
          display: flex;
          align-items: center;
          gap: 0.5rem;
        `;
        document.body.appendChild(toast);
      }
      toast.textContent = msg;
      toast.style.opacity = '1';
      clearTimeout(this._toastTimer);
      this._toastTimer = setTimeout(() => {
        toast.style.opacity = '0';
      }, 2500);
    }
  }

  window.CodeIDE = new CodeIDE();

})(window);
