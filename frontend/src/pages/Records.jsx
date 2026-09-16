import React, { useEffect, useState, useContext } from 'react';
import { fetchWithAuth } from '../api';
import { ShieldAlert, ShieldCheck, HelpCircle } from 'lucide-react';
import { AuthContext } from '../AuthContext';

export default function Records() {
    const { user } = useContext(AuthContext);
    const [records, setRecords] = useState([]);
    const [selectedRecord, setSelectedRecord] = useState(null);
    const [error, setError] = useState(null);

    
    const [patients, setPatients] = useState([]);
    const [showCreate, setShowCreate] = useState(false);
    const [newRecord, setNewRecord] = useState({patient_id: '', record_type: 'Blood Test', val: ''});

    useEffect(() => {
        if (user && (user.role === 'DOCTOR' || user.role === 'LAB')) {
            fetchWithAuth('/patients').then(r=>r.json()).then(d=>setPatients(d.patients || [])).catch(e=>console.error(e));
        }
    }, [user]);

    const handleCreateRecord = async (e) => {
        e.preventDefault();
        try {
            await fetchWithAuth('/records', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({
                    patient_id: newRecord.patient_id,
                    record_type: newRecord.record_type,
                    record_data: { value: newRecord.val }
                })
            });
            setShowCreate(false);
            loadRecords();
            alert('Record Created!');
        } catch(e) {
            alert('Error creating record: ' + e.message);
        }
    };

    const [editingRecord, setEditingRecord] = useState(null);
    const [editData, setEditData] = useState('');

    const handleUpdateRecord = async (e) => {
        e.preventDefault();
        try {
            let parsedData;
            try {
                parsedData = JSON.parse(editData);
            } catch(err) {
                alert('Invalid JSON data');
                return;
            }
            await fetchWithAuth(`/records/${editingRecord.record_id}`, {
                method: 'PUT',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({
                    record_type: editingRecord.record_type,
                    record_data: parsedData
                })
            });
            setEditingRecord(null);
            loadRecords();
            alert('Record Updated!');
        } catch(e) {
            alert('Error updating record: ' + e.message);
        }
    };

    const loadRecords = () => {
        fetchWithAuth('/records')
            .then(res => res.json())
            .then(data => setRecords(data.records))
            .catch(err => setError(err.message || "Failed to load data"));
    };

    useEffect(() => {
        loadRecords();
    }, []);

    const verifyRecord = async (id) => {
        try {
            const res = await fetchWithAuth(`/verify/${id}`, { method: 'POST' });
            const data = await res.json();
            alert(`Integrity Status: ${data.status}\n\nDetails: ${data.detail || ''}`);
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
            <div className="flex justify-between items-center mb-4">
                <h2 className="text-xl font-bold">Healthcare Records</h2>
                {user && (user.role === 'DOCTOR' || user.role === 'LAB') && (
                    <button onClick={() => setShowCreate(true)} className="bg-blue-600 text-white px-4 py-2 rounded">+ Create Record</button>
                )}
            </div>
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
                                        {r.record.permission === 'EDIT' && (
                                            <button onClick={() => { setEditingRecord(r.record); setEditData(JSON.stringify(r.record.record_data, null, 2)); }} className="text-green-600 hover:text-green-900">Edit</button>
                                        )}
                                        <button onClick={() => verifyRecord(r.record.record_id)} className="text-indigo-600 hover:text-indigo-900">Verify</button>
                                        {user?.role === 'DOCTOR' && <button onClick={() => tamperRecord(r.record.record_id)} className="text-red-600 hover:text-red-900">Tamper (Demo)</button>}
                                    </td>
                                </tr>
                            );
                        })}
                    </tbody>
                </table>
            </div>

            {showCreate && (
                <div className="fixed inset-0 bg-gray-600 bg-opacity-50 flex items-center justify-center p-4 z-50">
                    <div className="bg-white rounded-lg shadow-xl max-w-md w-full p-6">
                        <h3 className="text-lg font-bold mb-4">Create New Record</h3>
                        <form onSubmit={handleCreateRecord} className="space-y-4">
                            <div>
                                <label className="block text-sm font-medium text-gray-700">Patient</label>
                                <select required className="mt-1 block w-full rounded-md border-gray-300 shadow-sm p-2 border" value={newRecord.patient_id} onChange={e=>setNewRecord({...newRecord, patient_id: e.target.value})}>
                                    <option value="">Select a patient...</option>
                                    {(patients || []).map(p => <option key={p.username} value={p.username}>{p.username}</option>)}
                                </select>
                            </div>
                            <div>
                                <label className="block text-sm font-medium text-gray-700">Record Type</label>
                                <select className="mt-1 block w-full rounded-md border-gray-300 shadow-sm p-2 border" value={newRecord.record_type} onChange={e=>setNewRecord({...newRecord, record_type: e.target.value})}>
                                    <option>Blood Test</option>
                                    <option>X-Ray</option>
                                    <option>MRI</option>
                                </select>
                            </div>
                            <div>
                                <label className="block text-sm font-medium text-gray-700">Value/Notes</label>
                                <input required type="text" className="mt-1 block w-full rounded-md border-gray-300 shadow-sm p-2 border" value={newRecord.val} onChange={e=>setNewRecord({...newRecord, val: e.target.value})}/>
                            </div>
                            <div className="flex justify-end gap-2 mt-4">
                                <button type="button" onClick={()=>setShowCreate(false)} className="px-4 py-2 bg-gray-200 rounded">Cancel</button>
                                <button type="submit" className="px-4 py-2 bg-blue-600 text-white rounded">Create</button>
                            </div>
                        </form>
                    </div>
                </div>
            )}

            {selectedRecord && (
                <div className="fixed inset-0 bg-gray-600 bg-opacity-50 flex items-center justify-center p-4 z-50">
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

            {editingRecord && (
                <div className="fixed inset-0 bg-gray-600 bg-opacity-50 flex items-center justify-center p-4 z-50">
                    <div className="bg-white rounded-lg shadow-xl max-w-2xl w-full p-6">
                        <h3 className="text-lg font-bold mb-4">Edit Record Data</h3>
                        <form onSubmit={handleUpdateRecord} className="space-y-4">
                            <div>
                                <label className="block text-sm font-medium text-gray-700">JSON Data</label>
                                <textarea required className="mt-1 block w-full rounded-md border-gray-300 shadow-sm p-2 border font-mono text-sm h-48" value={editData} onChange={e=>setEditData(e.target.value)} />
                            </div>
                            <div className="flex justify-end gap-2 mt-4">
                                <button type="button" onClick={() => setEditingRecord(null)} className="px-4 py-2 bg-gray-200 rounded text-gray-800 hover:bg-gray-300">Cancel</button>
                                <button type="submit" className="px-4 py-2 bg-green-600 text-white rounded hover:bg-green-700">Save Update</button>
                            </div>
                        </form>
                    </div>
                </div>
            )}
        </div>
    );
}
