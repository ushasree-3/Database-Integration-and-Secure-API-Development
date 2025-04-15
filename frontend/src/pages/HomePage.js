// src/pages/HomePage.js (No Router Version)
import React from 'react';
// REMOVED: import { Link } from 'react-router-dom';

// ... styles ...

function HomePage({ token, onLogout }) { // Still needs token and logout
    return (
        <div style={styles.container}>
            {/* ... Background image logic if you added it ... */}
            <h1 style={styles.title}>Welcome Home!</h1>
            <p>You are successfully logged in.</p>
            {token && <p>Token starts with: {token.substring(0, 15)}...</p>}
            <button onClick={onLogout} style={{ marginTop: '20px', padding: '8px 15px' }}>
                Logout
            </button>
            <hr style={{ margin: '30px 0' }} />
            <h2>Dashboard Area</h2>
            <p>(Content for managing Teams, Events, etc. would be added here directly or via conditionally rendered components based on state, not separate routes)</p>
            {/* Example: <button>Manage Teams</button> <button>Manage Events</button> */}
        </div>
    );
}
const styles = { container: { padding: '20px' }, title: { color: '#4a148c' }}; // Simplified styles
export default HomePage;