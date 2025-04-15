// src/components/EditMemberForm.js
import React, { useState, useEffect } from 'react';
import { updateMemberAdmin } from '../services/api'; // API function

// Basic styles (inline for simplicity)
const styles = {
    formOverlay: {
        position: 'fixed', top: 0, left: 0, right: 0, bottom: 0,
        backgroundColor: 'rgba(0, 0, 0, 0.6)', display: 'flex',
        alignItems: 'center', justifyContent: 'center', zIndex: 1000,
    },
    formContainer: {
        background: 'white', padding: '30px', borderRadius: '8px',
        boxShadow: '0 5px 15px rgba(0,0,0,0.2)', width: '90%', maxWidth: '500px',
    },
    form: { display: 'flex', flexDirection: 'column', gap: '15px' },
    inputGroup: { display: 'flex', flexDirection: 'column', width: '100%' },
    label: { marginBottom: '5px', fontWeight: 'bold', color: '#555' },
    input: { padding: '10px', border: '1px solid #ccc', borderRadius: '4px', fontSize: '1em' },
    buttonContainer: { display: 'flex', justifyContent: 'flex-end', gap: '10px', marginTop: '20px' },
    button: { padding: '10px 15px', border: 'none', borderRadius: '4px', cursor: 'pointer', fontSize: '1em'},
    saveButton: { backgroundColor: '#4CAF50', color: 'white' }, // Green
    cancelButton: { backgroundColor: '#f44336', color: 'white' }, // Red
    error: { color: 'red', marginTop: '10px' }
};

function EditMemberForm({ memberToEdit, onSave, onCancel }) {
    // State for form fields, pre-filled with member data
    const [userName, setUserName] = useState('');
    const [emailID, setEmailID] = useState('');
    const [dob, setDob] = useState(''); // Store as YYYY-MM-DD string

    const [isLoading, setIsLoading] = useState(false);
    const [error, setError] = useState('');

    // Pre-fill form when memberToEdit changes or loads
    useEffect(() => {
        if (memberToEdit) {
            setUserName(memberToEdit.UserName || '');
            setEmailID(memberToEdit.emailID || '');
            // Format date correctly for input type="date"
            const formattedDob = memberToEdit.DoB ? new Date(memberToEdit.DoB).toISOString().split('T')[0] : '';
            setDob(formattedDob);
            setError(''); // Clear error when new member is loaded
        }
    }, [memberToEdit]); // Re-run effect if memberToEdit object changes

    const handleSubmit = async (event) => {
        event.preventDefault();
        setIsLoading(true);
        setError('');

        const updatedData = {
            UserName: userName,
            emailID: emailID,
            DoB: dob // Send date string in YYYY-MM-DD format
        };

        try {
            const response = await updateMemberAdmin(memberToEdit.ID, updatedData);
            console.log("Update successful:", response.data);
            onSave(response.data.member); // Pass updated member data back to parent
        } catch (err) {
            console.error("Update member error:", err);
            const errorMsg = err.response?.data?.error || err.message || "Failed to update member";
            setError(`Error: ${errorMsg}`);
        } finally {
            setIsLoading(false);
        }
    };

    // Don't render anything if no member is selected for editing
    if (!memberToEdit) {
        return null;
    }

    return (
        <div style={styles.formOverlay}>
            <div style={styles.formContainer}>
                <h3>Edit Member: {memberToEdit.UserName} (ID: {memberToEdit.ID})</h3>
                <form onSubmit={handleSubmit} style={styles.form}>
                    <div style={styles.inputGroup}>
                        <label htmlFor="editUserName" style={styles.label}>Username:</label>
                        <input
                            type="text" id="editUserName" value={userName}
                            onChange={(e) => setUserName(e.target.value)}
                            required style={styles.input}
                        />
                    </div>
                    <div style={styles.inputGroup}>
                        <label htmlFor="editEmailID" style={styles.label}>Email:</label>
                        <input
                            type="email" id="editEmailID" value={emailID}
                            onChange={(e) => setEmailID(e.target.value)}
                            required style={styles.input}
                        />
                    </div>
                    <div style={styles.inputGroup}>
                        <label htmlFor="editDoB" style={styles.label}>Date of Birth:</label>
                        <input
                            type="date" id="editDoB" value={dob} // Input type="date" needs YYYY-MM-DD
                            onChange={(e) => setDob(e.target.value)}
                            required style={styles.input}
                        />
                    </div>

                    {error && <p style={styles.error}>{error}</p>}

                    <div style={styles.buttonContainer}>
                        <button type="button" onClick={onCancel} disabled={isLoading} style={{...styles.button, ...styles.cancelButton}}>
                            Cancel
                        </button>
                        <button type="submit" disabled={isLoading} style={{...styles.button, ...styles.saveButton}}>
                            {isLoading ? 'Saving...' : 'Save Changes'}
                        </button>
                    </div>
                </form>
            </div>
        </div>
    );
}

export default EditMemberForm;