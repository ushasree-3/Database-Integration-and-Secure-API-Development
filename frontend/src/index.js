import React from 'react';
import ReactDOM from 'react-dom/client';
import './index.css';
import App from './App';
import { AuthProvider } from './context/AuthContext';

const root = ReactDOM.createRoot(document.getElementById('root'));
root.render(
    // Removed StrictMode temporarily based on previous issues, add back later if desired
    // <React.StrictMode>
        <AuthProvider> {/* *** WRAP App here *** */}
            <App />
        </AuthProvider>
    // </React.StrictMode>
);

