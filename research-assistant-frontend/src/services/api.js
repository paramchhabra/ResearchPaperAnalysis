// src/services/api.js

import axios from 'axios';

// Create an Axios instance
const apiClient = axios.create({
  baseURL: 'http://127.0.0.1:8000', // Your FastAPI server URL
  headers: {
    'Content-Type': 'application/json',
  },
});

// Add a request interceptor to include the token in headers
apiClient.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('authToken');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Define API calls
export const loginUser = (credentials) => {
  return apiClient.post('/login', credentials);
};

export const signupUser = (userData) => {
  return apiClient.post('/signup', userData);
};

export const postChatMessage = (message) => {
  return apiClient.post('/chat/', { message });
};

export default apiClient;