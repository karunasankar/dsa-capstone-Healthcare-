import os

files = {}

files['src/api.js'] = """
const BASE_URL = "http://127.0.0.1:8001";

function getHeaders() {
    const token = localStorage.getItem('token');
    return {
        'Content-Type': 'application/json',
        'Authorization': token ? `Bearer ${token}` : ''
    };
}

export async function login(username, password) {
    const res = await fetch(`${BASE_URL}/auth/login`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ username, password })
    });
    if (!res.ok) throw new Error('Login failed');
    return await res.json();
}

export async function fetchWithAuth(endpoint, options = {}) {
    const res = await fetch(`${BASE_URL}${endpoint}`, {
        ...options,
        headers: getHeaders()
    });
    if (res.status === 401 || res.status === 403) {
        throw new Error(res.status === 401 ? "Unauthorized" : "Forbidden");
    }
    return res;
}
"""

files['src/AuthContext.jsx'] = """
import React, { createContext, useState, useEffect } from 'react';
import { fetchWithAuth } from './api';

export const AuthContext = createContext();

export function AuthProvider({ children }) {
    const [user, setUser] = useState(null);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        const token = localStorage.getItem('token');
        if (token) {
            fetchWithAuth('/auth/me')
                .then(res => res.json())
                .then(data => setUser(data))
                .catch(() => {
                    localStorage.removeItem('token');
                    setUser(null);
                })
                .finally(() => setLoading(false));
        } else {
            setLoading(false);
        }
    }, []);

    const login = (token, userData) => {
        localStorage.setItem('token', token);
        setUser(userData);
    };

    const logout = () => {
        localStorage.removeItem('token');
        setUser(null);
    };

    return (
        <AuthContext.Provider value={{ user, login, logout, loading }}>
            {children}
        </AuthContext.Provider>
    );
}
"""

files['src/Layout.jsx'] = """
import React, { useContext } from 'react';
import { Outlet, Link, useNavigate, useLocation } from 'react-router-dom';
import { AuthContext } from './AuthContext';
import { Shield, Activity, Database, Lock, Share2, FileText, User, LogOut, LayoutDashboard } from 'lucide-react';

export default function Layout() {
    const { user, logout } = useContext(AuthContext);
    const navigate = useNavigate();
    const location = useLocation();

    if (!user) return <Outlet />;

    const navItems = [
        { path: '/', label: 'Dashboard', icon: LayoutDashboard, roles: ['ADMIN', 'DOCTOR', 'LAB', 'PATIENT'] },
        { path: '/records', label: 'Records', icon: Database, roles: ['ADMIN', 'DOCTOR', 'LAB', 'PATIENT'] },
        { path: '/integrity', label: 'Integrity Demo', icon: Shield, roles: ['ADMIN', 'DOCTOR', 'LAB', 'PATIENT'] },
        { path: '/blockchain', label: 'Blockchain Explorer', icon: Activity, roles: ['ADMIN'] },
        { path: '/sharing', label: 'Sharing', icon: Share2, roles: ['PATIENT'] },
        { path: '/audit', label: 'Audit Logs', icon: FileText, roles: ['ADMIN', 'DOCTOR', 'LAB'] }
    ];

    const handleLogout = () => {
        logout();
        navigate('/login');
    };

    return (
        <div className="flex h-screen bg-gray-100">
            <aside className="w-64 bg-gray-900 text-white flex flex-col">
                <div className="p-4 flex items-center gap-3 border-b border-gray-800">
                    <Shield className="w-8 h-8 text-blue-500" />
                    <div>
                        <h1 className="text-xl font-bold">HealthChain</h1>
                        <p className="text-xs text-gray-400">Secure Records</p>
                    </div>
                </div>
                <nav className="flex-1 p-4 space-y-1 overflow-y-auto">
                    {navItems.filter(item => item.roles.includes(user.role)).map(item => {
                        const Icon = item.icon;
                        const isActive = location.pathname === item.path;
                        return (
                            <Link key={item.path} to={item.path} className={`flex items-center gap-3 px-3 py-2 rounded-md transition-colors ${isActive ? 'bg-blue-600 text-white' : 'text-gray-300 hover:bg-gray-800 hover:text-white'}`}>
                                <Icon className="w-5 h-5" />
                                {item.label}
                            </Link>
                        );
                    })}
                </nav>
                <div className="p-4 border-t border-gray-800">
                    <div className="flex items-center gap-3 mb-4">
                        <div className="w-10 h-10 rounded-full bg-gray-700 flex items-center justify-center">
                            <User className="w-6 h-6 text-gray-400" />
                        </div>
                        <div>
                            <p className="text-sm font-medium">{user.username}</p>
                            <p className="text-xs text-gray-400">{user.role}</p>
                        </div>
                    </div>
                    <button onClick={handleLogout} className="flex items-center gap-2 text-sm text-gray-400 hover:text-white transition-colors w-full">
                        <LogOut className="w-4 h-4" />
                        Logout
                    </button>
                </div>
            </aside>
            <main className="flex-1 flex flex-col overflow-hidden">
                <header className="bg-white border-b px-6 py-4 flex justify-between items-center">
                    <h2 className="text-xl font-semibold text-gray-800 capitalize">
                        {location.pathname === '/' ? 'Dashboard' : location.pathname.slice(1)}
                    </h2>
                </header>
                <div className="flex-1 overflow-auto p-6">
                    <Outlet />
                </div>
            </main>
        </div>
    );
}
"""

