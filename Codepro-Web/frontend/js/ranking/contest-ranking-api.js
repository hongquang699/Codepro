/**
 * Contest Ranking & Scoreboard API Client
 */
const ContestRankingApi = {
  baseUrl: '/api/v1/rankings',

  async fetchScoreboard(contestId, live = true) {
    const res = await fetch(`${this.baseUrl}/contest/${contestId}/?live=${live}`);
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    return await res.json();
  },

  async fetchProblemSolvers(problemCode, limit = 50) {
    const res = await fetch(`${this.baseUrl}/problems/${encodeURIComponent(problemCode)}/?limit=${limit}`);
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    return await res.json();
  },

  async recalculateRatings(contestId) {
    const res = await fetch(`${this.baseUrl}/contest/${contestId}/compute-ratings/`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' }
    });
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    return await res.json();
  }
};

window.ContestRankingApi = ContestRankingApi;
