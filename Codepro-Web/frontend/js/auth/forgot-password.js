/**
 * frontend/js/auth/forgot-password.js
 * Initiates password recovery flow.
 */

document.addEventListener('DOMContentLoaded', () => {
  const form = document.getElementById('forgotForm');
  const submitBtn = document.getElementById('forgotSubmitBtn');

  if (form) {
    form.addEventListener('submit', async (e) => {
      e.preventDefault();
      Auth.hideAlert('authAlert');

      const identifier = document.getElementById('identifier').value.trim();
      if (!identifier) {
        Auth.showAlert('authAlert', 'Vui lòng nhập tên đăng nhập hoặc email.', 'error');
        return;
      }

      if (submitBtn) {
        submitBtn.disabled = true;
        submitBtn.innerHTML = '<span>Đang gửi yêu cầu...</span>';
      }

      try {
        const res = await fetch('/api/v1/auth/forgot-password', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ username_or_email: identifier })
        });

        const data = await res.json();
        Auth.showAlert(
          'authAlert',
          data.message || 'Nếu tài khoản khớp với hệ thống, chúng tôi đã gửi email hướng dẫn.',
          'success'
        );

        if (submitBtn) {
          submitBtn.disabled = false;
          submitBtn.innerHTML = '<span>Gửi lại yêu cầu</span>';
        }
      } catch {
        Auth.showAlert('authAlert', 'Lỗi kết nối máy chủ.', 'error');
        if (submitBtn) {
          submitBtn.disabled = false;
          submitBtn.innerHTML = '<span>Gửi hướng dẫn</span>';
        }
      }
    });
  }
});
