/**
 * CodeProOJ - Global Theme Manager
 * Manages Dual Themes (Light / Dark) and System Preference Sync
 * Preserves user preference across page navigation via localStorage ('cp_theme')
 */
(function() {
  'use strict';

  const STORAGE_KEY = 'cp_theme';
  const MODES = ['auto', 'light', 'dark'];

  function getSystemPreference() {
    if (window.matchMedia && window.matchMedia('(prefers-color-scheme: light)').matches) {
      return 'light';
    }
    return 'dark';
  }

  function getMode() {
    const saved = localStorage.getItem(STORAGE_KEY);
    if (saved && MODES.includes(saved)) {
      return saved;
    }
    // Light is the default; users can still choose dark or auto.
    return 'light';
  }

  function getResolvedTheme() {
    const mode = getMode();
    if (mode === 'auto') {
      return getSystemPreference();
    }
    return mode;
  }

  function applyTheme(mode) {
    const effectiveMode = mode || getMode();
    const resolved = effectiveMode === 'auto' ? getSystemPreference() : effectiveMode;

    document.documentElement.setAttribute('data-theme', resolved);
    document.documentElement.setAttribute('data-theme-mode', effectiveMode);
    if (document.body) {
      document.body.setAttribute('data-theme', resolved);
    }

    // Meta theme-color update for mobile browser title bars
    let metaThemeColor = document.querySelector('meta[name="theme-color"]');
    if (!metaThemeColor) {
      metaThemeColor = document.createElement('meta');
      metaThemeColor.name = 'theme-color';
      document.head.appendChild(metaThemeColor);
    }
    metaThemeColor.content = resolved === 'light' ? '#eef3f5' : '#07131f';

    updateToggleButtons();

    // Custom event for reactive components (charts, Monaco editor, etc.)
    window.dispatchEvent(new CustomEvent('cp-theme-changed', {
      detail: { mode: effectiveMode, resolved }
    }));
  }

  function setMode(mode) {
    if (!MODES.includes(mode)) mode = 'auto';
    localStorage.setItem(STORAGE_KEY, mode);
    applyTheme(mode);
  }

  function cycleTheme() {
    // 2-way direct toggle: if current resolved is dark -> switch to light, else switch to dark
    const resolved = getResolvedTheme();
    const nextMode = resolved === 'light' ? 'dark' : 'light';
    setMode(nextMode);
    return nextMode;
  }

  function updateToggleButtons() {
    const mode = getMode();
    const resolved = getResolvedTheme();

    // Update all elements with class 'cp-theme-toggle' or '[data-theme-toggle]'
    const buttons = document.querySelectorAll('.cp-theme-toggle, [data-theme-toggle]');
    buttons.forEach(btn => {
      // Icon mapping:
      // auto: system laptop / auto icon
      // light: sun icon
      // dark: moon icon
      let iconName = 'moon';
      let title = 'Chế độ: Tối (Dark)';
      if (mode === 'auto') {
        iconName = resolved === 'light' ? 'sun' : 'moon';
        title = `Chế độ: Tự động theo hệ thống (${resolved === 'light' ? 'Sáng' : 'Tối'})`;
      } else if (mode === 'light') {
        iconName = 'sun';
        title = 'Chế độ: Sáng (Light)';
      }

      btn.setAttribute('title', title);
      btn.setAttribute('aria-label', title);
      btn.dataset.currentMode = mode;

      const iconWrap = btn.querySelector('.theme-icon-wrap') || btn;
      if (window.CPIcons) {
        iconWrap.innerHTML = window.CPIcons.get(iconName, 18);
      }
      
      const labelWrap = btn.querySelector('.theme-label');
      if (labelWrap) {
        if (mode === 'auto') labelWrap.textContent = 'Auto';
        else if (mode === 'light') labelWrap.textContent = 'Light';
        else labelWrap.textContent = 'Dark';
      }
    });
  }

  // Listen to system preference changes when in 'auto' mode
  if (window.matchMedia) {
    const mediaQuery = window.matchMedia('(prefers-color-scheme: light)');
    const handler = (e) => {
      if (getMode() === 'auto') {
        applyTheme('auto');
      }
    };
    if (mediaQuery.addEventListener) {
      mediaQuery.addEventListener('change', handler);
    } else if (mediaQuery.addListener) {
      mediaQuery.addListener(handler);
    }
  }

  // Fast apply immediately on script load to prevent FOUC
  applyTheme();

  // Attach DOMContentLoaded listener for buttons
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
      updateToggleButtons();
    });
  } else {
    updateToggleButtons();
  }

  // Expose global API
  window.CPTheme = {
    getMode,
    getResolvedTheme,
    setMode,
    cycleTheme,
    apply: applyTheme,
    updateButtons: updateToggleButtons
  };
})();