files['src/pages/Login.jsx'] = """
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
                    Demo accounts: admin, doctor1, lab1, patient1
                </div>
            </div>
        </div>
    );
}
"""

files['src/pages/Dashboard.jsx'] = """
import React, { useEffect, useState } from 'react';
import { fetchWithAuth } from '../api';
import { Database, Link, Share2, Activity, ShieldAlert, ShieldCheck } from 'lucide-react';

export default function Dashboard() {
    const [stats, setStats] = useState(null);

    useEffect(() => {
        fetchWithAuth('/dashboard/stats')
            .then(res => res.json())
            .then(data => setStats(data))
            .catch(err => console.error(err));
    }, []);

    if (!stats) return <div>Loading...</div>;

    const cards = [
        { title: 'Total Records', value: stats.total_records, icon: Database, color: 'text-blue-500' },
        { title: 'Blockchain Blocks', value: stats.blocks, icon: Link, color: 'text-purple-500' },
        { title: 'Active Shares', value: stats.active_shares, icon: Share2, color: 'text-green-500' },
        { title: 'Chain Valid', value: stats.chain_valid ? 'YES' : 'NO', icon: stats.chain_valid ? ShieldCheck : ShieldAlert, color: stats.chain_valid ? 'text-green-500' : 'text-red-500' },
    ];

    return (
        <div className="space-y-6">
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
                {cards.map((card, idx) => (
                    <div key={idx} className="bg-white rounded-lg shadow p-6 flex items-center">
                        <div className={`p-3 rounded-full bg-gray-50 ${card.color} mr-4`}>
                            <card.icon className="w-8 h-8" />
                        </div>
                        <div>
                            <p className="text-sm font-medium text-gray-500">{card.title}</p>
                            <p className="text-2xl font-bold text-gray-900">{card.value}</p>
                        </div>
                    </div>
                ))}
            </div>
            <div className="bg-white rounded-lg shadow p-6">
                <h3 className="text-lg font-medium mb-4">Current Merkle Root</h3>
                <code className="bg-gray-100 p-3 rounded block text-sm break-all">{stats.merkle_root || 'None'}</code>
            </div>
        </div>
    );
}
"""

