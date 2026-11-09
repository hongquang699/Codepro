/**
 * CodeProOJ - Moderator Action Engine
 */
const Moderator = {
  approveProblem(problemCode) {
    if (!confirm(`Phê duyệt công khai bài tập ${problemCode}?`)) return;
    fetch(`/api/v2/problem/${encodeURIComponent(problemCode)}/publish`, {
      method: 'POST',
      headers: window.adminApiHeaders ? window.adminApiHeaders() : {}
    })
      .then(async res => {
        const json = await res.json();
        if (!res.ok) throw new Error(json?.error?.message || 'Không thể duyệt bài tập');
        return json;
      })
      .then(json => {
        alert(json.data?.message || 'Đã duyệt bài tập thành công!');
        window.location.reload();
      })
      .catch(err => alert('Lỗi: ' + err.message));
  },

  rejectProblem(problemCode) {
    const reason = prompt('Lý do từ chối bài tập:');
    if (reason) {
      alert(`Đã từ chối bài ${problemCode}. Lý do: ${reason}`);
    }
  }
};

window.Moderator = Moderator;
