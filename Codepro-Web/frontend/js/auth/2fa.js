/**
 * frontend/js/auth/2fa.js
 * Handles Two-Factor verification challenge during login or setup in settings.
 */

document.addEventListener('DOMContentLoaded', () => {
  const form = document.getElementById('twoFactorForm');
  const submitBtn = document.getElementById('twoFactorSubmitBtn');

  const urlParams = new URLSearchParams(window.location.search);
  const userId = urlParams.get('user_id');
  const username = urlParams.get('username');

  const displayUser = document.getElementById('displayUser');
  if (displayUser && username) {
    displayUser.textContent = username;
  }

  if (form) {
    form.addEventListener('submit', async (e) => {
      e.preventDefault();
      Auth.hideAlert('authAlert');

      const code = document.getElementById('twoFactorCode').value.trim();
      if (!code) {
        Auth.showAlert('authAlert', 'Vui lòng nhập mã xác thực từ ứng dụng Authenticator.', 'error');
        return;
      }

      if (submitBtn) {
        submitBtn.disabled = true;
        submitBtn.innerHTML = '<span>Đang xác nhận...</span>';
      }

      try {
        const res = await fetch('/api/v1/auth/2fa/verify-login', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'Accept': 'application/json'
          },
          credentials: 'include',
          body: JSON.stringify({
            user_id: userId,
            code: code
          })
        });

        const data = await res.json();

        if (!res.ok || !data.success) {
          Auth.showAlert('authAlert', data.message || 'Mã xác thực không hợp lệ.', 'error');
          if (submitBtn) {
            submitBtn.disabled = false;
            submitBtn.innerHTML = '<span>Xác nhận</span>';
          }
          return;
        }

        if (data.user) {
          localStorage.setItem('user', JSON.stringify(data.user));
        }

        Auth.showAlert('authAlert', 'Đăng nhập thành công! Đang chuyển hướng...', 'success');
        setTimeout(() => {
          window.location.href = Auth.getRedirectUrl();
        }, 800);

      } catch {
        Auth.showAlert('authAlert', 'Lỗi kết nối máy chủ.', 'error');
        if (submitBtn) {
          submitBtn.disabled = false;
          submitBtn.innerHTML = '<span>Xác nhận</span>';
        }
      }
    });
  }
});