files['src/pages/Records.jsx'] = """
import React, { useEffect, useState, useContext } from 'react';
import { fetchWithAuth } from '../api';
import { ShieldAlert, ShieldCheck, HelpCircle } from 'lucide-react';
import { AuthContext } from '../AuthContext';

export default function Records() {
    const { user } = useContext(AuthContext);
    const [records, setRecords] = useState([]);
    const [selectedRecord, setSelectedRecord] = useState(null);

    const loadRecords = () => {
        fetchWithAuth('/records')
            .then(res => res.json())
            .then(data => setRecords(data.records))
            .catch(err => console.error(err));
    };

    useEffect(() => {
        loadRecords();
    }, []);

    const verifyRecord = async (id) => {
        try {
            const res = await fetchWithAuth(`/verify/${id}`, { method: 'POST' });
            const data = await res.json();
            alert(`Integrity Status: ${data.status}\\n\\nDetails: ${data.detail || ''}`);
        } catch (err) {
            alert("Verification Failed / Unauthorized");
        }
    };

    const tamperRecord = async (id) => {
        if (!confirm("Simulate Unauthorized Modification? This will corrupt the ciphertext directly.")) return;
        await fetchWithAuth(`/tamper/${id}`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ tampered: true })
        });
        alert('Tampered!');
        loadRecords();
    };

    return (
        <div className="space-y-6">
            <div className="bg-white shadow rounded-lg overflow-hidden">
                <table className="min-w-full divide-y divide-gray-200">
                    <thead className="bg-gray-50">
                        <tr>
                            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">ID</th>
                            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Patient</th>
                            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Type</th>
                            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Status</th>
                            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Actions</th>
                        </tr>
                    </thead>
                    <tbody className="bg-white divide-y divide-gray-200">
                        {records.map(r => {
                            const isError = r.record.record_data?.ERROR;
                            return (
                                <tr key={r.record.record_id}>
                                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500" title={r.record.record_id}>
                                        {r.record.record_id.slice(0,8)}...
                                    </td>
                                    <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">{r.record.patient_id}</td>
                                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{r.record.record_type}</td>
                                    <td className="px-6 py-4 whitespace-nowrap">
                                        {isError ? (
                                            <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-medium bg-red-100 text-red-800">
                                                <ShieldAlert className="w-4 h-4"/> TAMPERED
                                            </span>
                                        ) : (
                                            <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-800">
                                                <ShieldCheck className="w-4 h-4"/> VERIFIED
                                            </span>
                                        )}
                                    </td>
                                    <td className="px-6 py-4 whitespace-nowrap text-sm font-medium space-x-3">
                                        <button onClick={() => setSelectedRecord(r.record)} className="text-blue-600 hover:text-blue-900">View</button>
                                        <button onClick={() => verifyRecord(r.record.record_id)} className="text-indigo-600 hover:text-indigo-900">Verify</button>
                                        {user?.role === 'DOCTOR' && <button onClick={() => tamperRecord(r.record.record_id)} className="text-red-600 hover:text-red-900">Tamper (Demo)</button>}
                                    </td>
                                </tr>
                            );
                        })}
                    </tbody>
                </table>
            </div>

            {selectedRecord && (
                <div className="fixed inset-0 bg-gray-600 bg-opacity-50 flex items-center justify-center p-4">
                    <div className="bg-white rounded-lg shadow-xl max-w-2xl w-full p-6">
                        <h3 className="text-lg font-bold mb-4">Record Details</h3>
                        <div className="space-y-3 text-sm">
                            <p><strong>ID:</strong> {selectedRecord.record_id}</p>
                            <p><strong>Patient:</strong> {selectedRecord.patient_id}</p>
                            <p><strong>Type:</strong> {selectedRecord.record_type}</p>
                            <div className="bg-gray-100 p-4 rounded mt-4">
                                <strong>Decrypted Medical Data:</strong>
                                <pre className="mt-2 text-xs overflow-auto">{JSON.stringify(selectedRecord.record_data, null, 2)}</pre>
                            </div>
                        </div>
                        <div className="mt-6 flex justify-end">
                            <button onClick={() => setSelectedRecord(null)} className="px-4 py-2 bg-gray-200 text-gray-800 rounded hover:bg-gray-300">Close</button>
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
}
"""

