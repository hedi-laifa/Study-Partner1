import axios from 'axios';

const apiClient = axios.create({
  baseURL: import.meta.env.VITE_API_URL || 'http://localhost:8000/api',
});

apiClient.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('token');
    if (token && config.headers) {
      config.headers.Authorization = `Bearer ${token}`;
    }

    let userId = localStorage.getItem('userId');
    if (!userId && token) {
      const match = token.match(/\d+/);
      if (match) {
        userId = match[0];
      }
    }
    if (!userId) {
      userId = '1';
    }

    if (config.headers) {
      config.headers['X-User-Id'] = userId;
    }

    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

export default apiClient;
