/**
 * CodeProOJ - Code Editor Helper
 */
const CodeEditor = {
  setup(textareaId, gutterId) {
    const ta = document.getElementById(textareaId);
    const gutter = gutterId ? document.getElementById(gutterId) : null;
    if (!ta) return;

    // Handle Tab key indentation
    ta.addEventListener('keydown', (e) => {
      if (e.key === 'Tab') {
        e.preventDefault();
        const start = ta.selectionStart;
        const end = ta.selectionEnd;
        ta.value = ta.value.substring(0, start) + '    ' + ta.value.substring(end);
        ta.selectionStart = ta.selectionEnd = start + 4;
        if (gutter) this.updateLineNumbers(ta, gutter);
      }
    });

    if (gutter) {
      ta.addEventListener('input', () => this.updateLineNumbers(ta, gutter));
      ta.addEventListener('scroll', () => {
        gutter.scrollTop = ta.scrollTop;
      });
      this.updateLineNumbers(ta, gutter);
    }
  },

  updateLineNumbers(ta, gutter) {
    const lines = ta.value.split('\n').length;
    let nums = '';
    for (let i = 1; i <= Math.max(1, lines); i++) {
      nums += i + '<br>';
    }
    gutter.innerHTML = nums;
  }
};

window.CodeEditor = CodeEditor;
