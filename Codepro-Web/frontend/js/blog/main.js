/**
 * CodeProOJ - Blog Main Controller
 */
document.addEventListener('DOMContentLoaded', () => {
  if (typeof BlogService !== 'undefined' && typeof loadBlogs === 'function') {
    loadBlogs();
  }
});
