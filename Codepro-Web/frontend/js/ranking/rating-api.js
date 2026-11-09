/**
 * Rating API Client
 */
const RatingApi = {
  baseUrl: '/api/v1/rankings',

  async fetchRatingLeaderboard({ page = 1, page_size = 50, tier = '', search = '' } = {}) {
    const params = new URLSearchParams();
    if (page) params.append('page', page);
    if (page_size) params.append('page_size', page_size);
    if (tier) params.append('tier', tier);
    if (search) params.append('search', search);

    const res = await fetch(`${this.baseUrl}/rating/?${params.toString()}`);
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    return await res.json();
  },

  async fetchRatingHistory(usernameOrId) {
    const res = await fetch(`${this.baseUrl}/history/${encodeURIComponent(usernameOrId)}/`);
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    return await res.json();
  }
};

window.RatingApi = RatingApi;
