import React, { useState, useContext } from 'react';
import { useNavigate } from 'react-router-dom';
import { login } from '../api';
import { AuthContext } from '../AuthContext';
import { Shield } from 'lucide-react';

export default function Login() {
    const [username, setUsername] = useState('');
    const [password, setPassword] = useState('password123');
    const [error, setError] = useState('');
    const navigate = useNavigate();
    const { login: setAuthContext } = useContext(AuthContext);

    const handleSubmit = async (e) => {
        e.preventDefault();
        try {
            const data = await login(username, password);
            setAuthContext(data.access_token, { username, role: '...' }); // me endpoint handles actual role
            window.location.href = '/';
        } catch (err) {
            setError('Invalid credentials');
        }
    };

    return (
        <div className="min-h-screen flex items-center justify-center bg-gray-100 px-4">
            <div className="max-w-md w-full bg-white rounded-lg shadow-lg p-8">
                <div className="flex justify-center mb-6">
                    <Shield className="w-16 h-16 text-blue-600" />
                </div>
                <h2 className="text-2xl font-bold text-center text-gray-900 mb-8">Sign in to HealthChain</h2>
                {error && <div className="bg-red-50 text-red-500 p-3 rounded mb-4 text-sm">{error}</div>}
                <form onSubmit={handleSubmit} className="space-y-6">
                    <div>
                        <label className="block text-sm font-medium text-gray-700">Username</label>
                        <input type="text" value={username} onChange={e => setUsername(e.target.value)} className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 p-2 border" required />
                    </div>
                    <div>
                        <label className="block text-sm font-medium text-gray-700">Password</label>
                        <input type="password" value={password} onChange={e => setPassword(e.target.value)} className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 p-2 border" required />
                    </div>
                    <button type="submit" className="w-full flex justify-center py-2 px-4 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500">
                        Sign in
                    </button>
                </form>
                <div className="mt-6 text-sm text-center text-gray-500">
                    Default Admin: admin / password123 (Create others via Dashboard)
                </div>
            </div>
        </div>
    );
}
