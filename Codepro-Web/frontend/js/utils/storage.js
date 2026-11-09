/**
 * CodeProOJ - Universal Storage Utilities
 */
const StorageUtils = {
  set(key, value) {
    try {
      localStorage.setItem(key, JSON.stringify(value));
      return true;
    } catch (e) {
      console.error('Storage set error:', e);
      return false;
    }
  },

  get(key, defaultValue = null) {
    try {
      const item = localStorage.getItem(key);
      if (item === null) return defaultValue;
      return JSON.parse(item);
    } catch (e) {
      return localStorage.getItem(key) || defaultValue;
    }
  },

  remove(key) {
    try {
      localStorage.removeItem(key);
      return true;
    } catch (e) {
      return false;
    }
  },

  clear() {
    try {
      localStorage.clear();
      return true;
    } catch (e) {
      return false;
    }
  }
};

window.StorageUtils = StorageUtils;
