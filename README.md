# Privacy-Preserving Healthcare Record Integrity and Secure Sharing Using Dynamic Merkle Trees and Blockchain

## Architecture
This project is a full-stack prototype demonstrating how healthcare records can be securely managed off-chain while maintaining their cryptographic integrity using a lightweight blockchain. 
The system consists of:
- **Frontend**: A React application for user interaction, record viewing, and verification.
- **Backend**: A Python FastAPI server handling business logic, cryptographic operations, and blockchain anchoring.
- **Database**: SQLite, used to store the actual medical records off-chain.
- **Blockchain**: A lightweight, Python-based hash-linked blockchain used exclusively to store cryptographic metadata.

## Authentication & Role-Based Access Control (RBAC)

The backend uses a robust, JWT-based (JSON Web Token) authentication architecture combined with strict RBAC enforcement to protect all sensitive API operations.

### JWT Flow
1. Users authenticate via `POST /auth/login`.
2. The server compares the provided credentials against the `bcrypt` hashed passwords in the SQLite `users` table.
3. Upon success, a signed JWT Access Token containing the user's `username` and `role` is returned.
4. Clients must pass this JWT as a Bearer token in the `Authorization` header for all protected endpoints.
5. FastAPI dependencies intercept incoming requests, validate the JWT signature, ensure token freshness, and assert that the user possesses the required `role` for the specified route.

### Password Hashing
The system ensures that plaintext passwords are **never** stored. All passwords are automatically salted and hashed via the `bcrypt` algorithm using `passlib` prior to storage.

### Permission Matrix

| Operation                  | Endpoint                        | Required Roles         | Patient Isolation Notes                                       |
|----------------------------|---------------------------------|------------------------|---------------------------------------------------------------|
| Create Record              | `POST /records`                 | DOCTOR, LAB            | -                                                             |
| Update Record              | `PUT /records/{id}`             | DOCTOR                 | -                                                             |
| Delete Record              | `DELETE /records/{id}`          | DOCTOR, ADMIN          | -                                                             |
| Verify Record              | `POST /verify/{id}`             | ALL ROLES              | PATIENT roles can strictly verify *only* their own records.   |
| View Blockchain State      | `GET /blockchain`               | ADMIN                  | Blocks non-admins to prevent mapping hash relationships.      |
| List Records               | `GET /records`                  | ALL ROLES              | PATIENT roles receive a filtered list omitting other patients.|

### Development Test Accounts
The database automatically seeds the following accounts for local prototyping (all use the password `password123`):
- **admin** (ADMIN)
- **doctor1** (DOCTOR)
- **lab1** (LAB)
- **patient1** (PATIENT)

*(Note: In a production healthcare system, self-service registration would be disabled in favor of strict external identity provisioning.)*

## Persistent Record Lifecycle
The system provides persistence for both off-chain medical data and on-chain blockchain records, allowing it to recover cleanly across server restarts.

### 1. Authorized Update
When a doctor legitimately updates a patient's record through the API (`PUT /records/{id}`):
- The medical record in the SQLite database is updated.
- A **new SHA-256 hash** is calculated based on the updated canonical data.
- The **Current Merkle State** is dynamically rebuilt using the updated hash.
- A **new Merkle Root** is calculated.
- A **new blockchain snapshot** is appended to the chain.
Because the system authorized the change and created a new mathematical proof, verifying the record will return `VALID`.

### 2. Unauthorized Tampering
If an attacker manually alters the SQLite database directly (simulated via `/tamper`):
- The physical medical record changes.
- The original cryptographic hash (stored off-chain) is **not** updated.
- The Merkle Tree is **not** rebuilt.
- No new blockchain snapshot is taken.
Because the newly hashed raw data no longer aligns with the old cryptographic proof remaining in the tree, verifying the record will instantly flag it as `TAMPERED`.

### 3. Historical Blockchain Snapshot vs. Current Merkle State
- **Current Merkle State**: Represents the unified hash tree of all *currently active* records in the system.
- **Historical Blockchain Snapshot**: The blockchain maintains an immutable append-only log of every single state the Merkle tree has ever been in.

## Data Flow
1. **Record Creation**: A user submits a new healthcare record via the React frontend.
2. **Storage**: The backend stores the raw record in the SQLite database.
3. **Hashing**: The backend generates a SHA-256 hash of a canonical representation of the record.
4. **Merkle Tree Update**: The new hash is appended to a list of historical leaves, and a new Merkle Tree root is computed.
5. **Blockchain Anchoring**: The new Merkle Root is stored in a newly mined block on the blockchain.
6. **Verification**: When requested, the system recalculates the record's current hash, reconstructs the Merkle proof using the current history, and verifies it against the Merkle root anchored in the blockchain.
