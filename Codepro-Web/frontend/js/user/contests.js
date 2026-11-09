/**
 * CodeProOJ - User Contests Controller
 */
const UserContests = {
  async getMyContests(username) {
    try {
      const res = await fetch(`/api/v2/contests?user=${username}`);
      const json = await res.json();
      return json.data?.items || json.data?.results || [];
    } catch (e) {
      return [];
    }
  }
};

window.UserContests = UserContests;
