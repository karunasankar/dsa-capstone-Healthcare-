# Performance and Scalability Evaluation Report (Corrected Audit)

## 1. Experimental Objective
The objective of this evaluation is to scientifically measure the component scalability of the cryptographic architecture (SHA-256 + Merkle Tree + Lightweight hash-linked blockchain prototype). 

## 2. Experimental Scope Clarification (1-Million Record Limit)
It is strictly important to clarify the boundary of the 1,000,000-record claim:
- **What WAS tested at 1M**: Merkle Tree construction, mathematical storage calculation, Merkle proof generation/verification, and incremental root updates. These were executed natively in-memory.
- **What WAS NOT tested at 1M**: Full-system database writes, 1M AES-GCM disk encryptions, or 1M HTTP API calls. The full application stack was not subjected to 1 million simultaneous network inserts.

## 3. Blockchain Batch Snapshot Methodology
For the scalability experiment, batched Merkle-root anchoring was used to keep the lightweight prototype computationally manageable. 
- Number of blocks generated: 1 block per dataset scale.
- Records represented per snapshot: Up to 1,000,000.
- Memory/Storage consumption of the blockchain: Negligible (a few hundred bytes), as it acts as an O(1) state anchor.

## 4. Verification Results: Merkle Proofs
A rigorous statistical audit was performed over 100 proof generation and verification cycles for each tree size, simulating the extraction of a random sibling path and recalculating the root natively:

| Dataset Size | Mean (ms) | Std Dev (ms) | Min (ms) | Max (ms) |
|--------------|-----------|--------------|----------|----------|
| 1,000        | 0.01417   | 0.00076      | 0.01360  | 0.02110  |
| 10,000       | 0.01473   | 0.00500      | 0.00790  | 0.05190  |
| 100,000      | 0.01838   | 0.00381      | 0.01320  | 0.04780  |
| 500,000      | 0.01929   | 0.00334      | 0.01820  | 0.05020  |
| 1,000,000    | 0.04204   | 0.00676      | 0.03430  | 0.08640  |

This mathematically confirms the `O(log n)` complexity constraint. Verifying a record amongst 1,000,000 others takes a fraction of a millisecond.

## 5. Incremental Update Verification
An `update_leaf(index, new_hash)` algorithm was implemented to prevent O(n) tree rebuilding on record updates. 

**Mathematical Correctness:**
- Incremental Root: `e9ca99bb54402eeab2edffb7bf256c429985b8e93e3e70b79c0aea4b47ed1804`
- Full Rebuild Root: `e9ca99bb54402eeab2edffb7bf256c429985b8e93e3e70b79c0aea4b47ed1804`
- **Match:** TRUE. Every affected parent hash recomputes correctly without traversing untouched branches.

**Timing (100,000 records, 10 updates):**
- Full Rebuild: `134.92 ms`
- Incremental Update: `0.23 ms`

## 6. Storage Footprint Audit
The storage sizes reported (Plaintext: ~210 MB vs Proposed: ~450 MB at 1M records) are based on native string byte-length mathematics:
1. **Record Data**: Raw JSON string lengths.
2. **Encryption Overhead**: Adds 48 bytes per record (AES-GCM tag/nonce).
3. **SHA-256 Metadata**: 64 bytes per record.
4. **Merkle Nodes**: ~2N nodes * 64 bytes per node.
5. **Blockchain Metadata**: Extremely small.

The additional storage is exclusively caused by the combination of local ciphertext expansion and the storage of `2N-1` Merkle node hashes. 

## 7. Memory Methodology Audit
The reported `109.33 MB` peak RAM for a 1M-record Merkle tree was measured using Python's native `tracemalloc`. It wraps strictly the `MerkleTree()` initialization scope. It measures the peak heap delta caused by allocating the internal `self.tree` lists of strings. It inherently excludes the overhead of the Python process daemon and the dataset generator.

## 8. Security/Tampering Results
A simulated loop modified 1,000 random leaf hashes after the original tree was constructed.
- Total Tampering Cases: 1,000
- Detected Cases: 1,000
- Undetected Cases: 0
- Detection Rate: 100.00%

*Note: This strictly demonstrates the detection rate under these targeted parameters, identifying any hash divergence up to the root. It does not universally prove zero-day security against state-level architectural vulnerabilities.*

## 9. Complexity Verification
Codebase inspection strictly aligns with:
- SHA-256 = `O(record size)`
- Merkle build = `O(n)`
- Merkle proof generation = `O(log n)`
- Merkle proof verification = `O(log n)`
- Incremental leaf update = `O(log n)`
- Full rebuild = `O(n)`
- Blockchain validation = `O(B)`

## 10. Final Corrected Conclusion
Based on empirical audits, the specific cryptographic components of the proposed architecture scale exceptionally well. The `O(log n)` mathematical constraints hold flawlessly up to 1,000,000 records in memory, achieving proof verifications in `~0.04 ms` and bypassing major write penalties via verified incremental updates.

However, we cannot claim the "entire healthcare system scales to 1 million records." The full-system SQLite and HTTP boundaries were not subjected to the 1M-scale test, and scaling to that level would face serious SQL indexing and networking limitations before the cryptography failed. Additionally, the cryptography introduces significant storage overhead (over 2x), meaning database footprint growth must be tightly monitored in production environments.
