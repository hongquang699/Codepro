/**
 * frontend/js/auth/verify-email.js
 * 6-Digit OTP verification with auto-focus jumping, paste support, and 60s countdown.
 */

document.addEventListener('DOMContentLoaded', () => {
  const form = document.getElementById('verifyForm');
  const otpBoxes = Array.from(document.querySelectorAll('.otp-box'));
  const resendBtn = document.getElementById('resendOtpBtn');
  const timerSpan = document.getElementById('countdownSpan');
  const displayEmail = document.getElementById('displayEmail');
  const submitBtn = document.getElementById('verifySubmitBtn');

  // Retrieve email from URL or sessionStorage
  const urlParams = new URLSearchParams(window.location.search);
  const email = urlParams.get('email') || sessionStorage.getItem('pending_verification_email') || '';

  if (displayEmail) {
    displayEmail.textContent = email || 'email của bạn';
  }

  // 1. Focus first box automatically
  if (otpBoxes.length > 0) {
    otpBoxes[0].focus();
  }

  // 2. Handle OTP Box Keyboard Navigation
  otpBoxes.forEach((box, index) => {
    box.addEventListener('input', (e) => {
      const val = e.target.value;

      // Ensure single digit
      if (val.length > 1) {
        box.value = val.slice(-1);
      }

      if (box.value) {
        box.classList.add('filled');
        // Advance to next box
        if (index < otpBoxes.length - 1) {
          otpBoxes[index + 1].focus();
        }
      } else {
        box.classList.remove('filled');
      }

      // Check if all 6 boxes are filled -> optional auto-submit
      const fullOtp = getEnteredOtp();
      if (fullOtp.length === 6) {
        // Can optionally auto submit
      }
    });

    box.addEventListener('keydown', (e) => {
      if (e.key === 'Backspace') {
        if (!box.value && index > 0) {
          otpBoxes[index - 1].focus();
          otpBoxes[index - 1].value = '';
          otpBoxes[index - 1].classList.remove('filled');
        } else {
          box.value = '';
          box.classList.remove('filled');
        }
      } else if (e.key === 'ArrowLeft' && index > 0) {
        otpBoxes[index - 1].focus();
      } else if (e.key === 'ArrowRight' && index < otpBoxes.length - 1) {
        otpBoxes[index + 1].focus();
      }
    });

    // 3. Paste Event Handler
    box.addEventListener('paste', (e) => {
      e.preventDefault();
      const pasteData = (e.clipboardData || window.clipboardData).getData('text').trim();
      const digits = pasteData.replace(/\D/g, '').slice(0, 6);

      if (!digits) return;

      digits.split('').forEach((digit, i) => {
        if (otpBoxes[i]) {
          otpBoxes[i].value = digit;
          otpBoxes[i].classList.add('filled');
        }
      });

      const nextFocus = Math.min(digits.length, otpBoxes.length - 1);
      otpBoxes[nextFocus].focus();
    });
  });

  function getEnteredOtp() {
    return otpBoxes.map(b => b.value.trim()).join('');
  }

  // 4. Countdown Timer for Resend
  let countdown = 60;
  let timerInterval = null;

  function startCountdown(seconds = 60) {
    countdown = seconds;
    if (resendBtn) resendBtn.disabled = true;
    if (timerSpan) timerSpan.textContent = `(${countdown}s)`;

    if (timerInterval) clearInterval(timerInterval);

    timerInterval = setInterval(() => {
      countdown--;
      if (timerSpan) timerSpan.textContent = `(${countdown}s)`;
      if (countdown <= 0) {
        clearInterval(timerInterval);
        if (resendBtn) resendBtn.disabled = false;
        if (timerSpan) timerSpan.textContent = '';
      }
    }, 1000);
  }

  startCountdown(60);

  // 5. Resend OTP Handler
  if (resendBtn) {
    resendBtn.addEventListener('click', async () => {
      if (!email) {
        Auth.showAlert('authAlert', 'Không tìm thấy địa chỉ email. Vui lòng quay lại trang đăng ký.', 'error');
        return;
      }

      Auth.hideAlert('authAlert');
      resendBtn.disabled = true;

      try {
        const res = await fetch('/api/v1/auth/resend-verification', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ email })
        });
        const data = await res.json();

        if (!res.ok || !data.success) {
          Auth.showAlert('authAlert', data.message || 'Chưa thể gửi lại mã.', 'error');
          startCountdown(data.wait_seconds || 15);
        } else {
          Auth.showAlert('authAlert', 'Đã gửi lại mã xác nhận mới đến email của bạn!', 'success');
          startCountdown(data.wait_seconds || 60);
          otpBoxes.forEach(b => { b.value = ''; b.classList.remove('filled'); });
          otpBoxes[0].focus();
        }
      } catch (e) {
        Auth.showAlert('authAlert', 'Lỗi kết nối khi gửi lại mã.', 'error');
        startCountdown(15);
      }
    });
  }

  // 6. Submit OTP Verification
  if (form) {
    form.addEventListener('submit', async (e) => {
      e.preventDefault();
      Auth.hideAlert('authAlert');

      const otp = getEnteredOtp();
      if (otp.length < 6) {
        Auth.showAlert('authAlert', 'Vui lòng nhập đủ 6 chữ số mã OTP.', 'error');
        return;
      }

      if (!email) {
        Auth.showAlert('authAlert', 'Không tìm thấy thông tin email. Vui lòng đăng ký lại.', 'error');
        return;
      }

      if (submitBtn) {
        submitBtn.disabled = true;
        submitBtn.innerHTML = '<span>Đang xác thực...</span>';
      }

      try {
        const response = await fetch('/api/v1/auth/verify-email', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'Accept': 'application/json'
          },
          credentials: 'include',
          body: JSON.stringify({ email, otp })
        });

        const data = await response.json();

        if (!response.ok || !data.success) {
          Auth.showAlert('authAlert', data.message || 'Mã OTP không hợp lệ.', 'error');
          if (submitBtn) {
            submitBtn.disabled = false;
            submitBtn.innerHTML = '<span>Xác thực tài khoản</span>';
          }
          return;
        }

        // Verification successful!
        sessionStorage.removeItem('pending_verification_email');
        if (data.user) {
          localStorage.setItem('user', JSON.stringify(data.user));
        }

        Auth.showAlert('authAlert', 'Kích hoạt tài khoản thành công! Đang chuyển hướng...', 'success');
        setTimeout(() => {
          window.location.href = Auth.getRedirectUrl();
        }, 1000);

      } catch (err) {
        console.error('Verify error:', err);
        Auth.showAlert('authAlert', 'Lỗi kết nối máy chủ. Vui lòng thử lại sau.', 'error');
        if (submitBtn) {
          submitBtn.disabled = false;
          submitBtn.innerHTML = '<span>Xác thực tài khoản</span>';
        }
      }
    });
  }
});
