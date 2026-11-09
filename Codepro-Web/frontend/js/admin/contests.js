/**
 * CodeProOJ - Admin Contest Operations
 */
const AdminContests = {
  async getContests() {
    try {
      const res = await fetch('/api/v2/contests');
      const json = await res.json();
      return json.data?.items || json.data?.results || [];
    } catch (e) {
      console.error(e);
      return [];
    }
  },

  async rejudgeContest(contestKey) {
    if (!confirm(`Xác nhận rejudge toàn bộ bài nộp kỳ thi ${contestKey}?`)) return;
    try {
      const res = await fetch(`/api/v2/rejudge/contest/${contestKey}`, { method: 'POST' });
      const json = await res.json();
      alert(json.data?.message || 'Đã kích hoạt rejudge');
    } catch (e) {
      alert('Lỗi: ' + e.message);
    }
  }
};

window.AdminContests = AdminContests;
