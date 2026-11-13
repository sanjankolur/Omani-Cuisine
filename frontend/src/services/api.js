const DEFAULT_API_BASE_URL = 'http://localhost:8001/api/v1';
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || DEFAULT_API_BASE_URL;

export async function apiRequest(path, { token, ...options } = {}) {
  const baseUrls = [...new Set([API_BASE_URL, DEFAULT_API_BASE_URL])];

  for (const baseUrl of baseUrls) {
    const headers = new Headers(options.headers || {});
    if (!(options.body instanceof FormData)) headers.set('Content-Type', 'application/json');
    if (token) headers.set('Authorization', `Bearer ${token}`);

    let response;
    try {
      response = await fetch(`${baseUrl}${path}`, { ...options, headers });
    } catch (error) {
      if (baseUrl !== DEFAULT_API_BASE_URL) {
        continue;
      }
      throw new Error(`Could not connect to the API at ${baseUrl}. Make sure the backend is running.`);
    }

    const data = await response.json().catch(() => ({}));
    if (response.ok) {
      return data;
    }

    if (response.status === 401 && baseUrl !== DEFAULT_API_BASE_URL) {
      continue;
    }

    throw new Error(data.detail || data.message || `API error ${response.status}`);
  }

  throw new Error('The Omani cuisine AI is unavailable right now. Please try again in a moment.');
}

export const getDishes = (search = '', region = '') => {
  const params = new URLSearchParams();
  if (search) params.set('search', search);
  if (region) params.set('region', region);
  const query = params.toString();
  return apiRequest(`/dishes${query ? `?${query}` : ''}`);
};
export const getDish = (id) => apiRequest(`/dishes/${id}`);
export const getNutrition = (id) => apiRequest(`/nutrition/${id}`);
export const getAnalytics = () => apiRequest('/analytics');
export const askFoodAssistant = (message) => apiRequest('/assistant/chat', { method: 'POST', body: JSON.stringify({ message }) });
export const getRecommendations = (criteria) => apiRequest('/recommendations', { method: 'POST', body: JSON.stringify(criteria) });
export const recognizeFood = (file) => {
  const form = new FormData();
  form.append('file', file);
  return apiRequest('/recognize', { method: 'POST', body: form });
};
