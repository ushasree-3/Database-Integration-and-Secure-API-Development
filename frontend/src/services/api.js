// src/services/api.js
import axios from 'axios';

// Assuming apiClient is configured with interceptor for token
const apiClient = axios.create({ baseURL: 'http://localhost:5001', /* ... headers */ });

apiClient.interceptors.request.use(
    (config) => {
        const token = localStorage.getItem('session_token');
        if (token) { config.headers['Authorization'] = `Bearer ${token}`; }
        return config;
    }, (error) => Promise.reject(error)
);

// ... other functions like loginUser ...
export const getMyProfile = () => apiClient.get('/profile/me');
export const getGroupMembers = () => apiClient.get('/members/my_group');

// ... other service functions ...