/**
 * Ranking API Client
 */
const RankingApi = {
  baseUrl: '/api/v1/rankings',

  async fetchGlobalRankings({ page = 1, page_size = 50, country = '', school = '', organization = '', search = '' } = {}) {
    const params = new URLSearchParams();
    if (page) params.append('page', page);
    if (page_size) params.append('page_size', page_size);
    if (country) params.append('country', country);
    if (school) params.append('school', school);
    if (organization) params.append('organization', organization);
    if (search) params.append('search', search);

    const res = await fetch(`${this.baseUrl}/global/?${params.toString()}`);
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    return await res.json();
  },

  async fetchCountryRankings(countryName = '') {
    const url = countryName 
      ? `${this.baseUrl}/country/${encodeURIComponent(countryName)}/`
      : `${this.baseUrl}/country/`;
    const res = await fetch(url);
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    return await res.json();
  },

  async fetchSchoolRankings(schoolName = '') {
    const url = schoolName 
      ? `${this.baseUrl}/school/${encodeURIComponent(schoolName)}/`
      : `${this.baseUrl}/school/`;
    const res = await fetch(url);
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    return await res.json();
  },

  async fetchOrgRankings(orgId = '') {
    const url = orgId 
      ? `${this.baseUrl}/organization/${orgId}/`
      : `${this.baseUrl}/organization/`;
    const res = await fetch(url);
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    return await res.json();
  },

  async fetchUserRanking(usernameOrId) {
    const res = await fetch(`${this.baseUrl}/users/${encodeURIComponent(usernameOrId)}/`);
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    return await res.json();
  },

  async fetchStatistics() {
    const res = await fetch(`${this.baseUrl}/statistics/`);
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    return await res.json();
  },

  async search(query) {
    const res = await fetch(`${this.baseUrl}/search/?q=${encodeURIComponent(query)}`);
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    return await res.json();
  }
};

window.RankingApi = RankingApi;
