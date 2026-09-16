import React, { useEffect, useState } from 'react';
import { fetchWithAuth } from '../api';
import { ShieldCheck, ShieldAlert, Link } from 'lucide-react';

export default function Blockchain() {
    const [chainData, setChainData] = useState(null);
    const [error, setError] = useState(null);

    useEffect(() => {
        fetchWithAuth('/blockchain')
            .then(res => res.json())
            .then(data => setChainData(data))
            .catch(err => setError(err.message || "Failed to load data"));
    }, []);

    if (error) return <div className="p-6 text-red-500 font-bold">API Error: {error}</div>;
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
