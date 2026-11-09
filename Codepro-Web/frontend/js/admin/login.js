/**
 * CodeProOJ - Admin Login Authentication Logic
 */

document.getElementById('adminLoginForm').addEventListener('submit', async function(e) {
      e.preventDefault();
      const username = document.getElementById('adminUsername').value.trim();
      const password = document.getElementById('adminPassword').value;
      const errorAlert = document.getElementById('adminErrorAlert');
      const submitBtn = document.getElementById('adminSubmitBtn');

      errorAlert.style.display = 'none';
      submitBtn.disabled = true;
      submitBtn.innerText = 'Đang xác thực...';

      try {
        const response = await fetch(`${CONFIG.API_BASE_URL}/auth/login`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ username, password })
        });
        const res = await response.json();

        if (response.ok && res.status === 200) {
          Auth.setUser(res.data.user, res.data.token);
          document.cookie = 'role=admin; path=/; max-age=86400; SameSite=Lax';
          document.cookie = 'is_admin=true; path=/; max-age=86400; SameSite=Lax';
          window.location.href = '/frontend/html/admin/dashboard.html';
        } else {
          errorAlert.style.display = 'block';
          errorAlert.innerText = (res.error && res.error.message) || 'Thông tin quản trị không chính xác!';
          submitBtn.disabled = false;
          submitBtn.innerText = 'Đăng nhập Quản trị';
        }
      } catch (err) {
        errorAlert.style.display = 'block';
        errorAlert.innerText = 'Không thể kết nối Backend API trên cổng 8000.';
        submitBtn.disabled = false;
        submitBtn.innerText = 'Đăng nhập Quản trị';
      }
    });
