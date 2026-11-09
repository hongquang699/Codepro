/**
 * CodeEditor Component
 * Handles textarea code input, line numbering synchronization, tab insertion, and shortcuts.
 */
class CodeEditor {
  constructor(containerId, textareaId, lineNumbersId) {
    this.container = document.getElementById(containerId);
    this.textarea = document.getElementById(textareaId);
    this.lineNumbers = document.getElementById(lineNumbersId);
    this.init();
  }

  init() {
    if (!this.textarea || !this.lineNumbers) return;

    this.textarea.addEventListener('input', () => this.updateLineNumbers());
    this.textarea.addEventListener('scroll', () => {
      this.lineNumbers.scrollTop = this.textarea.scrollTop;
    });

    // Tab key support
    this.textarea.addEventListener('keydown', (e) => {
      if (e.key === 'Tab') {
        e.preventDefault();
        const start = this.textarea.selectionStart;
        const end = this.textarea.selectionEnd;
        this.textarea.value = this.textarea.value.substring(0, start) + '    ' + this.textarea.value.substring(end);
        this.textarea.selectionStart = this.textarea.selectionEnd = start + 4;
        this.updateLineNumbers();
      }
    });

    this.updateLineNumbers();
  }

  updateLineNumbers() {
    const lines = this.textarea.value.split('\n').length;
    let numbers = '';
    for (let i = 1; i <= Math.max(lines, 20); i++) {
      numbers += i + '\n';
    }
    this.lineNumbers.textContent = numbers;
  }

  setValue(val) {
    if (this.textarea) {
      this.textarea.value = val;
      this.updateLineNumbers();
    }
  }

  getValue() {
    return this.textarea ? this.textarea.value : '';
  }
}

if (typeof window !== 'undefined') {
  window.CodeEditor = CodeEditor;
}
