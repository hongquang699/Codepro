/**
 * CodeProOJ - User Problems & Solved List Controller
 */
const UserProblems = {
  async getSolvedProblems(username) {
    try {
      const res = await fetch(`/api/v1/users/${username}/problems`);
      const json = await res.json();
      return json.data || [];
    } catch (e) {
      return [];
    }
  }
};

window.UserProblems = UserProblems;
