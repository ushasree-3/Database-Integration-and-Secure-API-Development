// src/pages/HomePage.js
import React, { useState } from 'react'; // Import useState
import MembersPage from './MembersPage'; // Import the new component

// Basic styles (inline for simplicity)
const styles = {
    container: { padding: '20px' },
    pageTitle: { color: '#444', fontSize: '1.5em', textAlign: 'center', marginBottom: '25px', fontWeight: '600' },
    actionButton: {
        display: 'inline-block', padding: '12px 20px', margin: '10px', fontSize: '1em',
        cursor: 'pointer', border: 'none', borderRadius: '5px', color: 'white',
        background: 'linear-gradient(45deg, #5e35b1, #7e57c2)', textAlign: 'center',
        textDecoration: 'none', boxShadow: '0 2px 4px rgba(0,0,0,0.15)',
        transition: 'background-color 0.2s ease, transform 0.1s ease',
    },
    logoutButton: {
        marginTop: '40px', padding: '8px 15px', cursor: 'pointer', backgroundColor: '#d32f2f',
        color: 'white', border: 'none', borderRadius: '4px',
    },
    viewMembersContainer: { // Style for the container holding the members table
        marginTop: '30px',
        borderTop: '1px solid #ccc',
        paddingTop: '20px'
    }
};

// Receive onLogout prop from App.js (non-context version)
function HomePage({ onLogout }) {
    // State to control visibility of MembersPage
    const [showMembers, setShowMembers] = useState(false);

    const handleViewMembersToggle = () => {
        // Simply toggle the boolean state
        setShowMembers(prevShow => !prevShow);
    };

    return (
        <div style={styles.container}>
            <h2 style={styles.pageTitle}>Sports Management Dashboard</h2>

            {/* Action buttons */}
            <div>
                {/* Modified View Members button to toggle state */}
                <button onClick={handleViewMembersToggle} style={styles.actionButton}>
                    {showMembers ? 'Hide Members' : 'View Group Members'}
                </button>
                <button onClick={() => alert('Manage Teams not implemented')} style={styles.actionButton}>
                    Manage Teams
                </button>
                <button onClick={() => alert('Manage Events not implemented')} style={styles.actionButton}>
                    Manage Events
                </button>
                <button onClick={() => alert('Manage Equipment not implemented')} style={styles.actionButton}>
                    Manage Equipment
                </button>
                {/* Add more placeholder buttons */}
            </div>

            {/* Conditionally render the MembersPage component */}
            {showMembers && (
                <div style={styles.viewMembersContainer}>
                    <MembersPage />
                </div>
            )}

            {/* Logout Button */}
            <div style={{ marginTop: '50px', textAlign: 'center' }}>
                <button onClick={onLogout} style={styles.logoutButton}>
                    Logout
                </button>
            </div>
        </div>
    );
}

export default HomePage;