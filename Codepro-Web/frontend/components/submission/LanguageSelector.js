/**
 * LanguageSelector Component
 * Manages selectable programming languages with templates.
 */
const LanguageSelector = {
  LANGUAGES: [
    { key: 'CPP17', label: 'C++17 (GNU G++)', ext: 'cpp', template: '#include <bits/stdc++.h>\nusing namespace std;\n\nint main() {\n    ios_base::sync_with_stdio(false);\n    cin.tie(NULL);\n    \n    // Nhập bài giải tại đây\n    \n    return 0;\n}\n' },
    { key: 'CPP20', label: 'C++20 (GNU G++)', ext: 'cpp', template: '#include <iostream>\n\nint main() {\n    std::cout << "Hello World" << std::endl;\n    return 0;\n}\n' },
    { key: 'C', label: 'C (GCC)', ext: 'c', template: '#include <stdio.h>\n\nint main() {\n    return 0;\n}\n' },
    { key: 'PY3', label: 'Python 3', ext: 'py', template: 'import sys\n\ndef main():\n    # Solution here\n    pass\n\nif __name__ == "__main__":\n    main()\n' },
    { key: 'PYPY3', label: 'PyPy 3', ext: 'py', template: 'def main():\n    # Solution here\n    pass\n\nif __name__ == "__main__":\n    main()\n' },
    { key: 'JAVA', label: 'Java (OpenJDK 17)', ext: 'java', template: 'import java.util.Scanner;\n\npublic class Main {\n    public static void main(String[] args) {\n        Scanner sc = new Scanner(System.in);\n    }\n}\n' },
    { key: 'PAS', label: 'Pascal (FPC)', ext: 'pas', template: 'program Solution;\nbegin\nend.\n' }
  ],

  renderOptions(selectedKey = 'CPP17') {
    return this.LANGUAGES.map(lang => {
      const selected = lang.key === selectedKey ? 'selected' : '';
      return `<option value="${lang.key}" ${selected}>${lang.label}</option>`;
    }).join('');
  },

  getTemplate(key) {
    const lang = this.LANGUAGES.find(l => l.key === key);
    return lang ? lang.template : '';
  }
};

if (typeof window !== 'undefined') {
  window.LanguageSelector = LanguageSelector;
}
