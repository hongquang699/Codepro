/* Private contest downloads: authenticated POST with visible progress. */
async function downloadContestArchive() {
  const button = document.getElementById('btnDownloadArchive');
  if (!button || button.disabled) return;
  let status = document.getElementById('archiveDownloadStatus');
  if (!status) {
    status = document.createElement('p');
    status.id = 'archiveDownloadStatus';
    status.setAttribute('role', 'status');
    status.setAttribute('aria-live', 'polite');
    document.querySelector('.admin-topbar').after(status);
  }
  button.disabled = true;
  button.setAttribute('aria-busy', 'true');
  status.textContent = 'Đang đóng gói dữ liệu cuộc thi…';
  try {
    const headers = {};
    const token = localStorage.getItem('token') || localStorage.getItem('access_token');
    if (token) headers.Authorization = `Token ${token}`;
    const csrf = document.cookie.match(/(?:^|;\s*)csrftoken=([^;]+)/);
    if (csrf) headers['X-CSRFToken'] = decodeURIComponent(csrf[1]);
    const response = await fetch(`/api/v2/admin/contest/${encodeURIComponent(contestKey)}/archive`, {
      method: 'POST', credentials: 'same-origin', headers
    });
    if (!response.ok) {
      const data = await response.json().catch(() => ({}));
      throw new Error(data.error || data.detail || 'Không thể tải bản lưu. Kiểm tra quyền quản trị và thử lại.');
    }
    const url = URL.createObjectURL(await response.blob());
    const link = document.createElement('a');
    link.href = url;
    link.download = `contest-${contestKey.replace(/[^a-zA-Z0-9_-]/g, '_')}.zip`;
    document.body.appendChild(link);
    link.click();
    link.remove();
    setTimeout(() => URL.revokeObjectURL(url), 60000);
    status.textContent = 'Đã tạo bản lưu. Tệp chứa mã nguồn và bộ test riêng tư; hãy lưu ở nơi chỉ người có quyền truy cập được.';
  } catch (error) {
    status.textContent = error.message;
  } finally {
    button.disabled = false;
    button.removeAttribute('aria-busy');
  }
}
