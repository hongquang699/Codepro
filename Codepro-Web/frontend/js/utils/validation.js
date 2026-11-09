/**
 * CodeProOJ - Universal Validation Utilities
 */
const ValidationUtils = {
  isValidUsername(username) {
    if (!username || typeof username !== 'string') return false;
    return /^[a-zA-Z0-9_-]{3,30}$/.test(username);
  },

  isValidEmail(email) {
    if (!email || typeof email !== 'string') return false;
    return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email);
  },

  isValidPassword(password) {
    if (!password || typeof password !== 'string') return false;
    return password.length >= 6;
  },

  isValidProblemCode(code) {
    if (!code || typeof code !== 'string') return false;
    return /^[A-Z0-9_-]{2,20}$/.test(code.toUpperCase());
  },

  sanitizeInput(str) {
    if (!str) return '';
    return str.trim();
  }
};

window.ValidationUtils = ValidationUtils;
