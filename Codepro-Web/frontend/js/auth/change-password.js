/**
 * frontend/js/auth/change-password.js
 * Updates password for logged-in user.
 */

document.addEventListener('DOMContentLoaded', () => {
  const form = document.getElementById('changePasswordForm');
  const submitBtn = document.getElementById('changeSubmitBtn');

  if (form) {
    form.addEventListener('submit', async (e) => {
      e.preventDefault();
      Auth.hideAlert('authAlert');

      const currentPassword = document.getElementById('currentPassword').value;
      const newPassword = document.getElementById('newPassword').value;
      const newPasswordConfirm = document.getElementById('newPasswordConfirm').value;

      if (!currentPassword || !newPassword) {
        Auth.showAlert('authAlert', 'Vui lòng điền đầy đủ các trường mật khẩu.', 'error');
        return;
      }

      if (newPassword.length < 8) {
        Auth.showAlert('authAlert', 'Mật khẩu mới phải có ít nhất 8 ký tự.', 'error');
        return;
      }

      if (newPassword !== newPasswordConfirm) {
        Auth.showAlert('authAlert', 'Mật khẩu xác nhận không trùng khớp.', 'error');
        return;
      }

      if (submitBtn) {
        submitBtn.disabled = true;
        submitBtn.innerHTML = '<span>Đang cập nhật...</span>';
      }

      try {
        const csrfToken = await Auth.getCsrfToken();
        const res = await fetch('/api/v1/auth/change-password', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json', 'X-CSRFToken': csrfToken },
          credentials: 'include',
          body: JSON.stringify({
            current_password: currentPassword,
            new_password: newPassword,
            new_password_confirm: newPasswordConfirm
          })
        });

        const data = await res.json();

        if (!res.ok || !data.success) {
          Auth.showAlert('authAlert', data.message || 'Đổi mật khẩu thất bại.', 'error');
          if (submitBtn) {
            submitBtn.disabled = false;
            submitBtn.innerHTML = '<span>Cập nhật mật khẩu</span>';
          }
          return;
        }

        Auth.showAlert('authAlert', 'Đổi mật khẩu thành công!', 'success');
        form.reset();
        if (submitBtn) {
          submitBtn.disabled = false;
          submitBtn.innerHTML = '<span>Cập nhật mật khẩu</span>';
        }

      } catch {
        Auth.showAlert('authAlert', 'Lỗi kết nối máy chủ.', 'error');
        if (submitBtn) {
          submitBtn.disabled = false;
          submitBtn.innerHTML = '<span>Cập nhật mật khẩu</span>';
        }
      }
    });
  }
});
