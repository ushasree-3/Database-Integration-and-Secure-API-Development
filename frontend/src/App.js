// src/App.js (No Router Version)
import React, { useState, useEffect } from 'react';
import LoginPage from './pages/LoginPage';   // Assuming LoginPage is in pages folder
import HomePage from './pages/HomePage';     // Assuming HomePage is in pages folder
import './App.css';

function App() {
    const [token, setToken] = useState(null);
    const [isLoading, setIsLoading] = useState(true); // Still useful

    // Check localStorage on initial load
    useEffect(() => {
        const storedToken = localStorage.getItem('session_token');
        if (storedToken) {
            console.log("App Mount: Found token:", storedToken.substring(0, 10) + "...");
            // TODO: Ideally validate token with backend here
            setToken(storedToken);
        }
        setIsLoading(false);
    }, []);

    // Login success handler - just updates token state
    const handleLoginSuccess = (newToken) => {
        console.log("App.js: handleLoginSuccess called, setting token.");
        setToken(newToken);
    };

    // Logout handler
    const handleLogout = () => {
        console.log("App.js: handleLogout called.");
        localStorage.removeItem('session_token');
        setToken(null);
    };

    if (isLoading) {
        return <div>Loading...</div>;
    }

    return (
        <div className="App">
            <header className="App-header">
                {/* Show title based on login state */}
                <h1>{token ? "Sports Management Dashboard" : "Sports Management Portal"}</h1>
            </header>
            <main>
                {/* Conditionally render the entire page component */}
                {!token ? (
                    <LoginPage onLoginSuccess={handleLoginSuccess} />
                ) : (
                    <HomePage token={token} onLogout={handleLogout} />
                )}
            </main>
        </div>
    );
}

export default App;