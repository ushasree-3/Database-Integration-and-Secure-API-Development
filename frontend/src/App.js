// src/App.js
import React, { useState, useEffect } from 'react';
import LoginPage from './pages/LoginPage'; // Import the LoginPage component
import './App.css'; // Keep default styling or add your own

function App() {
  // State to hold the authentication token
  const [token, setToken] = useState(null);

  // Check localStorage for an existing token when the app loads
  useEffect(() => {
    const storedToken = localStorage.getItem('session_token');
    if (storedToken) {
      // TODO: Add validation here - ideally call an API endpoint like /verify_token
      //       to ensure the token is still valid on the server before setting it.
      //       For now, we just assume it's valid if it exists.
      console.log("Found token in storage:", storedToken.substring(0, 10) + "...");
      setToken(storedToken);
    }
  }, []); // Empty dependency array means this runs only once on mount

  // Callback function passed to LoginPage to update token state on success
  const handleLoginSuccess = (newToken) => {
    console.log("Login successful in App.js, setting token.");
    setToken(newToken);
    // Note: LoginPage already saves it to localStorage
  };

  // Function to handle logout
  const handleLogout = () => {
    console.log("Logging out.");
    localStorage.removeItem('session_token'); // Remove token from storage
    setToken(null); // Clear token state
  };

  return (
    <div className="App">
      <header className="App-header">
        <h1>Sports Management Portal</h1>
      </header>
      <main>
        {/* Conditionally render Login page or main content */}
        {!token ? (
          // If no token, show the Login Page
          <LoginPage onLoginSuccess={handleLoginSuccess} />
        ) : (
          // If token exists, show logged-in content (placeholder for now)
          <div>
            <h2>Welcome!</h2>
            <p>You are logged in.</p>
            <p>Your token (first 10 chars): {token.substring(0, 10)}...</p>
            {/* Add links or components for other features here */}
            {/* Example: <TeamList token={token} /> */}
            <button onClick={handleLogout} style={{ marginTop: '20px', padding: '8px 15px' }}>
              Logout
            </button>
          </div>
        )}
      </main>
    </div>
  );
}

export default App;