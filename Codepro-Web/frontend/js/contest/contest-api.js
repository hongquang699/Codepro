/**
 * CodeProOJ - Contest API Client & WebSocket/Polling Engine
 */
const ContestAPI = (() => {
  const API_BASE = window.API_BASE || window.location.origin;

  function getHeaders() {
    const headers = { 'Content-Type': 'application/json' };
    const token = localStorage.getItem('token');
    if (token) {
      headers['Authorization'] = `Token ${token}`;
    }
    return headers;
  }

  function getCurrentUser() {
    try {
      const raw = localStorage.getItem('user');
      return raw ? JSON.parse(raw) : null;
    } catch (e) {
      return null;
    }
  }

  return {
    getCurrentUser,

    async getContest(contestKey) {
      const res = await fetch(`${API_BASE}/api/v1/contests/${contestKey}/`, { headers: getHeaders() });
      return await res.json();
    },

    async registerContest(contestKey, accessCode) {
      const u = getCurrentUser()?.username;
      const res = await fetch(`${API_BASE}/api/v1/contests/${contestKey}/register`, {
        method: 'POST',
        headers: getHeaders(),
        body: JSON.stringify({ username: u, user: u, access_code: accessCode || '' })
      });
      const data = await res.json();
      if (res.status === 403 && data?.error?.code === 'ACCESS_CODE_REQUIRED' && accessCode === undefined) {
        const code = window.prompt('Kỳ thi yêu cầu mã truy cập:');
        if (code) return this.registerContest(contestKey, code);
      }
      return data;
    },

    async leaveContest(contestKey) {
      const u = getCurrentUser()?.username;
      const res = await fetch(`${API_BASE}/api/v1/contests/${contestKey}/leave`, {
        method: 'POST',
        headers: getHeaders(),
        body: JSON.stringify({ username: u, user: u })
      });
      return await res.json();
    },

    async getDashboard(contestKey) {
      const u = getCurrentUser()?.username || '';
      const url = `${API_BASE}/api/v1/contests/${contestKey}/dashboard${u ? `?user=${encodeURIComponent(u)}` : ''}`;
      const res = await fetch(url, { headers: getHeaders() });
      return await res.json();
    },

    async getProblem(contestKey, problemId) {
      const u = getCurrentUser()?.username || '';
      const url = `${API_BASE}/api/v1/contests/${contestKey}/problems/${problemId}${u ? `?user=${encodeURIComponent(u)}` : ''}`;
      const res = await fetch(url, { headers: getHeaders() });
      return await res.json();
    },

    async submitProblem(contestKey, problemId, language, sourceCode) {
      const res = await fetch(`${API_BASE}/api/v1/contests/${contestKey}/problems/${problemId}/submit`, {
        method: 'POST',
        headers: getHeaders(),
        body: JSON.stringify({
          language,
          source_code: sourceCode,
          user: getCurrentUser()?.username
        })
      });
      return await res.json();
    },

    async getSubmission(submissionId) {
      const res = await fetch(`${API_BASE}/api/v1/submissions/${submissionId}/`, { headers: getHeaders() });
      return await res.json();
    },

    async getSubmissionsList(contestKey, filters = {}) {
      let query = new URLSearchParams(filters).toString();
      const url = `${API_BASE}/api/v1/contests/${contestKey}/submissions${query ? `?${query}` : ''}`;
      const res = await fetch(url, { headers: getHeaders() });
      return await res.json();
    },

    async getRanking(contestKey) {
      const res = await fetch(`${API_BASE}/api/v1/contests/${contestKey}/ranking`, { headers: getHeaders() });
      return await res.json();
    },

    async getAnnouncements(contestKey) {
      const res = await fetch(`${API_BASE}/api/v1/contests/${contestKey}/announcements`, { headers: getHeaders() });
      return await res.json();
    },

    async getClarifications(contestKey) {
      const res = await fetch(`${API_BASE}/api/v1/contests/${contestKey}/clarifications`, { headers: getHeaders() });
      return await res.json();
    },

    async askClarification(contestKey, data) {
      const res = await fetch(`${API_BASE}/api/v1/contests/${contestKey}/clarifications`, {
        method: 'POST',
        headers: getHeaders(),
        body: JSON.stringify({ ...data, user: getCurrentUser()?.username })
      });
      return await res.json();
    },

    /**
     * Poll submission status until completed
     */
    pollStatus(submissionId, onUpdate, onDone, maxAttempts = 30) {
      let attempts = 0;
      const interval = setInterval(async () => {
        attempts++;
        try {
          const res = await fetch(`${API_BASE}/api/v1/submissions/${submissionId}/status/`, { headers: getHeaders() });
          const json = await res.json();
          if (json && json.data) {
            onUpdate(json.data);
            if (json.data.is_done || attempts >= maxAttempts) {
              clearInterval(interval);
              onDone(json.data);
            }
          }
        } catch (e) {
          if (attempts >= maxAttempts) {
            clearInterval(interval);
            onDone(null);
          }
        }
      }, 1000);
      return () => clearInterval(interval);
    }
  };
})();