files['src/pages/Integrity.jsx'] = """
import React, { useEffect, useState } from 'react';
import { fetchWithAuth } from '../api';
import { ShieldCheck, ArrowDown } from 'lucide-react';

export default function Integrity() {
    const [tree, setTree] = useState(null);

    useEffect(() => {
        fetchWithAuth('/merkle/tree')
            .then(res => res.json())
            .then(data => setTree(data))
            .catch(err => console.error(err));
    }, []);

    if (!tree) return <div>Loading...</div>;

    return (
        <div className="space-y-6">
            <div className="bg-white shadow rounded-lg p-6 text-center">
                <h3 className="text-lg font-bold mb-6">Merkle Tree Verification Flow</h3>
                
                <div className="flex flex-col items-center gap-2 mb-8">
                    <div className="bg-blue-100 text-blue-800 p-3 rounded font-mono text-sm max-w-full break-all border border-blue-200">
                        <strong>Current Root:</strong><br/>{tree.root}
                    </div>
                    <ArrowDown className="text-gray-400" />
                    <div className="bg-purple-100 text-purple-800 p-3 rounded border border-purple-200">
                        Anchored to Blockchain
                    </div>
                </div>

                <div className="overflow-x-auto">
                    <div className="min-w-max inline-flex flex-col items-center gap-6">
                        {[...tree.levels].reverse().map((level, i) => (
                            <div key={i} className="flex gap-4">
                                {level.map((hash, j) => (
                                    <div key={j} className="bg-gray-50 border rounded p-2 text-xs font-mono text-gray-600" title={hash}>
                                        {i === tree.levels.length - 1 ? (tree.record_map[hash] ? `Record: ${tree.record_map[hash].slice(0,6)}` : 'Leaf') : 'Node'}
                                        <br/>
                                        {hash.slice(0, 8)}...
                                    </div>
                                ))}
                            </div>
                        ))}
                    </div>
                </div>
            </div>
        </div>
    );
}
"""

files['src/pages/Blockchain.jsx'] = """
import React, { useEffect, useState } from 'react';
import { fetchWithAuth } from '../api';
import { ShieldCheck, ShieldAlert, Link } from 'lucide-react';

export default function Blockchain() {
    const [chainData, setChainData] = useState(null);

    useEffect(() => {
        fetchWithAuth('/blockchain')
            .then(res => res.json())
            .then(data => setChainData(data))
            .catch(err => console.error(err));
    }, []);

    if (!chainData) return <div>Loading...</div>;

    return (
        <div className="space-y-6">
            <div className={`p-4 rounded-lg flex items-center gap-3 ${chainData.valid ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'}`}>
                {chainData.valid ? <ShieldCheck className="w-6 h-6" /> : <ShieldAlert className="w-6 h-6" />}
                <span className="font-bold text-lg">Blockchain Status: {chainData.valid ? 'VALID' : 'INVALID'}</span>
            </div>

            <div className="space-y-4">
                {chainData.chain.map((block, idx) => (
                    <div key={idx} className="bg-white rounded-lg shadow p-6 relative">
                        {idx !== 0 && <div className="absolute -top-4 left-8 w-1 h-4 bg-gray-300"></div>}
                        <div className="flex items-center gap-2 mb-4">
                            <Link className="text-purple-500" />
                            <h3 className="font-bold text-lg">Block #{block.index}</h3>
                            <span className="text-gray-400 text-sm ml-auto">{new Date(block.timestamp * 1000).toLocaleString()}</span>
                        </div>
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm font-mono text-gray-600">
                            <div>
                                <strong className="text-gray-900">Hash:</strong><br/>
                                <span className="break-all">{block.hash}</span>
                            </div>
                            <div>
                                <strong className="text-gray-900">Previous Hash:</strong><br/>
                                <span className="break-all">{block.previous_hash || '0'}</span>
                            </div>
                            <div className="md:col-span-2">
                                <strong className="text-gray-900">Merkle Root:</strong><br/>
                                <span className="break-all">{block.merkle_root || 'N/A'}</span>
                            </div>
                        </div>
                        <div className="mt-4 pt-4 border-t text-sm">
                            <strong>Anchored Records:</strong> {block.record_ids.length > 0 ? block.record_ids.length : 'Genesis'}
                        </div>
                    </div>
                ))}
            </div>
        </div>
    );
}
"""

