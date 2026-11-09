class ApiClient {
  constructor(baseUrl) {
    this.baseUrl = baseUrl || (typeof CONFIG !== 'undefined' ? CONFIG.API_BASE_URL : '/api/v2');
  }

  async request(endpoint, options = {}) {
    const token = localStorage.getItem('token');
    const headers = {
      'Content-Type': 'application/json',
      'Accept': 'application/json',
      ...(token ? { 'Authorization': `Token ${token}` } : {}),
      ...options.headers
    };

    try {
      const cleanEndpoint = endpoint.startsWith('/') ? endpoint : `/${endpoint}`;
      const response = await fetch(`${this.baseUrl}${cleanEndpoint}`, {
        ...options,
        headers
      });

      const data = await response.json().catch(() => null);
      if (!response.ok) {
        return { 
          success: false, 
          status: response.status, 
          error: (data && data.error) ? data.error : { message: `HTTP ${response.status}: ${response.statusText}` } 
        };
      }
      return { success: true, status: response.status, ...(data || {}) };
    } catch (err) {
      console.error(`[API ERROR] ${endpoint}:`, err);
      return { success: false, status: 0, error: { message: err.message || 'Lỗi kết nối máy chủ' } };
    }
  }

  get(endpoint) { return this.request(endpoint, { method: 'GET' }); }
  post(endpoint, data) { return this.request(endpoint, { method: 'POST', body: JSON.stringify(data) }); }
  put(endpoint, data) { return this.request(endpoint, { method: 'PUT', body: JSON.stringify(data) }); }
  delete(endpoint) { return this.request(endpoint, { method: 'DELETE' }); }
}

const api = new ApiClient();
