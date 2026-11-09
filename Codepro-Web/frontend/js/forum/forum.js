/**
 * CodeProOJ - Forum Discussion Service
 */
const ForumService = {
  async getThreads(categoryId = null) {
    try {
      const url = categoryId ? `/api/community/threads/?category=${categoryId}` : '/api/community/threads/';
      const res = await fetch(url);
      const json = await res.json();
      return json.results || json.data || [];
    } catch (e) {
      console.error(e);
      return [];
    }
  },

  async vote(threadId, type = 'up') {
    try {
      const res = await fetch(`/api/community/threads/${threadId}/vote/`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ type })
      });
      return await res.json();
    } catch (e) {
      console.error(e);
      return null;
    }
  }
};

window.ForumService = ForumService;