files['src/pages/Sharing.jsx'] = """
import React, { useEffect, useState, useContext } from 'react';
import { fetchWithAuth } from '../api';
import { AuthContext } from '../AuthContext';

export default function Sharing() {
    const { user } = useContext(AuthContext);
    const [users, setUsers] = useState([]);
    const [records, setRecords] = useState([]);
    
    // Form state
    const [selectedRecord, setSelectedRecord] = useState('');
    const [recipient, setRecipient] = useState('');
    const [permission, setPermission] = useState('VIEW');

    useEffect(() => {
        if (user?.role === 'PATIENT') {
            fetchWithAuth('/records').then(res => res.json()).then(data => {
                setRecords(data.records);
                if(data.records.length > 0) setSelectedRecord(data.records[0].record.record_id);
            });
            fetchWithAuth('/users').then(res => res.json()).then(data => {
                const docs = data.users.filter(u => u.role === 'DOCTOR' || u.role === 'LAB');
                setUsers(docs);
                if(docs.length > 0) setRecipient(docs[0].username);
            });
        }
    }, [user]);

    const handleShare = async (e) => {
        e.preventDefault();
        try {
            await fetchWithAuth(`/records/${selectedRecord}/share`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ recipient_user_id: recipient, permission })
            });
            alert('Shared successfully!');
        } catch (err) {
            alert('Failed to share');
        }
    };

    if (user?.role !== 'PATIENT') {
        return <div className="p-6 bg-yellow-50 text-yellow-800 rounded">Only Patients can manage shares here.</div>;
    }

    return (
        <div className="space-y-6">
            <div className="bg-white rounded-lg shadow p-6">
                <h3 className="text-lg font-bold mb-4">Share a Record</h3>
                <form onSubmit={handleShare} className="space-y-4 max-w-md">
                    <div>
                        <label className="block text-sm font-medium">Record</label>
                        <select value={selectedRecord} onChange={e => setSelectedRecord(e.target.value)} className="mt-1 block w-full rounded border p-2">
                            {records.map(r => <option key={r.record.record_id} value={r.record.record_id}>{r.record.record_type} - {r.record.created_at.slice(0,10)}</option>)}
                        </select>
                    </div>
                    <div>
                        <label className="block text-sm font-medium">Recipient</label>
                        <select value={recipient} onChange={e => setRecipient(e.target.value)} className="mt-1 block w-full rounded border p-2">
                            {users.map(u => <option key={u.username} value={u.username}>{u.username} ({u.role})</option>)}
                        </select>
                    </div>
                    <div>
                        <label className="block text-sm font-medium">Permission</label>
                        <select value={permission} onChange={e => setPermission(e.target.value)} className="mt-1 block w-full rounded border p-2">
                            <option value="VIEW">VIEW</option>
                            <option value="EDIT">EDIT</option>
                        </select>
                    </div>
                    <button type="submit" className="bg-blue-600 text-white px-4 py-2 rounded">Grant Access</button>
                </form>
            </div>
            
            <div className="bg-white rounded-lg shadow p-6">
                <h3 className="text-lg font-bold mb-4">Note on Revocation</h3>
                <p className="text-sm text-gray-600">To view or revoke active shares, select the "Shares" endpoint via API. UI implementation for the revocation table is currently simplified in this view.</p>
            </div>
        </div>
    );
}
"""

files['src/pages/AuditLogs.jsx'] = """
import React, { useEffect, useState } from 'react';
import { fetchWithAuth } from '../api';

export default function AuditLogs() {
    const [logs, setLogs] = useState([]);

    useEffect(() => {
        fetchWithAuth('/audit-logs')
            .then(res => res.json())
            .then(data => setLogs(data.logs))
            .catch(err => console.error(err));
    }, []);

    return (
        <div className="bg-white shadow rounded-lg overflow-hidden">
            <table className="min-w-full divide-y divide-gray-200">
                <thead className="bg-gray-50">
                    <tr>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Timestamp</th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">User</th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Action</th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Status</th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Record ID</th>
                    </tr>
                </thead>
                <tbody className="bg-white divide-y divide-gray-200">
                    {logs.map((log, i) => (
                        <tr key={i}>
                            <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{new Date(log.timestamp).toLocaleString()}</td>
                            <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">{log.username}</td>
                            <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{log.action}</td>
                            <td className="px-6 py-4 whitespace-nowrap">
                                <span className={`inline-flex px-2 rounded-full text-xs font-semibold ${log.status === 'SUCCESS' ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'}`}>
                                    {log.status}
                                </span>
                            </td>
                            <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500 font-mono">{log.record_id ? log.record_id.slice(0,8) + '...' : '-'}</td>
                        </tr>
                    ))}
                </tbody>
            </table>
        </div>
    );
}
"""

files['src/App.jsx'] = """
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
"""

files['src/main.jsx'] = """
import React from 'react';
import ReactDOM from 'react-dom/client';
import App from './App.jsx';
import './index.css';

ReactDOM.createRoot(document.getElementById('root')).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>,
)
"""

for path, content in files.items():
    os.makedirs(os.path.dirname(path) or '.', exist_ok=True)
    with open(path, 'w', encoding='utf-8') as f:
        f.write(content.strip() + '\n')
