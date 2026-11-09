/**
 * CodeProOJ - Toast Notification System
 */
const Notification = {
  container: null,

  init() {
    if (!this.container) {
      let box = document.getElementById('toastNotificationContainer');
      if (!box) {
        box = document.createElement('div');
        box.id = 'toastNotificationContainer';
        box.style.cssText = 'position:fixed;top:20px;right:20px;z-index:9999;display:flex;flex-direction:column;gap:10px;pointer-events:none;';
        document.body.appendChild(box);
      }
      this.container = box;
    }
  },

  show(message, type = 'info', duration = 3500) {
    this.init();
    const colors = {
      success: { bg: '#065f46', border: '#10b981', text: '#34d399', icon: '✅' },
      error: { bg: '#7f1d1d', border: '#ef4444', text: '#f87171', icon: '❌' },
      warning: { bg: '#78350f', border: '#f59e0b', text: '#fbbf24', icon: '⚠️' },
      info: { bg: '#1e3a8a', border: '#3b82f6', text: '#93c5fd', icon: 'ℹ️' }
    };
    const c = colors[type] || colors.info;

    const toast = document.createElement('div');
    toast.style.cssText = `background:${c.bg};border:1px solid ${c.border};color:#fff;padding:0.85rem 1.25rem;border-radius:10px;font-size:0.9rem;font-weight:600;display:flex;align-items:center;gap:0.75rem;box-shadow:0 10px 25px rgba(0,0,0,0.4);pointer-events:auto;animation:toastIn 0.25s ease;`;
    const icon = document.createElement('span');
    icon.textContent = c.icon;
    const content = document.createElement('span');
    content.textContent = String(message);
    toast.append(icon, content);

    this.container.appendChild(toast);

    setTimeout(() => {
      toast.style.opacity = '0';
      toast.style.transform = 'translateY(-10px)';
      toast.style.transition = 'all 0.25s ease';
      setTimeout(() => toast.remove(), 250);
    }, duration);
  },

  success(msg, dur) { this.show(msg, 'success', dur); },
  error(msg, dur) { this.show(msg, 'error', dur); },
  warning(msg, dur) { this.show(msg, 'warning', dur); },
  info(msg, dur) { this.show(msg, 'info', dur); }
};

window.Toast = Notification;
window.Notification = Notification;
