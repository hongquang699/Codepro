const CONFIG = {
  API_BASE_URL: '/api/v2',
  WS_URL: `${location.protocol === 'https:' ? 'wss:' : 'ws:'}//${location.host}/ws/submissions/`,
  PLATFORM_NAME: 'CodeProOJ',
  SUPPORTED_LANGUAGES: [
    { key: 'CPP17', name: 'C++17 (GNU G++)', ext: 'cpp' },
    { key: 'C11', name: 'C11 (GNU GCC)', ext: 'c' },
    { key: 'PY3', name: 'Python 3.12', ext: 'py' },
    { key: 'PYPY3', name: 'PyPy 3', ext: 'py' },
    { key: 'JAVA17', name: 'Java 17 (OpenJDK)', ext: 'java' },
    { key: 'RUST', name: 'Rust 1.75', ext: 'rs' },
    { key: 'GO', name: 'Go 1.22', ext: 'go' },
    { key: 'PAS', name: 'Free Pascal 3.2', ext: 'pas' }
  ]
};

// Ensure modern SVG icon system is loaded
if (typeof CPIcons === 'undefined' && typeof document !== 'undefined') {
  const iconScript = document.createElement('script');
  iconScript.src = '/frontend/js/core/icons.js';
  document.head.appendChild(iconScript);
}
