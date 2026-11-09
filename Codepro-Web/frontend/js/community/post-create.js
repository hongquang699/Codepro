/**
 * Create Post Form Logic
 */
document.addEventListener('DOMContentLoaded', () => {
  const btn = document.getElementById('btnSubmitPost');
  const titleInput = document.getElementById('postTitle');
  const contentInput = document.getElementById('postContent');
  const tagsInput = document.getElementById('postTags');

  if (!btn || !titleInput || !contentInput) return;

  btn.addEventListener('click', async () => {
    const title = titleInput.value.trim();
    const content = contentInput.value.trim();
    const tags = tagsInput ? tagsInput.value.split(',').map(t => t.trim()).filter(Boolean) : [];

    if (!title || !content) {
      alert('Vui lòng nhập đầy đủ tiêu đề và nội dung bài viết!');
      return;
    }

    btn.disabled = true;
    btn.textContent = 'Đang lưu bài viết...';

    try {
      const res = await CommunityAPI.createPost({ title, content, tags });
      if (res && res.status === 201) {
        alert('Đăng bài viết thành công!');
        window.location.href = `/frontend/html/community/posts/detail.html?id=${res.data.id}`;
      } else {
        alert(res?.error?.message || 'Không thể tạo bài viết');
      }
    } catch (err) {
      alert('Lỗi: ' + err.message);
    } finally {
      btn.disabled = false;
      btn.textContent = 'Xuất bản bài viết';
    }
  });
});
