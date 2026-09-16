import React, { useEffect, useState } from 'react';
import { fetchWithAuth } from '../api';
import { ArrowDown, ShieldCheck } from 'lucide-react';

export default function Integrity() {
    const [tree, setTree] = useState(null);
    const [error, setError] = useState(null);
    const [selectedLeaf, setSelectedLeaf] = useState(null);
    const [highlightedHashes, setHighlightedHashes] = useState(new Set());

    useEffect(() => {
        fetchWithAuth('/merkle/tree')
            .then(res => res.json())
            .then(data => setTree(data))
            .catch(err => setError(err.message || "Failed to load data"));
    }, []);

    const handleSelectLeaf = (hashIndex) => {
        if (!tree) return;
        const leafHash = tree.levels[0][hashIndex];
        setSelectedLeaf(leafHash);

        const newHighlights = new Set();
        let currentIndex = hashIndex;

        // Reconstruct the proof path manually based on index
        for (let i = 0; i < tree.levels.length - 1; i++) {
            const level = tree.levels[i];
            const isRight = currentIndex % 2 !== 0;
            const siblingIndex = isRight ? currentIndex - 1 : Math.min(currentIndex + 1, level.length - 1);
            
            newHighlights.add(level[currentIndex]);
            newHighlights.add(level[siblingIndex]);
            
            currentIndex = Math.floor(currentIndex / 2);
        }
        // Root is always highlighted
        newHighlights.add(tree.levels[tree.levels.length - 1][0]);
        setHighlightedHashes(newHighlights);
    };

    if (error) return <div className="p-6 text-red-500 font-bold">API Error: {error}</div>;
    if (!tree) return <div>Loading...</div>;

    return (
        <div className="space-y-6">
            <div className="bg-white shadow rounded-lg p-6 text-center overflow-x-auto">
                <h3 className="text-lg font-bold mb-6">Dynamic Merkle Tree Visualization</h3>
                
                <div className="flex flex-col items-center gap-2 mb-8">
                    <div className="bg-blue-100 text-blue-800 p-3 rounded font-mono text-sm max-w-full break-all border border-blue-200">
                        <strong>Current Merkle Root:</strong><br/>{tree.root}
                    </div>
                    <ArrowDown className="text-gray-400" />
                    <div className="bg-purple-100 text-purple-800 p-3 rounded border border-purple-200">
                        Anchored to Blockchain
                    </div>
                </div>

                <div className="min-w-max inline-flex flex-col items-center gap-8">
                    {[...tree.levels].reverse().map((level, i_reversed) => {
                        const i = tree.levels.length - 1 - i_reversed;
                        const isLeafLevel = (i === 0);
                        
                        return (
                            <div key={i} className="flex gap-4">
                                {level.map((hash, j) => {
                                    const isHighlighted = highlightedHashes.has(hash);
                                    const isSelected = isLeafLevel && selectedLeaf === hash;
                                    let bgClass = "bg-gray-50 border-gray-200 text-gray-600";
                                    
                                    if (isSelected) bgClass = "bg-green-100 border-green-500 text-green-900 ring-2 ring-green-500";
                                    else if (isHighlighted) bgClass = "bg-blue-50 border-blue-400 text-blue-900 shadow-md";

                                    return (
                                        <div 
                                            key={j} 
                                            onClick={() => isLeafLevel && handleSelectLeaf(j)}
                                            className={`border rounded p-3 text-xs font-mono transition-all ${bgClass} ${isLeafLevel ? 'cursor-pointer hover:bg-gray-100' : ''}`} 
                                            title={hash}
                                        >
                                            <div className="font-bold mb-1">
                                                {isLeafLevel ? (tree.record_map[hash] ? `Record: ${tree.record_map[hash].slice(0,6)}` : 'Leaf') : 'Node'}
                                            </div>
                                            {hash.slice(0, 8)}...
                                        </div>
                                    )
                                })}
                            </div>
                        )
                    })}
                </div>
                <div className="mt-8 text-sm text-gray-500 text-left">
                    <p><strong>Instructions:</strong> Click any leaf node (Record) above to dynamically calculate and highlight its Merkle Proof path to the root. The highlighted nodes represent the exact sibling hashes needed to mathematically reconstruct the Root without revealing the other records.</p>
                </div>
            </div>
        </div>
    );
}
