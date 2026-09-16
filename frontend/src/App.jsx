import React, { useContext } from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider, AuthContext } from './AuthContext';
import Layout from './Layout';
import Login from './pages/Login';
import Dashboard from './pages/Dashboard';
import Records from './pages/Records';
import Integrity from './pages/Integrity';
import Blockchain from './pages/Blockchain';
import Sharing from './pages/Sharing';
import AuditLogs from './pages/AuditLogs';

function ProtectedRoute({ children }) {
    const { user, loading } = useContext(AuthContext);
    if (loading) return <div>Loading session...</div>;
    if (!user) return <Navigate to="/login" />;
    return children;
}

export default function App() {
    return (
        <AuthProvider>
            <BrowserRouter>
                <Routes>
                    <Route path="/login" element={<Login />} />
                    <Route path="/" element={<ProtectedRoute><Layout /></ProtectedRoute>}>
                        <Route index element={<Dashboard />} />
                        <Route path="records" element={<Records />} />
                        <Route path="integrity" element={<Integrity />} />
                        <Route path="blockchain" element={<Blockchain />} />
                        <Route path="sharing" element={<Sharing />} />
                        <Route path="audit" element={<AuditLogs />} />
                    </Route>
                </Routes>
            </BrowserRouter>
        </AuthProvider>
    );
}
