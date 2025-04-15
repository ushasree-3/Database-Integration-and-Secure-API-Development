// src/pages/MembersPage.js
import React, { useState, useEffect } from 'react';
import { getGroupMembers } from '../services/api'; // Import API function

// Styles for the table
const styles = {
    table: {
        marginTop: '20px',
        width: '100%',
        maxWidth: '800px', // Limit table width
        margin: '20px auto', // Center table
        borderCollapse: 'collapse',
        boxShadow: '0 1px 3px rgba(0,0,0,0.1)',
    },
    th: {
        backgroundColor: '#7e57c2', // Violet
        color: 'white',
        padding: '12px 15px',
        textAlign: 'left',
        borderBottom: '2px solid #5e35b1', // Deeper violet
    },
    td: {
        padding: '10px 15px',
        borderBottom: '1px solid #eee',
    },
    // Basic alternating row color
    trOdd: {
        backgroundColor: '#f9f9f9'
    },
    loading: { textAlign: 'center', margin: '20px', fontStyle: 'italic', color: '#777'},
    error: { textAlign: 'center', margin: '20px', color: 'red'},
    container: { padding: '10px'} // Add padding around the table area
};


function MembersPage() {
    const [members, setMembers] = useState([]);
    const [isLoading, setIsLoading] = useState(true); // Start loading true
    const [error, setError] = useState('');

    useEffect(() => {
        // Fetch members when the component mounts
        const fetchMembers = async () => {
            setIsLoading(true);
            setError('');
            try {
                const response = await getGroupMembers();
                setMembers(response.data || []);
            } catch (err) {
                console.error("Error fetching group members:", err);
                const errorMsg = err.response?.data?.error || err.message || "Could not fetch members";
                setError(`Error: ${errorMsg}`);
                setMembers([]); // Clear members on error
            } finally {
                setIsLoading(false);
            }
        };

        fetchMembers();
    }, []); // Empty dependency array means run only once on mount

    return (
        <div style={styles.container}>
            <h2>Group 2 Members</h2>
            {isLoading && <p style={styles.loading}>Loading members...</p>}
            {error && <p style={styles.error}>{error}</p>}
            {!isLoading && !error && members.length === 0 && (
                <p>No members found in this group.</p>
            )}
            {!isLoading && !error && members.length > 0 && (
                <table style={styles.table}>
                    <thead>
                        <tr>
                            <th style={styles.th}>ID</th>
                            <th style={styles.th}>Username</th>
                            <th style={styles.th}>Email</th>
                            <th style={styles.th}>Date of Birth</th>
                        </tr>
                    </thead>
                    <tbody>
                        {members.map((member, index) => (
                            <tr key={member.ID} style={index % 2 !== 0 ? styles.trOdd : {}}>
                                <td style={styles.td}>{member.ID}</td>
                                <td style={styles.td}>{member.UserName}</td>
                                <td style={styles.td}>{member.emailID}</td>
                                <td style={styles.td}>{member.DoB ? new Date(member.DoB).toLocaleDateString() : 'N/A'}</td>
                            </tr>
                        ))}
                    </tbody>
                </table>
            )}
        </div>
    );
}

export default MembersPage;