// src/pages/LoginPage.js (No Router Version)
import React, { useState } from 'react';
import axios from 'axios';
// REMOVED: import { useNavigate } from 'react-router-dom';

const API_URL = 'http://localhost:5001';

function LoginPage({ onLoginSuccess }) { // Needs prop to update App state
    const [userId, setUserId] = useState('');
    const [password, setPassword] = useState('');
    const [error, setError] = useState('');
    const [isLoading, setIsLoading] = useState(false);
    // REMOVED: const navigate = useNavigate();

    const handleLogin = async (event) => {
        event.preventDefault();
        setError('');
        setIsLoading(true);

        try {
            const response = await axios.post(`${API_URL}/login`, { user: userId, password: password });
            if (response.data && response.data.session_token) {
                const newToken = response.data.session_token;
                console.log("Login successful:", response.data);
                localStorage.setItem('session_token', newToken);
                if (onLoginSuccess) {
                    onLoginSuccess(newToken); // Update App state *** THIS CAUSES THE RENDER CHANGE ***
                }
                // REMOVED: navigate('/dashboard', { replace: true, state: { token: newToken } });
            } else {
                setError('Login successful, but no token received.');
            }
        } catch (err) {
            console.error("Login error:", err);
             if (err.response) { setError(err.response.data?.error || `Login failed: ${err.response.status}`);}
             else if (err.request) { setError('Network error or server is down.');}
             else { setError('Login error occurred.');}
        } finally {
            setIsLoading(false);
        }
    };

    return (
        // JSX remains the same
        <div style={styles.container}>
            <h2>Login</h2>
            <form onSubmit={handleLogin} style={styles.form}>
                 {/* Input fields */}
                 <div style={styles.inputGroup}> <label htmlFor="userId" style={styles.label}>Member ID:</label> <input type="text" id="userId" value={userId} onChange={(e) => setUserId(e.target.value)} required style={styles.input} autoComplete="username"/> </div>
                 <div style={styles.inputGroup}> <label htmlFor="password" style={styles.label}>Password:</label> <input type="password" id="password" value={password} onChange={(e) => setPassword(e.target.value)} required style={styles.input} autoComplete="current-password"/> </div>
                 {error && <p style={styles.error}>{error}</p>}
                 <button type="submit" disabled={isLoading} style={styles.button}> {isLoading ? 'Logging in...' : 'Login'} </button>
            </form>
        </div>
    );
}
// Styles remain the same
const styles = { container: { display: 'flex', flexDirection: 'column', alignItems: 'center', padding: '20px' }, form: { display: 'flex', flexDirection: 'column', width: '300px', gap: '15px' }, inputGroup: { display: 'flex', flexDirection: 'column', width: '100%' }, label: { marginBottom: '5px', fontWeight: 'bold' }, input: { padding: '10px', border: '1px solid #ccc', borderRadius: '4px' }, button: { padding: '10px 15px', backgroundColor: '#6a1b9a', color: 'white', border: 'none', borderRadius: '4px', cursor: 'pointer', fontSize: '16px' }, error: { color: 'red', marginTop: '10px', textAlign: 'center' } };
export default LoginPage;