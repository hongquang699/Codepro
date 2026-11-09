/**
 * CodeProOJ - Admin Submission Operations
 */
const AdminSubmissions = {
  async rejudge(id) {
    if (!confirm(`Rejudge bài nộp #${id}?`)) return;
    try {
      const res = await fetch(`/api/v2/rejudge/${id}`, { method: 'POST', headers: window.adminApiHeaders() });
      const json = await res.json();
      if (!res.ok) throw new Error(json?.error?.message || 'Không thể chấm lại bài');
      alert(json.data?.message || 'Đã gửi lại bài vào máy chấm');
      window.location.reload();
    } catch (e) {
      alert('Lỗi: ' + e.message);
    }
  }
};

window.AdminSubmissions = AdminSubmissions;
