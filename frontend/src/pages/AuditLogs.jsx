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
