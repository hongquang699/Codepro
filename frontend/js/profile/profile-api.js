/**
 * CodeProOJ - User Profile API Client & Shared UI Renderer
 */
const ProfileAPI = (() => {
  const API_BASE = (window.API_BASE !== undefined) ? window.API_BASE : '';

  function getHeaders() {
    const headers = { 'Content-Type': 'application/json' };
    const token = localStorage.getItem('token');
    if (token) headers['Authorization'] = `Token ${token}`;
    return headers;
  }

  async function readJson(res) {
    const contentType = res.headers.get('content-type') || '';
    if (!contentType.includes('application/json')) {
      throw new Error(`Máy chủ trả về dữ liệu không hợp lệ (HTTP ${res.status}).`);
    }
    const data = await res.json();
    if (!res.ok) throw new Error(data.error || data.message || `Lỗi HTTP ${res.status}`);
    return data;
  }

  function getRankColor(rank, rating) {
    if (typeof CPRating !== 'undefined') {
      return CPRating.getColor(rank, rating);
    }
    const numRating = parseInt(rating, 10);
    if (!isNaN(numRating) && numRating <= 0) return '#94a3b8';

    const r = (rank || '').toLowerCase().trim();
    if (r === 'unrated' || r.includes('chưa') || r === '0') return '#94a3b8';

    if (typeof rating === 'number' && !isNaN(rating)) {
      if (rating >= 3000) return '#ef4444'; // LGM
      if (rating >= 2400) return '#ef4444'; // Grandmaster
      if (rating >= 2100) return '#f97316'; // Master
      if (rating >= 1900) return '#a855f7'; // Candidate Master
      if (rating >= 1600) return '#3b82f6'; // Expert
      if (rating >= 1400) return '#10b981'; // Specialist
      if (rating >= 1200) return '#06b6d4'; // Pupil
      return '#94a3b8'; // Newbie
    }

    if (r.includes('legendary') || r.includes('grandmaster')) return '#ef4444';
    if (r.includes('candidate')) return '#a855f7';
    if (r.includes('master')) return '#f97316';
    if (r.includes('expert')) return '#3b82f6';
    if (r.includes('specialist')) return '#10b981';
    if (r.includes('pupil')) return '#06b6d4';
    return '#94a3b8';
  }

  function getUsernameFromUrl() {
    // 1. Try path /profile/{username}/...
    const parts = window.location.pathname.split('/').filter(Boolean);
    const pIdx = parts.indexOf('profile');
    if (pIdx !== -1 && parts[pIdx + 1] && !parts[pIdx + 1].endsWith('.html')) {
      return decodeURIComponent(parts[pIdx + 1]);
    }
    // 2. Try query param ?user=... or ?username=...
    const urlParams = new URLSearchParams(window.location.search);
    const paramUser = urlParams.get('username') || urlParams.get('user');
    if (paramUser) return paramUser;

    try {
      const u = JSON.parse(localStorage.getItem('user'));
      if (u && u.username) return u.username;
    } catch (e) {}

    return localStorage.getItem('username') || '';
  }

  return {
    getRankColor,
    getUsernameFromUrl,

    async getOverview(username) {
      const res = await fetch(`${API_BASE}/api/v1/users/${encodeURIComponent(username)}`, { headers: getHeaders() });
      return readJson(res);
    },

    async getStatistics(username) {
      const res = await fetch(`${API_BASE}/api/v1/users/${username}/statistics`, { headers: getHeaders() });
      return await res.json();
    },

    async getSubmissions(username, params = {}) {
      const q = new URLSearchParams(params).toString();
      const res = await fetch(`${API_BASE}/api/v1/users/${username}/submissions${q ? '?' + q : ''}`, { headers: getHeaders() });
      return await res.json();
    },

    async getContests(username) {
      const res = await fetch(`${API_BASE}/api/v1/users/${encodeURIComponent(username)}/contests`, { headers: getHeaders() });
      return readJson(res);
    },

    async getProblems(username) {
      const res = await fetch(`${API_BASE}/api/v1/users/${encodeURIComponent(username)}/problems`, { headers: getHeaders() });
      return readJson(res);
    },

    async getRating(username) {
      const res = await fetch(`${API_BASE}/api/v1/users/${username}/rating`, { headers: getHeaders() });
      return await res.json();
    },

    async getRatingHistory(username) {
      const res = await fetch(`${API_BASE}/api/v1/users/${username}/rating/history`, { headers: getHeaders() });
      return await res.json();
    },

    async getOrganizations(username) {
      const res = await fetch(`${API_BASE}/api/v1/users/${username}/organizations`, { headers: getHeaders() });
      return await res.json();
    },

    async getAchievements(username) {
      const res = await fetch(`${API_BASE}/api/v1/users/${username}/achievements`, { headers: getHeaders() });
      return await res.json();
    },

    async getActivity(username) {
      const res = await fetch(`${API_BASE}/api/v1/users/${username}/activity`, { headers: getHeaders() });
      return await res.json();
    },

    async getBlog(username) {
      const res = await fetch(`${API_BASE}/api/v1/users/${username}/blog`, { headers: getHeaders() });
      return await res.json();
    },

    async getSettings(username) {
      const res = await fetch(`${API_BASE}/api/v1/users/${username}/settings`, { headers: getHeaders() });
      return await res.json();
    },

    async saveSettings(username, data) {
      const res = await fetch(`${API_BASE}/api/v1/users/${username}/settings`, {
        method: 'PATCH',
        headers: getHeaders(),
        body: JSON.stringify(data)
      });
      return await res.json();
    },

    async updateProfile(username, data) {
      const res = await fetch(`${API_BASE}/api/v1/users/${username}/profile`, {
        method: 'PATCH',
        headers: getHeaders(),
        body: JSON.stringify(data)
      });
      return await res.json();
    },

    renderHeader(containerId, data, activeTab = 'overview') {
      const c = document.getElementById(containerId);
      if (!c) return;

      const p = data.profile || {};
      const s = data.statistics || {};
      const r = data.rating || {};
      const ratingVal = (typeof r.rating === 'number' ? r.rating : (typeof p.rating === 'number' ? p.rating : null));
      const rankColor = getRankColor(p.rank, ratingVal);
      const curUser = localStorage.getItem('username');
      const isOwner = (curUser && curUser.toLowerCase() === p.username.toLowerCase()) || p.is_staff;

      const u = encodeURIComponent(p.username);

      const verifiedBadge = p.is_verified ? `
        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" style="vertical-align:middle; margin-left:6px; display:inline-block;" title="Tài khoản đã xác minh chính chủ (Tích xanh CodeProOJ)">
          <path d="M9 12L11 14L15 10M12 3L13.91 4.26L16.14 3.73L17.55 5.48L19.78 5.74L20.31 7.97L22.06 9.38L21.53 11.61L22.79 13.52L21.53 15.43L22.06 17.66L20.31 19.07L19.78 21.3L17.55 21.56L16.14 23.31L13.91 22.78L12 24.04L10.09 22.78L7.86 23.31L6.45 21.56L4.22 21.3L3.69 19.07L1.94 17.66L2.47 15.43L1.21 13.52L2.47 11.61L1.94 9.38L3.69 7.97L4.22 5.74L6.45 5.48L7.86 3.73L10.09 4.26L12 3Z" fill="#38BDF8" stroke="#0284C7" stroke-width="1.2" stroke-linecap="round" stroke-linejoin="round"/>
          <path d="M8.5 12.5L11 15L16 9" stroke="white" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
        </svg>
      ` : '';

      c.innerHTML = `
        <div class="profile-hero">
          <div class="profile-header-top">
            <div class="profile-avatar-wrap">
              ${p.avatar ? `<img src="${p.avatar}" class="profile-avatar-img" style="border-color:${rankColor};" alt="${p.username}">` : `<div class="profile-avatar-img" style="border-color:${rankColor}; background:${rankColor}22; color:${rankColor};">${(p.username || 'U')[0].toUpperCase()}</div>`}
              <span class="profile-status-dot"></span>
            </div>

            <div class="profile-info-main">
              <div class="profile-name-row">
                <h1 class="profile-username" style="color:${rankColor}; display:inline-flex; align-items:center;">
                  ${p.username} ${verifiedBadge}
                </h1>
                <span class="profile-rank-badge" style="background:${rankColor}22; color:${rankColor}; border-color:${rankColor}55;">
                  ★ ${(s.contests > 0 || r.contest_count > 0) ? (p.rank || r.rank || 'Newbie') : 'Unrated'}
                </span>
              </div>
              <div class="profile-fullname">${p.display_name && p.display_name !== p.username ? p.display_name : 'Lập trình viên'}</div>
              
              <div class="profile-tags">
                ${p.country ? `<span class="profile-tag-item"><cp-icon name="globe" size="xs"></cp-icon> ${p.country}</span>` : ''}
                ${p.school ? `<span class="profile-tag-item"><cp-icon name="graduation-cap" size="xs"></cp-icon> ${p.school}</span>` : ''}
                ${p.organization ? `<span class="profile-tag-item"><cp-icon name="building" size="xs"></cp-icon> ${p.organization}</span>` : ''}
                ${p.github ? `<a href="https://github.com/${p.github}" target="_blank" style="color:#60a5fa; text-decoration:none;" class="profile-tag-item"><cp-icon name="github" size="xs"></cp-icon> ${p.github}</a>` : ''}
              </div>

              ${p.bio ? `<p class="profile-bio">${p.bio}</p>` : '<p class="profile-bio" style="font-style:italic; opacity:0.7;">Chưa có tiểu sử giới thiệu.</p>'}
            </div>

            <div class="profile-header-actions">
              ${isOwner ? `
                <a href="/profile/${u}/settings" class="btn-profile-act">
                  <cp-icon name="settings" size="xs"></cp-icon> Cài đặt
                </a>
              ` : `
                <button class="btn-profile-act primary" onclick="alert('Đã theo dõi ${p.username}!')">
                  <cp-icon name="plus" size="xs"></cp-icon> Theo dõi
                </button>
              `}
            </div>
          </div>

          <!-- Quick Metrics Row -->
          <div class="profile-metrics-row">
            <div class="metric-pill">
              <div class="label"><cp-icon name="star" size="xs" style="color:#fbbf24;"></cp-icon> Rating</div>
              <div class="val" style="color:${rankColor};">${(s.contests > 0 || r.contest_count > 0) ? (r.rating || p.rating || 0) : 0}</div>
            </div>
            <div class="metric-pill">
              <div class="label"><cp-icon name="trophy" size="xs" style="color:#f59e0b;"></cp-icon> Cấp bậc</div>
              <div class="val" style="color:${rankColor}; font-size:1.05rem;">${(s.contests > 0 || r.contest_count > 0) ? (p.rank || r.rank || 'Newbie') : 'Unrated'}</div>
            </div>
            <div class="metric-pill">
              <div class="label"><cp-icon name="check" size="xs" style="color:#10b981;"></cp-icon> Đã giải</div>
              <div class="val" style="color:#10b981;">${s.solved_problems ?? p.solved_count ?? 0}</div>
            </div>
            <div class="metric-pill">
              <div class="label"><cp-icon name="document" size="xs" style="color:#60a5fa;"></cp-icon> Tổng bài nộp</div>
              <div class="val" style="color:#60a5fa;">${s.total_submissions ?? 0}</div>
            </div>
            <div class="metric-pill">
              <div class="label"><cp-icon name="award" size="xs" style="color:#34d399;"></cp-icon> Tỷ lệ AC</div>
              <div class="val" style="color:#34d399;">${s.ac_rate ?? 0}%</div>
            </div>
            <div class="metric-pill">
              <div class="label"><cp-icon name="flag" size="xs" style="color:#f59e0b;"></cp-icon> Kỳ thi</div>
              <div class="val" style="color:#f59e0b;">${s.contests ?? 0}</div>
            </div>
          </div>
        </div>

        <!-- Navigation Tabs Bar -->
        <nav class="profile-tabs-nav">
          <a href="/profile/${u}" class="profile-tab-btn ${activeTab === 'overview' ? 'active' : ''}">
            <cp-icon name="home" size="xs"></cp-icon> Tổng quan
          </a>
          <a href="/profile/${u}/submissions" class="profile-tab-btn ${activeTab === 'submissions' ? 'active' : ''}">
            <cp-icon name="document" size="xs"></cp-icon> Bài nộp
          </a>
          <a href="/profile/${u}/contests" class="profile-tab-btn ${activeTab === 'contests' ? 'active' : ''}">
            <cp-icon name="trophy" size="xs"></cp-icon> Kỳ thi
          </a>
          <a href="/profile/${u}/problems" class="profile-tab-btn ${activeTab === 'problems' ? 'active' : ''}">
            <cp-icon name="code" size="xs"></cp-icon> Bài tập
          </a>
          <a href="/profile/${u}/rating" class="profile-tab-btn ${activeTab === 'rating' ? 'active' : ''}">
            <cp-icon name="chart" size="xs"></cp-icon> Rating
          </a>
          <a href="/profile/${u}/organizations" class="profile-tab-btn ${activeTab === 'organizations' ? 'active' : ''}">
            <cp-icon name="building" size="xs"></cp-icon> Tổ chức
          </a>
          <a href="/profile/${u}/achievements" class="profile-tab-btn ${activeTab === 'achievements' ? 'active' : ''}">
            <cp-icon name="award" size="xs"></cp-icon> Danh hiệu
          </a>
          <a href="/profile/${u}/activity" class="profile-tab-btn ${activeTab === 'activity' ? 'active' : ''}">
            <cp-icon name="bolt" size="xs"></cp-icon> Hoạt động
          </a>
          <a href="/profile/${u}/blog" class="profile-tab-btn ${activeTab === 'blog' ? 'active' : ''}">
            <cp-icon name="edit" size="xs"></cp-icon> Blog
          </a>
          ${isOwner ? `
            <a href="/profile/${u}/settings" class="profile-tab-btn ${activeTab === 'settings' ? 'active' : ''}">
              <cp-icon name="settings" size="xs"></cp-icon> Cài đặt
            </a>
          ` : ''}
        </nav>
      `;
    }
  };
})();
