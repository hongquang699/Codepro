/**
 * TimeMemory Component
 * Formats time (ms/s) and memory (KB/MB) cleanly.
 */
const TimeMemory = {
  formatTime(ms) {
    if (ms === undefined || ms === null) return '-';
    if (ms < 1000) return `${ms} ms`;
    return `${(ms / 1000).toFixed(2)} s`;
  },

  formatMemory(kb) {
    if (kb === undefined || kb === null) return '-';
    if (kb < 1024) return `${kb} KB`;
    return `${(kb / 1024).toFixed(1)} MB`;
  }
};

if (typeof window !== 'undefined') {
  window.TimeMemory = TimeMemory;
}
