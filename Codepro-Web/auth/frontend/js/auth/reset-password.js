/**
 * frontend/js/auth/reset-password.js
 * Validates reset token and sets new password.
 */

document.addEventListener('DOMContentLoaded', async () => {
  const form = document.getElementById('resetForm');
  const submitBtn = document.getElementById('resetSubmitBtn');
  const togglePassBtn = document.getElementById('togglePasswordBtn');
  const toggleConfirmBtn = document.getElementById('toggleConfirmPasswordBtn');

  if (togglePassBtn) {
    togglePassBtn.addEventListener('click', () => {
      Auth.togglePassword('password', togglePassBtn);
    });
  }
  if (toggleConfirmBtn) {
    toggleConfirmBtn.addEventListener('click', () => {
      Auth.togglePassword('passwordConfirm', toggleConfirmBtn);
    });
  }

  const urlParams = new URLSearchParams(window.location.search);
  const token = urlParams.get('token');

  if (!token) {
    Auth.showAlert('authAlert', 'Liên kết không hợp lệ hoặc thiếu mã xác thực.', 'error');
    if (submitBtn) submitBtn.disabled = true;
    return;
  }

  // Validate token via API
  try {
    const res = await fetch(`/api/v1/auth/reset-password/validate?token=${encodeURIComponent(token)}`);
    const data = await res.json();
    if (!res.ok || !data.valid) {
      Auth.showAlert('authAlert', data.message || 'Liên kết đặt lại mật khẩu đã hết hạn hoặc không hợp lệ.', 'error');
      if (submitBtn) submitBtn.disabled = true;
    }
  } catch {
    // Fail silently in case of temporary network glitch
  }

  if (form) {
    form.addEventListener('submit', async (e) => {
      e.preventDefault();
      Auth.hideAlert('authAlert');

      const password = document.getElementById('password').value;
      const passwordConfirm = document.getElementById('passwordConfirm').value;

      if (!password || password.length < 8) {
        Auth.showAlert('authAlert', 'Mật khẩu mới phải có ít nhất 8 ký tự.', 'error');
        return;
      }

      if (password !== passwordConfirm) {
        Auth.showAlert('authAlert', 'Mật khẩu xác nhận không khớp.', 'error');
        return;
      }

      if (submitBtn) {
        submitBtn.disabled = true;
        submitBtn.innerHTML = '<span>Đang cập nhật mật khẩu...</span>';
      }

      try {
        const response = await fetch('/api/v1/auth/reset-password', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            token,
            password,
            password_confirm: passwordConfirm
          })
        });

        const data = await response.json();

        if (!response.ok || !data.success) {
          Auth.showAlert('authAlert', data.message || 'Không thể đặt lại mật khẩu.', 'error');
          if (submitBtn) {
            submitBtn.disabled = false;
            submitBtn.innerHTML = '<span>Lưu mật khẩu mới</span>';
          }
          return;
        }

        Auth.showAlert('authAlert', 'Mật khẩu đã được cập nhật thành công! Đang chuyển đến trang đăng nhập...', 'success');
        setTimeout(() => {
          window.location.href = '/login';
        }, 1200);

      } catch (err) {
        Auth.showAlert('authAlert', 'Lỗi kết nối máy chủ.', 'error');
        if (submitBtn) {
          submitBtn.disabled = false;
          submitBtn.innerHTML = '<span>Lưu mật khẩu mới</span>';
        }
      }
    });
  }
});
