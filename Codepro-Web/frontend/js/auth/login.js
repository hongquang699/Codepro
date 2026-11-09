/**
 * frontend/js/auth/login.js
 * Handles Login interaction, 2FA challenge redirection, and error handling.
 */

document.addEventListener('DOMContentLoaded', () => {
  const form = document.getElementById('loginForm');
  const alertBox = document.getElementById('authAlert');
  const submitBtn = document.getElementById('loginSubmitBtn');
  const togglePassBtn = document.getElementById('togglePasswordBtn');

  if (togglePassBtn) {
    togglePassBtn.addEventListener('click', () => {
      Auth.togglePassword('password', togglePassBtn);
    });
  }

  // Pre-fill username from query param or previous register if any
  const urlParams = new URLSearchParams(window.location.search);
  const userParam = urlParams.get('username') || sessionStorage.getItem('registered_username');
  if (userParam) {
    const userInput = document.getElementById('username');
    if (userInput) userInput.value = userParam;
  }

  if (form) {
    form.addEventListener('submit', async (e) => {
      e.preventDefault();
      Auth.hideAlert('authAlert');

      const username = document.getElementById('username').value.trim();
      const password = document.getElementById('password').value;
      const rememberMe = document.getElementById('rememberMe') ? document.getElementById('rememberMe').checked : false;

      if (!username || !password) {
        Auth.showAlert('authAlert', 'Vui lòng nhập đầy đủ thông tin tài khoản và mật khẩu.', 'error');
        return;
      }

      if (submitBtn) {
        submitBtn.disabled = true;
        submitBtn.innerHTML = '<span>Đang xác thực...</span>';
      }

      try {
        const response = await fetch('/api/v1/auth/login', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'Accept': 'application/json'
          },
          credentials: 'include',
          body: JSON.stringify({
            username,
            password,
            remember_me: rememberMe
          })
        });

        // A server error may return an HTML traceback while DEBUG is enabled.
        // Never display an unexpected response body on the login page.
        let data;
        try {
          data = await response.json();
        } catch (_) {
          data = null;
        }

        if (!response.ok || !data?.success) {
          const knownError = (response.status === 401 && data?.error_code === 'INVALID_CREDENTIALS') ||
            (response.status === 403 && data?.error_code === 'ADMIN_IP_RESTRICTED');
          const message = knownError && typeof data?.message === 'string'
            ? data.message
            : 'Không thể đăng nhập lúc này. Vui lòng thử lại sau.';
          Auth.showAlert('authAlert', message, 'error');
          if (submitBtn) {
            submitBtn.disabled = false;
            submitBtn.innerHTML = '<span>Đăng nhập</span>';
          }
          return;
        }

        // Check if 2FA is required
        if (data.requires_2fa) {
          const redirect = encodeURIComponent(Auth.getRedirectUrl());
          window.location.href = `/two-factor?user_id=${data.user_id}&username=${encodeURIComponent(data.username)}&next=${redirect}`;
          return;
        }

        // Authenticated successfully
        if (data.user) {
          localStorage.setItem('user', JSON.stringify(data.user));
          localStorage.setItem('username', data.user.username);
          const isUserAdmin = Boolean(data.user.is_admin || data.user.role === 'admin' || data.user.is_staff || data.user.is_superuser);
          localStorage.setItem('role', isUserAdmin ? 'admin' : (data.user.role || 'user'));

          if (isUserAdmin) {
            document.cookie = 'role=admin; path=/; max-age=86400; SameSite=Lax';
            document.cookie = 'is_admin=true; path=/; max-age=86400; SameSite=Lax';
          } else {
            document.cookie = 'role=user; path=/; max-age=86400; SameSite=Lax';
            document.cookie = 'is_admin=; path=/; max-age=0; expires=Thu, 01 Jan 1970 00:00:00 GMT';
            document.cookie = 'admin_token=; path=/; max-age=0; expires=Thu, 01 Jan 1970 00:00:00 GMT';
          }
        }
        if (data.token) {
          localStorage.setItem('token', data.token);
        } else if (data.session_token) {
          localStorage.setItem('token', data.session_token);
        }

        Auth.showAlert('authAlert', 'Đăng nhập thành công! Đang chuyển hướng...', 'success');
        setTimeout(() => {
          window.location.href = Auth.getRedirectUrl();
        }, 500);

      } catch (err) {
        console.error('Login error:', err);
        Auth.showAlert('authAlert', 'Không thể kết nối đến máy chủ. Vui lòng thử lại sau.', 'error');
        if (submitBtn) {
          submitBtn.disabled = false;
          submitBtn.innerHTML = '<span>Đăng nhập</span>';
        }
      }
    });
  }
});
