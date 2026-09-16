# Project Architecture

## Overview
This document outlines the final architecture of the healthcare prototype system. The system enforces zero-trust principles via envelope encryption, cryptographic hashing, dynamic Merkle Trees, and hash-linked blockchain anchoring. 

## Technology Stack
- **Frontend**: React, Vite, TailwindCSS, Lucide-React
- **Backend**: Python 3, FastAPI, Uvicorn
- **Database**: SQLite3
- **Security**: PyJWT, Argon2 (via Passlib), Cryptography (AESGCM)

## Architecture Diagram

```mermaid
graph TD
    UI[React Frontend] -->|HTTPS / JWT| API[FastAPI Backend]
    
    subgraph Backend Core
        API --> AUTH[Auth & RBAC Module]
        AUTH --> ENC[AES-256-GCM Envelope Encryption]
        AUTH --> DB[(SQLite Database)]
        ENC --> DB
        
        ENC --> HASH[SHA-256 Canonical Hashing]
        HASH --> MERKLE[Dynamic Merkle Tree]
        MERKLE --> BC[Lightweight Blockchain]
        
        AUTH --> AUDIT[Audit Log Table]
    end
    
    DB --> |Encrypted Ciphertexts| DB
    MERKLE --> |O(log n) Updates| MERKLE
```

## Complete Data Flow

### Record Creation
1. **USER**: Submits a healthcare record creation request via the React UI.
2. **LOGIN / JWT**: The request includes a Bearer token.
3. **RBAC**: The backend strictly ensures the token identity corresponds to an authorized `DOCTOR` or `ADMIN`.
4. **ENCRYPT RECORD**: The plaintext record dict is passed to the Envelope Encryption module. A random DEK is generated. The record is encrypted with AES-256-GCM. The DEK is encrypted with the Master KEK.
5. **STORE OFF-CHAIN**: The raw ciphertexts, nonces, and AES tags are saved in the SQLite `records` table. Plaintext is discarded.
6. **SHA-256 HASH**: The canonical metadata is hashed into a 64-character SHA-256 string.
7. **MERKLE TREE**: The hash is appended as a leaf to the in-memory `MerkleTree`, and the parents are incrementally updated (`O(log n)`).
8. **MERKLE ROOT**: A new global cryptographic commitment (Root) is generated.
9. **BLOCKCHAIN ANCHOR**: A new Block is instantiated. It inherits the `previous_hash` and commits the new Merkle Root.
10. **AUDIT LOG**: `RECORD_CREATED` is appended to the SQLite `audit_logs` table.

### Record Verification
1. **Stored Encrypted Record**: Retrieved via `GET /records`.
2. **AES-GCM Authentication/Decryption**: The ciphertext is passed alongside its 16-byte authentication tag and 12-byte nonce. If tampered, AES-GCM raises `InvalidTag` and the pipeline aborts safely.
3. **SHA-256**: The canonical representation of the verified metadata is hashed.
4. **Merkle Proof**: A sibling-path array is extracted from the `MerkleTree`.
5. **Current/Authorized Merkle Root**: The sibling-path is reduced logically to a candidate root.
6. **Blockchain Anchor**: The candidate root is compared against the immutable Blockchain's latest state.
7. **VALID / TAMPERED**: Result reflects back to the React UI as a visual green checkmark or red alert.

## Security Audit
### Authentication
- **WHAT it protects**: Ensures only recognized identities access the API.
- **HOW it works**: Argon2 hashes passwords. Successful logins yield a JWT signed by a server secret.
- **WHAT it does NOT protect**: Compromised JWTs on the client device.

### Authorization
- **WHAT it protects**: Enforces Data Isolation and Role Access (ADMIN, DOCTOR, LAB, PATIENT).
- **HOW it works**: Backend intercepts requests natively checking the `RequiresRole` Dependency wrapper.
- **WHAT it does NOT protect**: Authorized insider threats legally requesting data.

### Encryption
- **WHAT it protects**: Data-at-rest from database leaks or unauthorized DBA access.
- **HOW it works**: AES-256-GCM Envelope Encryption generates a per-record Data Encryption Key (DEK). The Master Key (KEK) is injected via `.env`.
- **WHAT it does NOT protect**: Endpoint compromises running inside the active Python heap.

### Integrity
- **WHAT it protects**: Undetected modification of records (Tampering).
- **HOW it works**: SHA-256 canonical hashing + `O(log n)` Merkle Trees + hash-chained Blockchain.
- **WHAT it does NOT protect**: A complete parallel rebuild of the Database + Blockchain by an attacker possessing the Master KEK.

### Sharing
- **WHAT it protects**: Unauthorized peer access to patient data.
- **HOW it works**: Explicit ACL mappings in the `record_shares` table. Patients toggle `VIEW` or `EDIT` states natively.
- **WHAT it does NOT protect**: An authorized shared peer copying the data externally.

### Audit
- **WHAT it protects**: Lack of oversight and accountability.
- **HOW it works**: Irreversible SQLite append-only logs tracking `RECORD_CREATED`, `RECORD_VIEWED`, `UNAUTHORIZED_ACCESS`, etc.
- **WHAT it does NOT protect**: Deletion of the raw SQLite `.db` file by a system administrator.

## Cryptographic Audit
A rigorous test suite validated:
- **Deterministic Hashing**: Enforced via `json.dumps(..., sort_keys=True)`.
- **Odd-Leaf Handling**: Secure duplication (`current_level[i + 1] if i + 1 < len(current_level) else left`).
- **Nonce Handling**: `os.urandom(12)` generates collision-resistant AES-GCM IVs per record.
- **Incremental Root Calc**: Sibling logic traverses upwards precisely.
- **Blockchain Consistency**: `is_chain_valid()` iteratively re-verifies `previous_hash` chains.

## Data Privacy Audit
**Verified**: Plaintext medical data is completely absent from the Blockchain, Merkle nodes, and Audit Logs. Medical data is strictly held in the `encrypted_data` hex columns. Unauthorized `GET /records/{id}` queries throw strict `403 Forbidden` responses prior to any cryptographic parsing.

## Sharing Security Audit
**Verified**: 
- A Patient sharing to a Doctor with `VIEW` access succeeds at `GET` but returns `403 Forbidden` on `PUT`.
- A Patient explicitly revoking the share instantly destroys the `active=1` constraint, causing the Doctor to instantly lose access natively.
- No user can access records unmapped to their `patient_id` or `record_shares` recipient.

## Tampering Audit
**Verified**: 
Modifying ciphertext hex in SQLite triggers an instantaneous **AES-GCM `InvalidTag`**.
Modifying the SHA-256 metadata triggers an instantaneous **Merkle Root divergence**.
Modifying the Blockchain triggers an instantaneous **Hash-chain break**.
The detection rate under tested scenarios is 100%. The system correctly flags the record as `TAMPERED` dynamically on the React UI without crashing.
