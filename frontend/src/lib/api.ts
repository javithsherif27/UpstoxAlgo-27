import axios from 'axios';
import { getUpstoxToken, clearUpstoxToken } from './auth';
import { isExpiredEOD } from './time';

// Allow configuring backend base URL via Vite env var VITE_API_BASE
// Default to localhost:8000 for local development
const API_BASE = (import.meta as any)?.env?.VITE_API_BASE || 'http://localhost:8000';

export const apiClient = axios.create({ withCredentials: true, baseURL: API_BASE });

apiClient.interceptors.request.use(config => {
  const tokenEntry = getUpstoxToken();
  if (tokenEntry) {
    if (isExpiredEOD(tokenEntry.expiresAt)) {
      clearUpstoxToken();
      window.location.href = '/login';
      return config;
    }
    config.headers = config.headers || {};
    config.headers['X-Upstox-Access-Token'] = tokenEntry.token;
  }
  return config;
});

apiClient.interceptors.response.use(r => r, err => {
  if (err.response?.status === 401) {
    clearUpstoxToken();
    window.location.href = '/login';
  }
  return Promise.reject(err);
});
