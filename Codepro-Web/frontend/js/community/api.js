/**
 * CodeProOJ Community Platform - Client API Service
 */
const CommunityAPI = (() => {
  const BASE = (window.API_BASE || window.location.origin) + '/api/v1/community';

  async function request(endpoint, options = {}) {
    const url = `${BASE}/${endpoint.replace(/^\//, '')}`;
    const headers = {
      'Content-Type': 'application/json',
      ...(options.headers || {})
    };

    const token = localStorage.getItem('token');
    if (token) {
      headers['Authorization'] = `Token ${token}`;
    }

    const response = await fetch(url, { ...options, headers });
    const json = await response.json();
    return json;
  }

  return {
    // Feed
    getFeed: () => request('/feed'),

    // Posts
    getPosts: (params = '') => request(`/posts${params ? '?' + params : ''}`),
    getPost: (id) => request(`/posts/${id}`),
    createPost: (data) => request('/posts', { method: 'POST', body: JSON.stringify(data) }),
    getComments: (postId) => request(`/posts/${postId}/comments`),
    addComment: (postId, data) => request(`/posts/${postId}/comments`, { method: 'POST', body: JSON.stringify(data) }),

    // Reactions
    toggleReaction: (targetType, targetId, reactionType = 'like') => request('/reactions', {
      method: 'POST',
      body: JSON.stringify({ target_type: targetType, target_id: targetId, reaction_type: reactionType })
    }),

    // Forum
    getCategories: () => request('/forum/categories'),
    getCategoryThreads: (slug, search = '') => request(`/forum/categories/${slug}/threads${search ? '?q=' + encodeURIComponent(search) : ''}`),
    getThreads: (params = '') => request(`/forum/threads${params ? '?' + params : ''}`),
    getThread: (id) => request(`/forum/threads/${id}`),
    createThread: (data) => request('/forum/threads', { method: 'POST', body: JSON.stringify(data) }),
    replyThread: (id, content) => request(`/forum/threads/${id}/reply`, { method: 'POST', body: JSON.stringify({ content }) }),

    // Groups
    getGroups: () => request('/groups'),
    joinGroup: (id) => request(`/groups/${id}/join`, { method: 'POST' }),
    leaveGroup: (id) => request(`/groups/${id}/leave`, { method: 'POST' }),

    // Direct Messages
    getConversations: () => request('/messages/conversations'),
    getMessages: (convId) => request(`/messages/${convId}`),
    sendMessage: (convId, content) => request(`/messages/${convId}`, { method: 'POST', body: JSON.stringify({ content }) }),

    // Notifications
    getNotifications: () => request('/notifications'),
    readAllNotifications: () => request('/notifications/read-all', { method: 'POST' }),

    // Search
    search: (query) => request(`/search?q=${encodeURIComponent(query)}`),

    // Current User Helper
    getCurrentUsername: () => {
      try {
        const u = JSON.parse(localStorage.getItem('user'));
        if (u && u.username) return u.username;
      } catch (e) {}
      return localStorage.getItem('username') || '';
    }
  };
})();

window.CommunityAPI = CommunityAPI;

window.escapeCommunityHtml = value => String(value ?? '').replace(/[&<>"']/g, char => ({
  '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;'
})[char]);
window.communityId = value => {
  const id = Number(value);
  return Number.isSafeInteger(id) && id > 0 ? id : 0;
};
window.communityLink = value => {
  try {
    const url = new URL(String(value), window.location.origin);
    if (url.origin === window.location.origin && /^https?:$/.test(url.protocol)) {
      return window.escapeCommunityHtml(url.pathname + url.search + url.hash);
    }
  } catch { /* Invalid or external links are not rendered. */ }
  return '';
};
