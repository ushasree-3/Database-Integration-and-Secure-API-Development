// src/LoginPage.js
import React, { useState } from 'react';
import axios from 'axios'; // Import axios

// Define the URL of your Flask API backend
const API_URL = 'http://localhost:5001'; // Make sure this matches where your Flask app runs

function LoginPage({ onLoginSuccess }) { // Receive a function prop to notify parent on success
    const [userId, setUserId] = useState(''); // State for MemberID input
    const [password, setPassword] = useState(''); // State for password input
    const [error, setError] = useState('');     // State for displaying login errors
    const [isLoading, setIsLoading] = useState(false); // State to show loading indicator

    const handleLogin = async (event) => {
        event.preventDefault(); // Prevent default form submission page reload
        setError(''); // Clear previous errors
        setIsLoading(true); // Show loading indicator

        try {
            // --- Make the API call to YOUR Flask /login endpoint ---
            const response = await axios.post(`${API_URL}/login`, {
                user: userId, // Use 'user' as the key, expecting MemberID
                password: password
            });

            // --- Handle SUCCESS ---
            if (response.data && response.data.session_token) {
                console.log("Login successful:", response.data);
                // Store the token (e.g., in localStorage for persistence)
                localStorage.setItem('session_token', response.data.session_token);
                // Notify the parent component (App.js) that login was successful
                if (onLoginSuccess) {
                    onLoginSuccess(response.data.session_token);
                }
            } else {
                // Handle unexpected success response format
                setError('Login successful, but no token received. Please contact support.');
                console.error("Unexpected success response:", response.data);
            }

        } catch (err) {
            // --- Handle ERRORS ---
            console.error("Login error:", err);
            if (err.response) {
                // The request was made and the server responded with a status code
                // that falls out of the range of 2xx
                console.error("Error response data:", err.response.data);
                console.error("Error response status:", err.response.status);
                // Set a user-friendly error message based on server response
                setError(err.response.data.error || `Login failed with status: ${err.response.status}`);
            } else if (err.request) {
                // The request was made but no response was received (e.g., network error, backend down)
                console.error("Error request:", err.request);
                setError('Network error or server is down. Please try again later.');
            } else {
                // Something happened in setting up the request that triggered an Error
                console.error('Error message:', err.message);
                setError('An unexpected error occurred during login.');
            }
        } finally {
            setIsLoading(false); // Hide loading indicator regardless of outcome
        }
    };

    return (
        <div style={styles.container}>
            <h2>Login</h2>
            <form onSubmit={handleLogin} style={styles.form}>
                <div style={styles.inputGroup}>
                    <label htmlFor="userId" style={styles.label}>Member ID:</label>
                    <input
                        type="text"
                        id="userId"
                        value={userId}
                        onChange={(e) => setUserId(e.target.value)}
                        required
                        style={styles.input}
                        autoComplete="username" // Helps browsers with autofill
                    />
                </div>
                <div style={styles.inputGroup}>
                    <label htmlFor="password" style={styles.label}>Password:</label>
                    <input
                        type="password"
                        id="password"
                        value={password}
                        onChange={(e) => setPassword(e.target.value)}
                        required
                        style={styles.input}
                        autoComplete="current-password"
                    />
                </div>
                {error && <p style={styles.error}>{error}</p>} {/* Display error messages */}
                <button type="submit" disabled={isLoading} style={styles.button}>
                    {isLoading ? 'Logging in...' : 'Login'}
                </button>
            </form>
        </div>
    );
}

// Basic inline styles (consider using CSS files for larger apps)
const styles = {
    container: { display: 'flex', flexDirection: 'column', alignItems: 'center', padding: '20px' },
    form: { display: 'flex', flexDirection: 'column', width: '300px', gap: '15px' },
    inputGroup: { display: 'flex', flexDirection: 'column', width: '100%' },
    label: { marginBottom: '5px', fontWeight: 'bold' },
    input: { padding: '10px', border: '1px solid #ccc', borderRadius: '4px' },
    button: { padding: '10px 15px', backgroundColor: '#007bff', color: 'white', border: 'none', borderRadius: '4px', cursor: 'pointer', fontSize: '16px' },
    error: { color: 'red', marginTop: '10px', textAlign: 'center' }
};

export default LoginPage;