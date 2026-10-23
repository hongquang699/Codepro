/**
 * CodeProOJ - Flaticon Vector Icons & Stickers Engine (flaticon.com)
 * High-performance, zero-latency vector icon rendering with Flaticon Uicons,
 * Web Component support, universal emoji transformer, and dynamic UI enhancements.
 */

(function () {
  'use strict';

  // Map icon names to official Flaticon Uicons classes (Regular Rounded / Solid Rounded)
  const NAME_TO_FLATICON = {
    // Navigation & General
    'home': 'fi-rr-home',
    'code': 'fi-rr-code-compare',
    'trophy': 'fi-rr-trophy',
    'award': 'fi-rr-medal',
    'send': 'fi-rr-paper-plane',
    'book': 'fi-rr-book-alt',
    'users': 'fi-rr-users',
    'user': 'fi-rr-user',
    'shield': 'fi-rr-shield-check',
    'judge': 'fi-rr-scale',
    'dashboard': 'fi-rr-apps',
    'bolt': 'fi-rr-bolt',
    'chart': 'fi-rr-chart-histogram',
    'database': 'fi-rr-database',
    'settings': 'fi-rr-settings',
    'search': 'fi-rr-search',
    'filter': 'fi-rr-filter',
    'plus': 'fi-rr-plus',
    'check': 'fi-rr-check',
    'cross': 'fi-rr-cross',
    'clock': 'fi-rr-time-fast',
    'cpu': 'fi-rr-microchip',
    'terminal': 'fi-rr-terminal',
    'rocket': 'fi-rr-rocket',
    'globe': 'fi-rr-globe',
    'graduation-cap': 'fi-rr-graduation-cap',
    'building': 'fi-rr-building',
    'snowflake': 'fi-rr-snowflake',
    'bell': 'fi-rr-bell',
    'lock': 'fi-rr-lock',
    'unlock': 'fi-rr-unlock',
    'sparkles': 'fi-rr-sparkles',
    'refresh': 'fi-rr-refresh',
    'trash': 'fi-rr-trash',
    'external-link': 'fi-rr-arrow-up-right-from-square',
    'eye': 'fi-rr-eye',
    'edit': 'fi-rr-edit',
    'pencil': 'fi-rr-pencil',
    'document': 'fi-rr-document',
    'flag': 'fi-rr-flag',
    'inbox': 'fi-rr-inbox',
    'flame': 'fi-rr-flame',
    'star': 'fi-rr-star',
    'github': 'fi-brands-github',
    'list-check': 'fi-rr-list-check',
    'tag': 'fi-rr-tag',
    'play': 'fi-rr-play',
    'download': 'fi-rr-download',
    'upload': 'fi-rr-upload',
    'copy': 'fi-rr-copy',
    'share': 'fi-rr-share',
    'calculator': 'fi-rr-calculator',
    'key': 'fi-rr-key',
    'info': 'fi-rr-info',
    'warning': 'fi-rr-exclamation',
    'heart': 'fi-rr-heart',
    'comment': 'fi-rr-comment-alt',
    'folder': 'fi-rr-folder',
    'calendar': 'fi-rr-calendar',
    'laptop': 'fi-rr-laptop',
    'puzzle': 'fi-rr-puzzle-piece'
  };

  // Comprehensive Emoji to Flaticon Uicons map
  const EMOJI_TO_FLATICON = {
    '🚀': { icon: 'fi-rr-rocket', color: '#f59e0b' },
    '📚': { icon: 'fi-rr-book-alt', color: '#3b82f6' },
    '📖': { icon: 'fi-rr-book', color: '#3b82f6' },
    '🏆': { icon: 'fi-rr-trophy', color: '#eab308' },
    '👑': { icon: 'fi-rr-crown', color: '#eab308' },
    '🥇': { icon: 'fi-rr-medal', color: '#fbbf24' },
    '🥈': { icon: 'fi-rr-medal', color: '#94a3b8' },
    '🥉': { icon: 'fi-rr-medal', color: '#d97706' },
    '🎖️': { icon: 'fi-rr-medal', color: '#a855f7' },
    '🎖': { icon: 'fi-rr-medal', color: '#a855f7' },
    '⭐': { icon: 'fi-rr-star', color: '#eab308' },
    '🌟': { icon: 'fi-rr-sparkles', color: '#eab308' },
    '✨': { icon: 'fi-rr-sparkles', color: '#fbbf24' },
    '💡': { icon: 'fi-rr-bulb', color: '#f59e0b' },
    '🧩': { icon: 'fi-rr-puzzle-piece', color: '#8b5cf6' },
    '🌲': { icon: 'fi-rr-tree', color: '#10b981' },
    '🌐': { icon: 'fi-rr-globe', color: '#0ea5e9' },
    '🌍': { icon: 'fi-rr-globe', color: '#0ea5e9' },
    '🌎': { icon: 'fi-rr-globe', color: '#0ea5e9' },
    '🌏': { icon: 'fi-rr-globe', color: '#0ea5e9' },
    '⚡': { icon: 'fi-rr-bolt', color: '#f59e0b' },
    '🔥': { icon: 'fi-rr-flame', color: '#ef4444' },
    '📢': { icon: 'fi-rr-megaphone', color: '#3b82f6' },
    '🔔': { icon: 'fi-rr-bell', color: '#f59e0b' },
    '📊': { icon: 'fi-rr-chart-histogram', color: '#38bdf8' },
    '📈': { icon: 'fi-rr-chart-line-up', color: '#10b981' },
    '📉': { icon: 'fi-rr-chart-line-up', color: '#ef4444' },
    '⚖️': { icon: 'fi-rr-scale', color: '#6366f1' },
    '⚖': { icon: 'fi-rr-scale', color: '#6366f1' },
    '🛡️': { icon: 'fi-rr-shield-check', color: '#10b981' },
    '🛡': { icon: 'fi-rr-shield-check', color: '#10b981' },
    '📝': { icon: 'fi-rr-edit', color: '#38bdf8' },
    '✏️': { icon: 'fi-rr-pencil', color: '#38bdf8' },
    '✏': { icon: 'fi-rr-pencil', color: '#38bdf8' },
    '✍️': { icon: 'fi-rr-edit', color: '#38bdf8' },
    '✍': { icon: 'fi-rr-edit', color: '#38bdf8' },
    '➕': { icon: 'fi-rr-plus', color: '#10b981' },
    '👥': { icon: 'fi-rr-users', color: '#38bdf8' },
    '👤': { icon: 'fi-rr-user', color: '#94a3b8' },
    '📋': { icon: 'fi-rr-document', color: '#a78bfa' },
    '📄': { icon: 'fi-rr-document-signed', color: '#94a3b8' },
    '📑': { icon: 'fi-rr-folder', color: '#f59e0b' },
    '📁': { icon: 'fi-rr-folder', color: '#f59e0b' },
    '🏷️': { icon: 'fi-rr-tag', color: '#f59e0b' },
    '🏷': { icon: 'fi-rr-tag', color: '#f59e0b' },
    '⚙️': { icon: 'fi-rr-settings', color: '#94a3b8' },
    '⚙': { icon: 'fi-rr-settings', color: '#94a3b8' },
    '🔧': { icon: 'fi-rr-wrench-simple', color: '#94a3b8' },
    '🛠️': { icon: 'fi-rr-tools', color: '#94a3b8' },
    '🛠': { icon: 'fi-rr-tools', color: '#94a3b8' },
    '🔍': { icon: 'fi-rr-search', color: '#38bdf8' },
    '🔎': { icon: 'fi-rr-search', color: '#38bdf8' },
    '💬': { icon: 'fi-rr-comment-alt', color: '#0ea5e9' },
    '📨': { icon: 'fi-rr-envelope', color: '#38bdf8' },
    '✉️': { icon: 'fi-rr-envelope', color: '#38bdf8' },
    '🔒': { icon: 'fi-rr-lock', color: '#f59e0b' },
    '🔓': { icon: 'fi-rr-unlock', color: '#10b981' },
    '⏱️': { icon: 'fi-rr-time-fast', color: '#38bdf8' },
    '⏱': { icon: 'fi-rr-time-fast', color: '#38bdf8' },
    '⏰': { icon: 'fi-rr-alarm-clock', color: '#ef4444' },
    '⏳': { icon: 'fi-rr-hourglass', color: '#f59e0b' },
    '💾': { icon: 'fi-rr-disk', color: '#38bdf8' },
    '📥': { icon: 'fi-rr-inbox', color: '#38bdf8' },
    '🎯': { icon: 'fi-rr-bullseye', color: '#ef4444' },
    '🟢': { icon: 'fi-rr-circle', color: '#10b981' },
    '✅': { icon: 'fi-rr-check', color: '#10b981' },
    '✓': { icon: 'fi-rr-check', color: '#10b981' },
    '✔': { icon: 'fi-rr-check', color: '#10b981' },
    '🔴': { icon: 'fi-rr-circle', color: '#ef4444' },
    '❌': { icon: 'fi-rr-cross', color: '#ef4444' },
    '✕': { icon: 'fi-rr-cross', color: '#ef4444' },
    '✖': { icon: 'fi-rr-cross', color: '#ef4444' },
    '🟡': { icon: 'fi-rr-circle', color: '#fbbf24' },
    '⚪': { icon: 'fi-rr-snowflake', color: '#94a3b8' },
    '🎓': { icon: 'fi-rr-graduation-cap', color: '#8b5cf6' },
    '🏛️': { icon: 'fi-rr-building', color: '#6366f1' },
    '🏛': { icon: 'fi-rr-building', color: '#6366f1' },
    '🏢': { icon: 'fi-rr-building', color: '#3b82f6' },
    '🏠': { icon: 'fi-rr-home', color: '#10b981' },
    '💻': { icon: 'fi-rr-laptop', color: '#38bdf8' },
    '🖥️': { icon: 'fi-rr-screen', color: '#38bdf8' },
    '🖥': { icon: 'fi-rr-screen', color: '#38bdf8' },
    '⌨️': { icon: 'fi-rr-keyboard', color: '#94a3b8' },
    '🗑️': { icon: 'fi-rr-trash', color: '#ef4444' },
    '🗑': { icon: 'fi-rr-trash', color: '#ef4444' },
    '🔄': { icon: 'fi-rr-refresh', color: '#0ea5e9' },
    '🔁': { icon: 'fi-rr-refresh', color: '#0ea5e9' },
    '🎉': { icon: 'fi-rr-sparkles', color: '#f59e0b' },
    '🐙': { icon: 'fi-brands-github', color: '#ffffff' },
    '🏅': { icon: 'fi-rr-medal', color: '#fbbf24' },
    '🏁': { icon: 'fi-rr-flag', color: '#ef4444' },
    '👁️': { icon: 'fi-rr-eye', color: '#38bdf8' },
    '👁': { icon: 'fi-rr-eye', color: '#38bdf8' },
    '🔑': { icon: 'fi-rr-key', color: '#fbbf24' },
    '🤖': { icon: 'fi-rr-microchip', color: '#a855f7' },
    '⚠️': { icon: 'fi-rr-exclamation', color: '#f59e0b' }
  };

  const EMOJI_REGEX = new RegExp(
    Object.keys(EMOJI_TO_FLATICON).map(k => k.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')).join('|'),
    'gu'
  );

  const CPIcons = {
    /**
     * Resolves an icon name to a full Flaticon class.
     */
    resolveClass(name) {
      if (!name) return 'fi fi-rr-code-compare';
      const clean = name.toLowerCase().trim();
      if (clean.startsWith('fi-') || clean.startsWith('fi ')) {
        return clean.startsWith('fi ') ? clean : `fi ${clean}`;
      }
      const mapped = NAME_TO_FLATICON[clean] || `fi-rr-${clean}`;
      return `fi ${mapped}`;
    },

    /**
     * Returns an HTML string rendering the Flaticon vector icon.
     */
    get(name, options = {}) {
      const fiClass = this.resolveClass(name);
      const cls = options.className || '';
      const size = options.size;
      const color = options.color;

      let styleStr = '';
      if (size) {
        const sizeVal = typeof size === 'number' ? `${size}px` : size;
        styleStr += `font-size: ${sizeVal}; `;
      }
      if (color) {
        styleStr += `color: ${color}; `;
      }

      const styleAttr = styleStr ? `style="${styleStr.trim()}"` : '';
      return `<i class="${fiClass} ${cls}" ${styleAttr}></i>`;
    },

    /**
     * Transforms raw emojis in text nodes into Flaticon vector icons.
     */
    replaceEmojisInTree(node) {
      if (!node) return;
      const tag = (node.nodeName || '').toUpperCase();
      if (['SCRIPT', 'STYLE', 'TEXTAREA', 'CODE', 'PRE', 'SVG', 'NOSCRIPT', 'INPUT'].includes(tag)) return;

      if (node.nodeType === 3) { // TEXT_NODE
        const val = node.nodeValue;
        if (val && EMOJI_REGEX.test(val)) {
          EMOJI_REGEX.lastIndex = 0;
          const trimmed = val.trim();
          const isSoloEmoji = (trimmed.length <= 4) && (trimmed.replace(EMOJI_REGEX, '').length === 0);
          const span = document.createElement('span');
          span.className = isSoloEmoji ? 'cp-icon-wrap cp-single-icon' : 'cp-icon-wrap';
          span.innerHTML = val.replace(EMOJI_REGEX, match => {
            const conf = EMOJI_TO_FLATICON[match];
            if (!conf) return match;
            const colorStyle = conf.color ? `color:${conf.color};` : '';
            const cls = isSoloEmoji ? `fi ${conf.icon} cp-single-icon` : `fi ${conf.icon} cp-inline-icon`;
            return `<i class="${cls}" style="${colorStyle}"></i>`;
          });
          node.replaceWith(...span.childNodes);
        }
        return;
      }

      const children = Array.from(node.childNodes);
      for (let i = 0; i < children.length; i++) {
        CPIcons.replaceEmojisInTree(children[i]);
      }
    },

    /**
     * Enhances DOM elements with Flaticon vector icons:
     * - Replaces <cp-icon> custom elements
     * - Auto-attaches icons to navbar links
     * - Converts plain emojis to vector icons
     */
    enhance(root = document) {
      const elements = selector => [
        ...(root.matches && root.matches(selector) ? [root] : []),
        ...root.querySelectorAll(selector)
      ];
      // 1. Ensure Flaticon CSS is loaded in document head
      if (!document.querySelector('link[href*="uicons"], link[href*="flaticon"], link[href="/frontend/css/global/icons.css"]')) {
        const uiconsLink = document.createElement('link');
        uiconsLink.rel = 'stylesheet';
        uiconsLink.href = 'https://cdn-uicons.flaticon.com/2.6.0/uicons-regular-rounded/css/uicons-regular-rounded.css';
        document.head.appendChild(uiconsLink);
      }

      // 2. Ensure Favicon is set
      if (!document.querySelector('link[rel="icon"]')) {
        const link = document.createElement('link');
        link.rel = 'icon';
        link.type = 'image/svg+xml';
        link.href = '/frontend/assets/icons/favicon.svg';
        document.head.appendChild(link);
      }

      // 3. Replace <cp-icon name="..."> elements with Flaticon <i> tags
      elements('cp-icon').forEach(el => {
        const name = el.getAttribute('name');
        const size = el.getAttribute('size');
        const color = el.getAttribute('color');
        const cls = el.getAttribute('class') || '';
        el.outerHTML = CPIcons.get(name, { size, color, className: cls });
      });

      // 4. Enhance .nav-links automatically
      elements('.nav-links a').forEach(a => {
        if (a.querySelector('i.fi, .cp-icon')) return;
        const text = (a.textContent || '').trim().toLowerCase();
        let icon = null;
        if (text.includes('trang chủ') || text.includes('home')) icon = 'home';
        else if (text.includes('bài tập') || text.includes('problem')) icon = 'code';
        else if (text.includes('cuộc thi') || text.includes('contest')) icon = 'trophy';
        else if (text.includes('xếp hạng') || text.includes('rank')) icon = 'award';
        else if (text.includes('tổ chức') || text.includes('organization')) icon = 'shield';
        else if (text.includes('bài nộp') || text.includes('submission')) icon = 'send';
        else if (text.includes('wiki') || text.includes('tài liệu') || text.includes('learning')) icon = 'book';
        else if (text.includes('cộng đồng') || text.includes('community')) icon = 'users';
        else if (text.includes('thành viên') || text.includes('user')) icon = 'user';
        else if (text.includes('quản trị') || text.includes('admin')) icon = 'shield';

        if (icon) {
          const iconHtml = CPIcons.get(icon, { size: '1rem' });
          const existingText = a.textContent.trim();
          a.style.display = 'inline-flex';
          a.style.alignItems = 'center';
          a.style.gap = '0.45rem';
          a.innerHTML = `${iconHtml}<span>${existingText}</span>`;
        }
      });

      // 5. Enhance search inputs containing emoji 🔍/🔎 in placeholder with vector icon
      elements('input[placeholder*="🔍"], input[placeholder*="🔎"]').forEach(inp => {
        inp.placeholder = inp.placeholder.replace(/[🔍🔎]\s*/g, '').trim();
        inp.classList.add('input-with-search-icon');
      });

      // 6. Replace all raw emojis in body text nodes with Flaticon vector icons
      const targetBody = root.body || (root === document ? document.body : root);
      if (targetBody) {
        CPIcons.replaceEmojisInTree(targetBody);
      }

      // Brand icons are rare; load their font only on pages that use one.
      if (document.querySelector('[class*="fi-brands-"]') && !document.querySelector('link[data-cp-brand-icons]')) {
        const brands = document.createElement('link');
        brands.rel = 'stylesheet';
        brands.href = 'https://cdn-uicons.flaticon.com/2.6.0/uicons-brands/css/uicons-brands.css';
        brands.dataset.cpBrandIcons = 'true';
        document.head.appendChild(brands);
      }
    },

    renderAll() {
      this.enhance();
    }
  };

  // Define Web Component <cp-icon>
  if (typeof customElements !== 'undefined' && !customElements.get('cp-icon')) {
    customElements.define('cp-icon', class extends HTMLElement {
      connectedCallback() {
        const name = this.getAttribute('name');
        const size = this.getAttribute('size');
        const color = this.getAttribute('color');
        const cls = this.getAttribute('class') || '';
        this.outerHTML = CPIcons.get(name, { size, color, className: cls });
      }
    });
  }

  // Expose globally
  window.CPIcons = CPIcons;
  window.Icons = CPIcons;

  // Auto-run on DOM ready and observe mutations
  function setup() {
    CPIcons.enhance();
    if (typeof MutationObserver !== 'undefined' && document.body) {
      let timeout;
      const pending = new Set();
      const observer = new MutationObserver(records => {
        for (const record of records) {
          for (const node of record.addedNodes) pending.add(node);
        }
        clearTimeout(timeout);
        timeout = setTimeout(() => {
          for (const node of pending) {
            if (node.nodeType === 1 && node.isConnected) CPIcons.enhance(node);
            else if (node.nodeType === 3 && node.isConnected) CPIcons.replaceEmojisInTree(node);
          }
          pending.clear();
        }, 60);
      });
      observer.observe(document.body, { childList: true, subtree: true });
    }
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', setup);
  } else {
    setup();
  }
})();
