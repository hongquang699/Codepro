/**
 * CodeProOJ - Universal Formatting Utilities
 */
const FormatUtils = {
  /**
   * Format relative time (e.g., '5 phút trước', '2 giờ trước')
   */
  timeAgo(dateStr) {
    if (!dateStr) return '—';
    const date = new Date(dateStr);
    const now = new Date();
    const diffSec = Math.floor((now - date) / 1000);

    if (diffSec < 60) return `${Math.max(1, diffSec)} giây trước`;
    const diffMin = Math.floor(diffSec / 60);
    if (diffMin < 60) return `${diffMin} phút trước`;
    const diffHours = Math.floor(diffMin / 60);
    if (diffHours < 24) return `${diffHours} giờ trước`;
    const diffDays = Math.floor(diffHours / 24);
    if (diffDays < 30) return `${diffDays} ngày trước`;
    return date.toLocaleDateString('vi-VN');
  },

  /**
   * Format seconds duration to HH:MM:SS
   */
  formatDuration(seconds) {
    if (seconds == null || isNaN(seconds)) return '00:00:00';
    const s = Math.max(0, Math.floor(seconds));
    const hrs = Math.floor(s / 3600).toString().padStart(2, '0');
    const mins = Math.floor((s % 3600) / 60).toString().padStart(2, '0');
    const secs = (s % 60).toString().padStart(2, '0');
    return `${hrs}:${mins}:${secs}`;
  },

  /**
   * Format memory bytes / KB to readable MB
   */
  formatMemory(kb) {
    if (kb == null) return '—';
    if (kb < 1024) return `${kb} KB`;
    return `${(kb / 1024).toFixed(1)} MB`;
  },

  /**
   * Format execution time
   */
  formatTime(sec) {
    if (sec == null) return '—';
    return `${parseFloat(sec).toFixed(3)}s`;
  },

  /**
   * Format verdict badge HTML
   */
  verdictBadge(verdict) {
    const v = (verdict || '').toUpperCase();
    const map = {
      'AC': { label: 'Accepted', class: 'bv-AC' },
      'WA': { label: 'Wrong Answer', class: 'bv-WA' },
      'TLE': { label: 'Time Limit Exceeded', class: 'bv-other' },
      'MLE': { label: 'Memory Limit Exceeded', class: 'bv-other' },
      'RTE': { label: 'Runtime Error', class: 'bv-other' },
      'CE': { label: 'Compilation Error', class: 'bv-other' },
      'QU': { label: 'Queued', class: 'bv-other' },
      'P': { label: 'Judging', class: 'bv-other' },
    };
    const item = map[v] || { label: v || 'Unknown', class: 'bv-other' };
    return `<span class="badge-v ${item.class}">${v}</span>`;
  },

  /**
   * Escape HTML to prevent XSS
   */
  escapeHtml(str) {
    if (!str) return '';
    return String(str)
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;')
      .replace(/'/g, '&#39;');
  }
};

window.FormatUtils = FormatUtils;
