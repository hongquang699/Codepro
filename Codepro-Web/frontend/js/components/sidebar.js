/**
 * CodeProOJ - Sidebar Navigation Component
 */
const Sidebar = {
  toggle() {
    const el = document.querySelector('.admin-sidebar, .comm-left-sidebar, .sidebar');
    if (el) {
      el.classList.toggle('active');
    }
  },

  highlightCurrent() {
    const path = window.location.pathname;
    document.querySelectorAll('.admin-nav-item, .comm-nav-link').forEach(link => {
      const href = link.getAttribute('href');
      if (href && (href === path || path.startsWith(href))) {
        link.classList.add('active');
      }
    });
  }
};

document.addEventListener('DOMContentLoaded', () => {
  Sidebar.highlightCurrent();
});

window.Sidebar = Sidebar;
