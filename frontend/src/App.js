// src/App.js (Corrected: Uses ONLY AuthContext for state)
import React from 'react'; // Removed useState, useEffect imports
import { useAuth } from './context/AuthContext'; // *** Use context hook ***

// Import Page components
import LoginPage from './pages/LoginPage';
import HomePage from './pages/HomePage';

import './App.css';

function App() {
    // *** Get user and loading state ONLY from Context ***
    const { currentUser, isLoading } = useAuth();

    // Show loading indicator provided by AuthContext
    if (isLoading) {
        return <div style={{textAlign: 'center', padding: '50px', fontSize: '1.2em'}}>Loading Application...</div>;
    }

    return (
        <div className="App">
            <header className="App-header">
                {/* Show title based on login state from context */}
                <h1>{currentUser ? "Sports Management Dashboard" : "Sports Management Portal - Login"}</h1>
            </header>
            <main>
                {/*
                   Conditionally render the page based on whether
                   currentUser exists in the AuthContext state.
                */}
                {!currentUser ? (
                    // If no user in context, show Login Page
                    // LoginPage uses context's login function, needs no props here
                    <LoginPage />
                ) : (
                    // If user exists in context, show Home Page
                    // HomePage uses context's currentUser and logout, needs no props here
                    <HomePage />
                )}
            </main>
        </div>
    );
}

export default App;