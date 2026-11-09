/**
 * Create Thread logic
 */
document.addEventListener('DOMContentLoaded', () => {
  const btn = document.getElementById('btnCreateThread');
  if (!btn) return;

  btn.addEventListener('click', async () => {
    const title = document.getElementById('threadTitleInput').value.trim();
    const content = document.getElementById('threadContentInput').value.trim();
    const category_slug = document.getElementById('threadCategorySelect').value;

    if (!title || !content) {
      alert('Vui lòng nhập đầy đủ tiêu đề và nội dung chủ đề!');
      return;
    }

    btn.disabled = true;
    try {
      const res = await CommunityAPI.createThread({ title, content, category_slug });
      if (res && res.status === 201) {
        alert('Tạo chủ đề thành công!');
        window.location.href = `/frontend/html/community/forum/thread.html?id=${res.data.id}`;
      } else {
        alert(res?.error?.message || 'Lỗi khi tạo chủ đề');
      }
    } catch (err) {
      alert('Lỗi: ' + err.message);
    } finally {
      btn.disabled = false;
    }
  });
});
