/**
 * frontend/js/auth/register.js
 * Handles User Registration, frontend validation, and OTP flow transition.
 */

document.addEventListener('DOMContentLoaded', () => {
  const form = document.getElementById('registerForm');
  const submitBtn = document.getElementById('registerSubmitBtn');
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

  function clearErrors() {
    Auth.hideAlert('authAlert');
    document.querySelectorAll('.auth-field-error').forEach(el => {
      el.textContent = '';
      el.classList.remove('active');
    });
  }

  function showFieldError(fieldId, errorMsg) {
    const errEl = document.getElementById(`${fieldId}Error`);
    if (errEl) {
      errEl.textContent = errorMsg;
      errEl.classList.add('active');
    }
  }

  if (form) {
    form.addEventListener('submit', async (e) => {
      e.preventDefault();
      clearErrors();

      const username = document.getElementById('username').value.trim();
      const email = document.getElementById('email').value.trim();
      const password = document.getElementById('password').value;
      const passwordConfirm = document.getElementById('passwordConfirm').value;
      const termsAgreed = document.getElementById('termsAgreed') ? document.getElementById('termsAgreed').checked : true;

      let hasLocalError = false;

      if (!username || username.length < 3) {
        showFieldError('username', 'Tên đăng nhập phải có từ 3 ký tự trở lên.');
        hasLocalError = true;
      }

      if (!email || !email.includes('@')) {
        showFieldError('email', 'Vui lòng nhập địa chỉ email hợp lệ.');
        hasLocalError = true;
      }

      if (!password || password.length < 8) {
        showFieldError('password', 'Mật khẩu phải chứa ít nhất 8 ký tự.');
        hasLocalError = true;
      }

      if (password !== passwordConfirm) {
        showFieldError('passwordConfirm', 'Mật khẩu xác nhận không khớp.');
        hasLocalError = true;
      }

      if (!termsAgreed) {
        Auth.showAlert('authAlert', 'Bạn cần đồng ý với điều khoản sử dụng để tiếp tục.', 'error');
        hasLocalError = true;
      }

      if (hasLocalError) return;

      if (submitBtn) {
        submitBtn.disabled = true;
        submitBtn.innerHTML = '<span>Đang gửi mã xác thực...</span>';
      }

      try {
        const response = await fetch('/api/v1/auth/register', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'Accept': 'application/json'
          },
          body: JSON.stringify({
            username,
            email,
            password,
            password_confirm: passwordConfirm,
            terms_agreed: termsAgreed
          })
        });

        const data = await response.json();

        if (!response.ok || !data.success) {
          if (data.errors) {
            Object.entries(data.errors).forEach(([field, msg]) => {
              showFieldError(field, msg);
            });
          }
          Auth.showAlert('authAlert', data.message || 'Đăng ký không thành công.', 'error');
          if (submitBtn) {
            submitBtn.disabled = false;
            submitBtn.innerHTML = '<span>Đăng ký</span>';
          }
          return;
        }

        // Registration initiated! Store email and redirect to OTP verification
        sessionStorage.setItem('pending_verification_email', email);
        sessionStorage.setItem('registered_username', username);

        Auth.showAlert('authAlert', 'Mã xác thực đã được gửi! Đang chuyển hướng...', 'success');
        setTimeout(() => {
          window.location.href = `/verify-email?email=${encodeURIComponent(email)}`;
        }, 800);

      } catch (err) {
        console.error('Register error:', err);
        Auth.showAlert('authAlert', 'Lỗi kết nối máy chủ. Vui lòng thử lại sau.', 'error');
        if (submitBtn) {
          submitBtn.disabled = false;
          submitBtn.innerHTML = '<span>Đăng ký</span>';
        }
      }
    });
  }
});
