/**
 * CodeProOJ - Universal Modal Controller
 */
const Modal = {
  show(modalId) {
    const el = typeof modalId === 'string' ? document.getElementById(modalId) : modalId;
    if (el) {
      el.style.display = 'flex';
      document.body.style.overflow = 'hidden';
    }
  },

  close(modalId) {
    const el = typeof modalId === 'string' ? document.getElementById(modalId) : modalId;
    if (el) {
      el.style.display = 'none';
      document.body.style.overflow = '';
    }
  },

  closeAll() {
    document.querySelectorAll('.modal-overlay').forEach(el => {
      el.style.display = 'none';
    });
    document.body.style.overflow = '';
  }
};

// Close on backdrop click or ESC
document.addEventListener('keydown', (e) => {
  if (e.key === 'Escape') Modal.closeAll();
});

window.Modal = Modal;
