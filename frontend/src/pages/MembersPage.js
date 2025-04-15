// src/pages/MembersPage.js
import React, { useState, useEffect } from 'react';
import { getGroupMembers } from '../services/api';
import EditMemberForm from '../components/EditMemberForm'; // Import the form
import { useAuth } from '../context/AuthContext'; // Import useAuth to check role

// ... (keep existing styles object) ...
const styles = { /* ... styles from previous MembersPage ... */
    editButton: { // Style for the edit button
        marginLeft: '10px',
        padding: '4px 8px',
        fontSize: '0.8em',
        cursor: 'pointer',
        backgroundColor: '#ff9800', // Orange
        color: 'white',
        border: 'none',
        borderRadius: '3px',
    }
};


function MembersPage() {
    const [members, setMembers] = useState([]);
    const [isLoading, setIsLoading] = useState(true);
    const [error, setError] = useState('');
    const { currentUser } = useAuth(); // Get current user to check role

    // State for editing
    const [editingMember, setEditingMember] = useState(null); // Store the member being edited
    const [showEditForm, setShowEditForm] = useState(false);

    const isAdmin = currentUser?.role === 'admin'; // Check if logged-in user is admin

    // Fetch members function (keep as before)
    const fetchMembers = async () => {
        setIsLoading(true);
        setError('');
        try {
            const response = await getGroupMembers();
            setMembers(response.data || []);
        } catch (err) { /* ... error handling ... */ }
        finally { setIsLoading(false); }
    };

    useEffect(() => {
        fetchMembers(); // Fetch on mount
    }, []);

    // --- Edit Handlers ---
    const handleEditClick = (member) => {
        setEditingMember(member); // Set the member to edit
        setShowEditForm(true);    // Show the form/modal
    };

    const handleEditCancel = () => {
        setShowEditForm(false);    // Hide the form
        setEditingMember(null);    // Clear editing state
    };

    const handleEditSave = (updatedMember) => {
        // Update the list in the state visually
        setMembers(prevMembers =>
            prevMembers.map(m => m.ID === updatedMember.ID ? updatedMember : m)
        );
        setShowEditForm(false);    // Hide the form
        setEditingMember(null);    // Clear editing state
        alert(`Member ${updatedMember.UserName} updated successfully!`); // Simple feedback
        // Optionally re-fetch the whole list: fetchMembers();
    };
    // --- End Edit Handlers ---

    return (
        <div style={styles.container}>
            <h2>Group 2 Members</h2>
            {isLoading && <p style={styles.loading}>Loading members...</p>}
            {error && <p style={styles.error}>{error}</p>}
            {/* ... (No members found message) ... */}

            {!isLoading && !error && members.length > 0 && (
                <table style={styles.table}>
                    <thead>
                        <tr>
                            <th style={styles.th}>ID</th>
                            <th style={styles.th}>Username</th>
                            <th style={styles.th}>Email</th>
                            <th style={styles.th}>Date of Birth</th>
                            {isAdmin && <th style={styles.th}>Actions</th>} {/* Action column for Admin */}
                        </tr>
                    </thead>
                    <tbody>
                        {members.map((member, index) => (
                            <tr key={member.ID} style={index % 2 !== 0 ? styles.trOdd : {}}>
                                <td style={styles.td}>{member.ID}</td>
                                <td style={styles.td}>{member.UserName}</td>
                                <td style={styles.td}>{member.emailID}</td>
                                <td style={styles.td}>{member.DoB ? new Date(member.DoB).toLocaleDateString() : 'N/A'}</td>
                                {/* Render Edit button only for Admins */}
                                {isAdmin && (
                                    <td style={styles.td}>
                                        <button
                                            onClick={() => handleEditClick(member)}
                                            style={styles.editButton}
                                        >
                                            Edit
                                        </button>
                                    </td>
                                )}
                            </tr>
                        ))}
                    </tbody>
                </table>
            )}

            {/* Conditionally render the Edit Form as an overlay/modal */}
            {showEditForm && (
                <EditMemberForm
                    memberToEdit={editingMember}
                    onSave={handleEditSave}
                    onCancel={handleEditCancel}
                />
            )}
        </div>
    );
}

export default MembersPage;