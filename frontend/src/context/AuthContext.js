// src/context/AuthContext.js
import React, { createContext, useState, useEffect, useContext } from 'react';
import { loginUser, getCurrentUser } from '../services/api'; // Assuming getCurrentUser exists in api.js
import {jwtDecode} from 'jwt-decode'; // Need this if getCurrentUser only decodes locally

// Create the context object
const AuthContext = createContext(null);

// Create the Provider component
export const AuthProvider = ({ children }) => {
    // State to hold the currently logged-in user object (or null)
    // User object might include { sub (MemberID), role, UserName, emailID, ID, DoB, etc. }
    const [currentUser, setCurrentUser] = useState(null);
    // Loading state to prevent rendering based on null user during initial check
    const [isLoading, setIsLoading] = useState(true);

    // Effect to check for existing token and validate session on initial app load
    useEffect(() => {
        const validateSession = async () => {
            setIsLoading(true);
            const token = localStorage.getItem('session_token');
            if (token) {
                try {
                    // OPTION 1 (Recommended): Use getCurrentUser if it validates token AND fetches profile
                    const user = await getCurrentUser(); // Assumes this function validates & fetches combined user data
                    setCurrentUser(user); // Will be user object or null if validation failed

                    // OPTION 2 (If getCurrentUser only decodes): Validate then Fetch Separately
                    // const decoded = jwtDecode(token);
                    // const now = Date.now() / 1000;
                    // if (decoded.exp < now) { // Basic expiry check
                    //    throw new Error("Token expired");
                    // }
                    // // TODO: Ideally call backend /verify endpoint here
                    // // If validation passes (local or server):
                    // const profileResponse = await getMyProfile(); // Assuming getMyProfile in api.js
                    // setCurrentUser({ ...decoded, ...profileResponse.data });

                } catch (error) {
                    console.error("Session validation error:", error);
                    localStorage.removeItem('session_token'); // Remove invalid/expired token
                    setCurrentUser(null);
                }
            } else {
                setCurrentUser(null); // No token found
            }
            setIsLoading(false);
        };
        validateSession();
    }, []); // Empty dependency array means run only once on initial mount

    // Login function - calls API, updates state and storage
    const login = async (credentials) => {
        // Clear previous state before attempting login
        setCurrentUser(null);
        localStorage.removeItem('session_token');
        try {
             const loginResponse = await loginUser(credentials); // Call actual login API
             if (loginResponse.data && loginResponse.data.session_token) {
                const token = loginResponse.data.session_token;
                localStorage.setItem('session_token', token); // Store new token
                // Fetch full user details after successful login
                const user = await getCurrentUser(); // Fetch details using the new token
                setCurrentUser(user);
                // Return success or user data if needed by caller
                return user;
             } else {
                 throw new Error("No session token received from login.");
             }
        } catch(error){
             console.error("Login failed in AuthContext:", error);
             setCurrentUser(null); // Ensure user is null on failure
             localStorage.removeItem('session_token'); // Clean up failed attempt
             throw error; // Re-throw for LoginPage/caller to handle UI display
        }
    };

    // Logout function
    const logout = () => {
        console.log("AuthContext: Attempting logout...");
        try {
            localStorage.removeItem('session_token');
            console.log("AuthContext: Token removed from localStorage.");
            setCurrentUser(null); // Attempt to set state to null
            console.log("AuthContext: setCurrentUser(null) called.");
        } catch (error) {
            console.error("!!! Error during logout state update:", error);
        }
    };

    // Value provided to consuming components
    // Pass down the current user, loading state, and login/logout functions
    const value = {
        currentUser,
        isLoading,
        login,
        logout
    };

    // Render children only when initial loading/validation is complete
    return (
        <AuthContext.Provider value={value}>
            {!isLoading && children}
        </AuthContext.Provider>
    );
};

// Custom hook to easily consume the context in other components
export const useAuth = () => {
    const context = useContext(AuthContext);
    if (context === undefined) {
        throw new Error('useAuth must be used within an AuthProvider');
    }
    return context;
};