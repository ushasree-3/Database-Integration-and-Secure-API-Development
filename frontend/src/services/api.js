// src/services/api.js
import axios from 'axios';
import {jwtDecode} from 'jwt-decode';

const API_URL = 'http://localhost:5001';
const apiClient = axios.create({ baseURL: 'http://localhost:5001', /* ... headers */ });

apiClient.interceptors.request.use(
    (config) => {
        const token = localStorage.getItem('session_token');
        if (token) { config.headers['Authorization'] = `Bearer ${token}`; }
        return config;
    }, (error) => Promise.reject(error)
);

// --- Login Function ---
export const loginUser = (credentials) => axios.post(`${API_URL}/login`, credentials);

// --- Member Service Functions ---
export const getMyProfile = () => apiClient.get('/profile/me');

// --- Get Current User (Decodes Token + Fetches Profile) ---
export const getCurrentUser = async () => {
    const token = localStorage.getItem('session_token');
    if (!token) {
        console.log("getCurrentUser: No token found");
        return null;
    }
    try {
        // 1. Decode token locally (check expiry)
        const decoded = jwtDecode(token);
        const now = Date.now() / 1000;
        if (decoded.exp < now) {
            console.log("getCurrentUser: Token expired");
            throw new Error("Token expired");
        }
        console.log("getCurrentUser: Token decoded:", decoded);

        // 2. Fetch fresh profile details from backend
        // This implicitly validates the token further on the server via the interceptor
        const profileResponse = await getMyProfile();
        console.log("getCurrentUser: Profile fetched:", profileResponse.data);

        // 3. Combine data
        return {
            sub: decoded.sub, // MemberID as subject
            role: decoded.role,
            iat: decoded.iat,
            exp: decoded.exp,
            ...profileResponse.data // Add ID, UserName, emailID, DoB from profile
        };
    } catch (error) {
        console.error("Error getting current user:", error.message);
        // If token invalid or profile fetch fails, remove token and return null
        localStorage.removeItem('session_token');
        return null;
    }
};

// --- Other Service Functions (Teams, Events, etc.) ---
export const getGroupMembers = () => apiClient.get('/members/my_group');
export const updateMemberAdmin = (memberId, memberData) => apiClient.put(`/admin/members/${memberId}`, memberData);
// ... etc ...