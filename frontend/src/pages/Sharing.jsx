import React, { useEffect, useState, useContext } from 'react';
import { fetchWithAuth } from '../api';
import { AuthContext } from '../AuthContext';

export default function Sharing() {
    const { user } = useContext(AuthContext);
    const [users, setUsers] = useState([]);
    const [records, setRecords] = useState([]);
    const [activeShares, setActiveShares] = useState([]);
    
    // Form state
    const [selectedRecord, setSelectedRecord] = useState('');
    const [recipient, setRecipient] = useState('');
    const [permission, setPermission] = useState('VIEW');

    useEffect(() => {
        if (user?.role === 'PATIENT') {
            loadRecords();
            fetchWithAuth('/users').then(res => res.json()).then(data => {
                const docs = data.users.filter(u => u.role === 'DOCTOR' || u.role === 'LAB');
                setUsers(docs);
                if(docs.length > 0) setRecipient(docs[0].username);
            });
        }
    }, [user]);

    const loadRecords = async () => {
        const res = await fetchWithAuth('/records');
        const data = await res.json();
        setRecords(data.records);
        if(data.records.length > 0) {
            setSelectedRecord(data.records[0].record.record_id);
            loadShares(data.records[0].record.record_id);
        }
    };

    const loadShares = async (recordId) => {
        try {
            const res = await fetchWithAuth(`/records/${recordId}/shares`);
            const data = await res.json();
            setActiveShares(data.shares);
        } catch (err) {
            setActiveShares([]);
        }
    };

    const handleRecordChange = (e) => {
        const rid = e.target.value;
        setSelectedRecord(rid);
        loadShares(rid);
    };

    const handleShare = async (e) => {
        e.preventDefault();
        try {
            await fetchWithAuth(`/records/${selectedRecord}/share`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ recipient_user_id: recipient, permission })
            });
            alert('Shared successfully!');
            loadShares(selectedRecord);
        } catch (err) {
            alert('Failed to share');
        }
    };

    const handleRevoke = async (shareId) => {
        try {
            await fetchWithAuth(`/records/${selectedRecord}/share/${shareId}`, { method: 'DELETE' });
            alert('Access revoked!');
            loadShares(selectedRecord);
        } catch (err) {
            alert('Failed to revoke');
        }
    };

    if (user?.role !== 'PATIENT') {
        return <div className="p-6 bg-yellow-50 text-yellow-800 rounded">Only Patients can manage shares here.</div>;
    }

    return (
        <div className="space-y-6">
            <div className="bg-white rounded-lg shadow p-6">
                <h3 className="text-lg font-bold mb-4">Grant Access</h3>
                <form onSubmit={handleShare} className="space-y-4 max-w-md">
                    <div>
                        <label className="block text-sm font-medium">Record</label>
                        <select value={selectedRecord} onChange={handleRecordChange} className="mt-1 block w-full rounded border p-2">
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
            
            <div className="bg-white rounded-lg shadow overflow-hidden">
                <div className="p-4 bg-gray-50 border-b">
                    <h3 className="text-lg font-bold">Active Shares for Selected Record</h3>
                </div>
                <table className="min-w-full divide-y divide-gray-200">
                    <thead className="bg-gray-50">
                        <tr>
                            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Recipient</th>
                            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Permission</th>
                            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Created</th>
                            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Actions</th>
                        </tr>
                    </thead>
                    <tbody className="bg-white divide-y divide-gray-200">
                        {activeShares.map(s => (
                            <tr key={s.share_id}>
                                <td className="px-6 py-4 whitespace-nowrap text-sm font-medium">{s.recipient_user_id}</td>
                                <td className="px-6 py-4 whitespace-nowrap text-sm">{s.permission}</td>
                                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{new Date(s.created_at).toLocaleString()}</td>
                                <td className="px-6 py-4 whitespace-nowrap text-sm">
                                    <button onClick={() => handleRevoke(s.share_id)} className="text-red-600 hover:text-red-900 font-bold">Revoke</button>
                                </td>
                            </tr>
                        ))}
                        {activeShares.length === 0 && (
                            <tr>
                                <td colSpan="4" className="px-6 py-4 text-center text-gray-500">No active shares found for this record.</td>
                            </tr>
                        )}
                    </tbody>
                </table>
            </div>
        </div>
    );
}
