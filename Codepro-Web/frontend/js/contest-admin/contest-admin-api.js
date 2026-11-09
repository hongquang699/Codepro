/**
 * CodeProOJ Contest Admin API Client
 */

const ContestAdminAPI = {
  baseUrl: '/api/v1/contest-admin',

  getContestKey() {
    const params = new URLSearchParams(window.location.search);
    if (params.get('contest')) return params.get('contest');
    if (params.get('key')) return params.get('key');
    if (params.get('id')) return params.get('id');
    
    // Check path /admin/contests/:key/
    const m = window.location.pathname.match(/\/admin\/contests\/([^\/]+)/);
    if (m && m[1]) return m[1];
    return 'HSG_TIN_2026';
  },

  async request(endpoint, options = {}) {
    const headers = {
      'Content-Type': 'application/json',
      ...(options.headers || {})
    };

    const token = localStorage.getItem('token') || localStorage.getItem('access_token');
    if (token) {
      headers['Authorization'] = `Token ${token}`;
    }
    const csrf = document.cookie.match(/(?:^|;\s*)csrftoken=([^;]+)/);
    if (csrf && options.method && !['GET', 'HEAD'].includes(options.method.toUpperCase())) {
      headers['X-CSRFToken'] = decodeURIComponent(csrf[1]);
    }
    try {
      const resp = await fetch(`${this.baseUrl}${endpoint}`, {
        ...options,
        headers
      });
      const data = await resp.json().catch(() => ({}));
      return data;
    } catch (err) {
      console.error('ContestAdminAPI Error:', err);
      return { status: 500, error: err.message || 'Lỗi kết nối máy chủ.' };
    }
  },

  // 1. Contests Portal
  getContests() {
    return this.request('/contests');
  },

  createContest(payload) {
    return this.request('/contests', {
      method: 'POST',
      body: JSON.stringify(payload)
    });
  },

  // 2. Dashboard
  getDashboard(contestKey) {
    return this.request(`/contests/${contestKey}/dashboard`);
  },

  // 3. Settings & Freeze
  getSettings(contestKey) {
    return this.request(`/contests/${contestKey}/settings`);
  },

  updateSettings(contestKey, payload) {
    return this.request(`/contests/${contestKey}/settings`, {
      method: 'PUT',
      body: JSON.stringify(payload)
    });
  },

  toggleFreeze(contestKey, action) {
    return this.request(`/contests/${contestKey}/freeze`, {
      method: 'POST',
      body: JSON.stringify({ action })
    });
  },

  // 4. Problems
  getProblems(contestKey) {
    return this.request(`/contests/${contestKey}/problems`);
  },

  addProblem(contestKey, payload) {
    return this.request(`/contests/${contestKey}/problems`, {
      method: 'POST',
      body: JSON.stringify(payload)
    });
  },

  removeProblem(contestKey, problemCode) {
    return this.request(`/contests/${contestKey}/problems`, {
      method: 'DELETE',
      body: JSON.stringify({ code: problemCode })
    });
  },

  getStatement(contestKey, problemCode) {
    return this.request(`/contests/${contestKey}/problems/${problemCode}/statement`);
  },

  updateStatement(contestKey, problemCode, statement) {
    return this.request(`/contests/${contestKey}/problems/${problemCode}/statement`, {
      method: 'PUT',
      body: JSON.stringify({ statement })
    });
  },

  getTestcases(contestKey, problemCode) {
    return this.request(`/contests/${contestKey}/problems/${problemCode}/testcases`);
  },

  addTestcase(contestKey, problemCode, payload) {
    return this.request(`/contests/${contestKey}/problems/${problemCode}/testcases`, {
      method: 'POST',
      body: JSON.stringify(payload)
    });
  },

  deleteTestcase(contestKey, problemCode, testId) {
    return this.request(`/contests/${contestKey}/problems/${problemCode}/testcases`, {
      method: 'DELETE',
      body: JSON.stringify({ id: testId })
    });
  },

  // 5. Participants
  getParticipants(contestKey) {
    return this.request(`/contests/${contestKey}/participants`);
  },

  participantAction(contestKey, action, username, payload = {}) {
    return this.request(`/contests/${contestKey}/participants`, {
      method: 'POST',
      body: JSON.stringify({ action, username, ...payload })
    });
  },

  // 6. Submissions
  getSubmissions(contestKey, filters = {}) {
    const q = new URLSearchParams(filters).toString();
    return this.request(`/contests/${contestKey}/submissions${q ? '?' + q : ''}`);
  },

  getSubmissionDetail(contestKey, submissionId) {
    return this.request(`/contests/${contestKey}/submissions/${submissionId}`);
  },

  rejudge(contestKey, payload = {}) {
    return this.request(`/contests/${contestKey}/rejudge`, {
      method: 'POST',
      body: JSON.stringify(payload)
    });
  },

  // 7. Ranking
  getRanking(contestKey) {
    return this.request(`/contests/${contestKey}/ranking`);
  },

  getExportUrl(contestKey) {
    return `${this.baseUrl}/contests/${contestKey}/ranking?export=csv`;
  },

  // 8. Announcements & Clarifications
  getAnnouncements(contestKey) {
    return this.request(`/contests/${contestKey}/announcements`);
  },

  createAnnouncement(contestKey, payload) {
    return this.request(`/contests/${contestKey}/announcements`, {
      method: 'POST',
      body: JSON.stringify(payload)
    });
  },

  deleteAnnouncement(contestKey, id) {
    return this.request(`/contests/${contestKey}/announcements`, {
      method: 'DELETE',
      body: JSON.stringify({ id })
    });
  },

  getClarifications(contestKey) {
    return this.request(`/contests/${contestKey}/clarifications`);
  },

  answerClarification(contestKey, id, answer, is_public = true) {
    return this.request(`/contests/${contestKey}/clarifications`, {
      method: 'POST',
      body: JSON.stringify({ id, answer, is_public })
    });
  },

  // 9. Jury & Cluster
  getJury(contestKey) {
    return this.request(`/contests/${contestKey}/jury`);
  },

  // 10. Reports
  getReports(contestKey) {
    return this.request(`/contests/${contestKey}/reports`);
  },

  antiCheat(contestKey, path = '', options = {}) {
    const contest = encodeURIComponent(contestKey);
    const token = localStorage.getItem('token') || localStorage.getItem('access_token');
    const csrf = document.cookie.match(/(?:^|;\s*)csrftoken=([^;]+)/);
    const headers = { 'Content-Type': 'application/json' };
    if (token) headers.Authorization = `Token ${token}`;
    if (csrf && options.method && !['GET', 'HEAD'].includes(options.method.toUpperCase())) {
      headers['X-CSRFToken'] = decodeURIComponent(csrf[1]);
    }
    return fetch(`/api/v1/admin/contests/${contest}/anti-cheat${path}`, {
      credentials: 'same-origin', ...options, headers: { ...headers, ...(options.headers || {}) }
    }).then(async response => {
      const data = await response.json().catch(() => ({}));
      if (!response.ok) throw new Error(data.detail || data.error || `HTTP ${response.status}`);
      return data;
    });
  },

  // 11. Audit Log
  getAuditLog(contestKey) {
    return this.request(`/contests/${contestKey}/audit`);
  }
};
