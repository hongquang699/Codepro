/**
 * CodeProOJ - User Forum Discussions Controller
 */
const UserForum = {
  async getMyThreads(username) {
    try {
      const res = await fetch(`/api/community/threads/?author=${username}`);
      const json = await res.json();
      return json.results || [];
    } catch (e) {
      return [];
    }
  }
};

window.UserForum = UserForum;
