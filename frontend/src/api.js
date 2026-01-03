// This is the central service for all communication with your backend API.

const API_BASE_URL = 'http://127.0.0.1:8000'; // Your FastAPI backend URL

const api = {
  /**
   * The core request function. Handles token authentication, headers,
   * and error handling for all API calls.
   */
  async request(endpoint, { body, method, ...customConfig } = {}) {
    const token = localStorage.getItem('dojo_token');
    const headers = { 'Content-Type': 'application/json' };

    if (token) {
      headers.Authorization = `Bearer ${token}`;
    }

    const config = {
      method: body ? (method || 'POST') : (method || 'GET'),
      ...customConfig,
      headers: { ...headers, ...customConfig.headers },
    };

    if (body) {
      config.body = JSON.stringify(body);
    }

    try {
      const response = await fetch(`${API_BASE_URL}${endpoint}`, config);
      if (!response.ok) {
        // Try to parse the error, but have a fallback.
        const errorData = await response.json().catch(() => ({ detail: 'An unknown error occurred.' }));
        throw new Error(errorData.detail || 'Something went wrong');
      }
      // Handle responses with no content (like a 204 No Content)
      return response.status === 204 ? {} : response.json();
    } catch (error) {
      console.error('API Service Error:', error);
      throw error;
    }
  },

  /**
   * Special case for login, as it uses form data instead of JSON.
   */
  login: (email, password) => {
    const formData = new URLSearchParams();
    formData.append('username', email); // The backend expects 'username' for the form
    formData.append('password', password);

    return fetch(`${API_BASE_URL}/auth/login`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
      body: formData,
    }).then(async (res) => {
      if (!res.ok) {
        const errorData = await res.json().catch(() => ({}));
        throw new Error(errorData.detail || 'Login failed');
      }
      return res.json();
    });
  },

  // --- User & Auth ---
  // UPDATED: Added github_username to match the registration form's requirements.
  register: (username, email, password, github_username) =>
    api.request('/auth/register', { body: { username, email, password, github_username } }),
  getMe: () => api.request('/auth/me'),
  updateMe: (github_username) =>
    api.request('/auth/me', { method: 'PUT', body: { github_username } }),

  // --- Groups ---
  getGroups: () => api.request('/groups/'),
  getGroup: (groupId) => api.request(`/groups/${groupId}`),
  createGroup: (name, description) =>
    api.request('/groups/', { body: { name, description } }),
  joinGroup: (groupId) =>
    api.request(`/groups/${groupId}/join`, { method: 'POST' }),

  // --- Challenges ---
  createChallenge: ({ Topic, difficulty, group_id }) =>
    api.request('/challenges/', { body: { Topic, difficulty, group_id } }),

  // CORRECT: This function properly calls your new endpoint.
  getChallengeHistory: (groupId) =>
    api.request(`/challenges/group/${groupId}`),

  // --- Submissions & Leaderboard ---
  getMySubmissions: () => api.request('/submissions/'),
  getGroupLeaderboard: (groupId) =>
    api.request(`/leaderboard/group/${groupId}`),
};

export default api;