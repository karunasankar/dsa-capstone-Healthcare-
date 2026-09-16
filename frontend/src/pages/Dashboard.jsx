import React, { useEffect, useState, useContext } from 'react';
import { fetchWithAuth } from '../api';
import { Database, Link, Share2, Activity, ShieldAlert, ShieldCheck } from 'lucide-react';
import { AuthContext } from '../AuthContext';

export default function Dashboard() {
    const { user } = useContext(AuthContext);
    const [stats, setStats] = useState(null);
    const [error, setError] = useState(null);
    const [records, setRecords] = useState([]);
    const [logs, setLogs] = useState([]);
    const [patients, setPatients] = useState([]);
    const [newPatient, setNewPatient] = useState({username: '', password: ''});
    const [staffList, setStaffList] = useState([]);
    const [newStaff, setNewStaff] = useState({username: '', password: '', role: 'DOCTOR'});
    const [showResetModal, setShowResetModal] = useState(false);
    const [resetConfirmText, setResetConfirmText] = useState('');

    useEffect(() => {
        if (user && user.role === 'ADMIN') {
            fetchWithAuth('/patients').then(r=>r.json()).then(d=>setPatients(d.patients || [])).catch(e=>console.error(e));
            fetchWithAuth('/admin/staff').then(r=>r.json()).then(d=>setStaffList(d.staff || [])).catch(e=>console.error(e));
        }
    }, [user]);

    const handleCreatePatient = async (e) => {
        e.preventDefault();
        try {
            const res = await fetchWithAuth('/patients', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify(newPatient)
            });
            if(!res.ok) throw new Error(await res.text());
            alert('Patient Created!');
            setNewPatient({username: '', password: ''});
            fetchWithAuth('/patients').then(r=>r.json()).then(d=>setPatients(d.patients || [])).catch(e=>console.error(e));
        } catch(e) {
            alert('Error: ' + e.message);
        }
    };

    const handleCreateStaff = async (e) => {
        e.preventDefault();
        try {
            const res = await fetchWithAuth('/admin/staff', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify(newStaff)
            });
            if(!res.ok) throw new Error(await res.text());
            alert('Staff Created!');
            setNewStaff({username: '', password: '', role: 'DOCTOR'});
            fetchWithAuth('/admin/staff').then(r=>r.json()).then(d=>setStaffList(d.staff || [])).catch(e=>console.error(e));
        } catch(e) {
            alert('Error: ' + e.message);
        }
    };

    const handleResetDemoData = async () => {
        if (resetConfirmText !== 'RESET') return;
        try {
            const res = await fetchWithAuth('/admin/reset-demo-data', { method: 'POST' });
            if (!res.ok) throw new Error(await res.text());
            alert('Demo data successfully reset. The application is now in a clean state.');
            window.location.reload();
        } catch (e) {
            alert('Error resetting demo data: ' + e.message);
        }
    };

    useEffect(() => {
        fetchWithAuth('/dashboard/stats')
            .then(res => res.json())
            .then(data => setStats(data))
            .catch(err => setError(err.message || "Failed to load data"));
            
        fetchWithAuth('/records')
            .then(res => res.json())
            .then(data => setRecords(data.records || []))
            .catch(err => setError(err.message || "Failed to load data"));
            
        if (user && user.role === 'ADMIN') {
            fetchWithAuth('/audit-logs')
                .then(res => res.json())
                .then(data => setLogs(data.logs || []))
                .catch(err => console.error(err));
        }
    }, [user]);

    if (error) return <div className="p-6 text-red-500 font-bold">API Error: {error}</div>;
    if (!stats) return <div>Loading...</div>;

    const tamperedCount = records.filter(r => r.record.record_data?.ERROR).length;
    const validCount = records.length - tamperedCount;
    
    // Aggregate logs by action for a simple bar chart
    const actionCounts = logs.reduce((acc, log) => {
        acc[log.action] = (acc[log.action] || 0) + 1;
        return acc;
    }, {});

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
            
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                {/* Integrity Chart */}
                <div className="bg-white rounded-lg shadow p-6">
                    <h3 className="text-lg font-bold mb-4">Integrity Status Overview</h3>
                    <div className="flex h-8 w-full rounded overflow-hidden">
                        {records.length > 0 ? (
                            <>
                                <div style={{width: `${(validCount / records.length) * 100}%`}} className="bg-green-500 flex items-center justify-center text-xs text-white font-bold" title="Valid">
                                    {validCount > 0 ? `${validCount} Valid` : ''}
                                </div>
                                <div style={{width: `${(tamperedCount / records.length) * 100}%`}} className="bg-red-500 flex items-center justify-center text-xs text-white font-bold" title="Tampered">
                                    {tamperedCount > 0 ? `${tamperedCount} Tampered` : ''}
                                </div>
                            </>
                        ) : (
                            <div className="w-full bg-gray-200 flex items-center justify-center text-xs text-gray-500">No Records</div>
                        )}
                    </div>
                    <div className="mt-4 flex gap-4 text-sm text-gray-600">
                        <div className="flex items-center gap-1"><span className="w-3 h-3 bg-green-500 inline-block rounded-full"></span> Valid ({validCount})</div>
                        <div className="flex items-center gap-1"><span className="w-3 h-3 bg-red-500 inline-block rounded-full"></span> Tampered ({tamperedCount})</div>
                    </div>
                </div>

                {/* Audit Activity */}
                <div className="bg-white rounded-lg shadow p-6">
                    <h3 className="text-lg font-bold mb-4">Audit Activity</h3>
                    <div className="space-y-3">
                        {Object.entries(actionCounts).slice(0, 5).map(([action, count]) => (
                            <div key={action} className="flex items-center">
                                <div className="w-32 text-xs font-mono truncate mr-2 text-gray-500" title={action}>{action}</div>
                                <div className="flex-1 bg-gray-100 rounded h-4 overflow-hidden">
                                    <div className="bg-blue-500 h-full" style={{ width: `${(count / Math.max(...Object.values(actionCounts))) * 100}%` }}></div>
                                </div>
                                <div className="w-8 text-right text-xs font-bold text-gray-700 ml-2">{count}</div>
                            </div>
                        ))}
                        {logs.length === 0 && <div className="text-sm text-gray-500">No audit activity logged.</div>}
                    </div>
                </div>
            </div>

            <div className="bg-white rounded-lg shadow p-6">
                <h3 className="text-lg font-bold mb-4">Current Cryptographic Commitment</h3>
                <div className="bg-gray-50 p-4 rounded border text-sm break-all font-mono">
                    <strong className="text-gray-900 block mb-1">Merkle Root</strong>
                    <span className="text-gray-600">{stats.merkle_root || 'No records anchored.'}</span>
                </div>
            </div>

            {user && user.role === 'ADMIN' && (
                <div className="bg-white rounded-lg shadow p-6">
                    <h3 className="text-lg font-bold mb-4">Patient Management</h3>
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                        <div>
                            <h4 className="font-semibold mb-2">Registered Patients</h4>
                            <ul className="bg-gray-50 border rounded p-4 h-48 overflow-y-auto">
                                {(patients || []).map(p => <li key={p.username} className="py-1 border-b last:border-0">{p.username}</li>)}
                                {(patients || []).length===0 && <li className="text-gray-500">No patients found.</li>}
                            </ul>
                        </div>
                        <div>
                            <h4 className="font-semibold mb-2">Create New Patient</h4>
                            <form onSubmit={handleCreatePatient} className="space-y-4 bg-gray-50 border rounded p-4">
                                <div>
                                    <label className="block text-xs font-medium text-gray-700">Username</label>
                                    <input required type="text" className="mt-1 block w-full rounded border-gray-300 p-2 border text-sm" value={newPatient.username} onChange={e=>setNewPatient({...newPatient, username: e.target.value})}/>
                                </div>
                                <div>
                                    <label className="block text-xs font-medium text-gray-700">Password</label>
                                    <input required type="password" className="mt-1 block w-full rounded border-gray-300 p-2 border text-sm" value={newPatient.password} onChange={e=>setNewPatient({...newPatient, password: e.target.value})}/>
                                </div>
                                <button type="submit" className="w-full bg-blue-600 text-white p-2 rounded text-sm">Create Patient</button>
                            </form>
                        </div>
                    </div>

                    <div className="mt-8 border-t pt-6">
                        <h3 className="text-lg font-bold mb-4">Staff Management</h3>
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                            <div>
                                <h4 className="font-semibold mb-2">Registered Staff</h4>
                                <ul className="bg-gray-50 border rounded p-4 h-56 overflow-y-auto">
                                    {(staffList || []).map(s => (
                                        <li key={s.username} className="py-2 border-b last:border-0 flex justify-between items-center">
                                            <span>{s.username}</span>
                                            <span className="text-xs bg-blue-100 text-blue-800 px-2 py-1 rounded">{s.role}</span>
                                        </li>
                                    ))}
                                    {(staffList || []).length===0 && <li className="text-gray-500">No staff found.</li>}
                                </ul>
                            </div>
                            <div>
                                <h4 className="font-semibold mb-2">Create New Staff</h4>
                                <form onSubmit={handleCreateStaff} className="space-y-4 bg-gray-50 border rounded p-4">
                                    <div>
                                        <label className="block text-xs font-medium text-gray-700">Username</label>
                                        <input required type="text" className="mt-1 block w-full rounded border-gray-300 p-2 border text-sm" value={newStaff.username} onChange={e=>setNewStaff({...newStaff, username: e.target.value})}/>
                                    </div>
                                    <div>
                                        <label className="block text-xs font-medium text-gray-700">Password</label>
                                        <input required type="password" className="mt-1 block w-full rounded border-gray-300 p-2 border text-sm" value={newStaff.password} onChange={e=>setNewStaff({...newStaff, password: e.target.value})}/>
                                    </div>
                                    <div>
                                        <label className="block text-xs font-medium text-gray-700">Role</label>
                                        <select required className="mt-1 block w-full rounded border-gray-300 p-2 border text-sm bg-white" value={newStaff.role} onChange={e=>setNewStaff({...newStaff, role: e.target.value})}>
                                            <option value="DOCTOR">DOCTOR</option>
                                            <option value="LAB">LAB</option>
                                        </select>
                                    </div>
                                    <button type="submit" className="w-full bg-indigo-600 text-white p-2 rounded text-sm hover:bg-indigo-700">Create Staff</button>
                                </form>
                            </div>
                        </div>
                    </div>

                    <div className="mt-8 border-t pt-6">
                        <h3 className="text-lg font-bold mb-4 text-red-600">System Maintenance</h3>
                        <div className="bg-red-50 border border-red-200 rounded p-4 flex justify-between items-center">
                            <div>
                                <p className="font-semibold text-red-800">Reset Demo Data</p>
                                <p className="text-sm text-red-600">Restore the application to a clean state for demonstrations and testing. Development/demo use only. This operation removes test data.</p>
                            </div>
                            <button onClick={() => setShowResetModal(true)} className="bg-red-600 text-white px-4 py-2 rounded font-bold hover:bg-red-700">
                                Reset Demo Data
                            </button>
                        </div>
                    </div>
                </div>
            )}

            {/* Reset Modal */}
            {showResetModal && (
                <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
                    <div className="bg-white p-6 rounded-lg shadow-xl max-w-md w-full">
                        <h2 className="text-xl font-bold text-red-600 mb-4">RESET DEMO DATA</h2>
                        <p className="mb-4 text-sm text-gray-700">
                            This operation will permanently remove all test PATIENT accounts, DOCTOR accounts, records, shares, and clear the blockchain/Merkle states. Only the ADMIN account will be preserved.
                        </p>
                        <p className="mb-4 text-sm font-semibold">Type <span className="font-mono text-red-600 bg-gray-100 px-1">RESET</span> below to confirm:</p>
                        <input 
                            type="text" 
                            className="w-full border rounded p-2 mb-6 font-mono" 
                            value={resetConfirmText} 
                            onChange={(e) => setResetConfirmText(e.target.value)} 
                            placeholder="RESET"
                        />
                        <div className="flex justify-end space-x-4">
                            <button onClick={() => { setShowResetModal(false); setResetConfirmText(''); }} className="px-4 py-2 bg-gray-200 rounded hover:bg-gray-300">
                                Cancel
                            </button>
                            <button 
                                onClick={handleResetDemoData} 
                                disabled={resetConfirmText !== 'RESET'} 
                                className={`px-4 py-2 rounded font-bold text-white ${resetConfirmText === 'RESET' ? 'bg-red-600 hover:bg-red-700' : 'bg-red-300 cursor-not-allowed'}`}
                            >
                                Reset Demo Data
                            </button>
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
}
