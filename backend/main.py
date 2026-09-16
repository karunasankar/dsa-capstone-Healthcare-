import sqlite3
from database import DB_PATH
from fastapi import FastAPI, HTTPException, Depends
from fastapi.security import OAuth2PasswordBearer
from pydantic import BaseModel
from typing import Dict, Any, List, Optional
import uuid
from datetime import datetime, timezone
import os

from dotenv import load_dotenv
load_dotenv()

from database import (
    init_db, clear_db, insert_record, get_record, get_all_records, 
    update_record_tamper, insert_block, get_all_blocks, 
    update_record_legitimate, delete_record,
    insert_user, get_user_by_username, log_audit,
    insert_share, revoke_share, get_shares_for_record, get_share_for_user, get_shared_records_for_user
)
from crypto import canonical_record_hash, MerkleTree, Blockchain, Block
from auth import get_password_hash, verify_password, create_access_token, decode_access_token
from encryption import encrypt_record_data, decrypt_record_data
from cryptography.exceptions import InvalidTag
from fastapi.middleware.cors import CORSMiddleware

init_db()

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

blockchain = Blockchain()
current_leaves = []
record_hash_map = {}

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")

def seed_users():
    default_users = [
        {"username": "admin", "role": "ADMIN"},
        {"username": "doctor1", "role": "DOCTOR"},
        {"username": "lab1", "role": "LAB"},
        {"username": "patient1", "role": "PATIENT"},
        {"username": "patient2", "role": "PATIENT"}
    ]
    for u in default_users:
        if not get_user_by_username(u["username"]):
            now = datetime.now(timezone.utc).isoformat()
            user_data = {
                "user_id": str(uuid.uuid4()),
                "username": u["username"],
                "password_hash": get_password_hash("password123"), # DEV ONLY
                "role": u["role"],
                "created_at": now,
                "active": 1
            }
            insert_user(user_data)

def load_state_from_db():
    global blockchain
    db_blocks = get_all_blocks()
    if db_blocks:
        blockchain.chain = [Block.from_dict(b) for b in db_blocks]
    else:
        blockchain = Blockchain()
        b = blockchain.chain[0]
        insert_block({
            "index": b.index,
            "previous_hash": b.previous_hash,
            "merkle_root": b.merkle_root,
            "record_ids": b.record_ids,
            "timestamp": b.timestamp,
            "hash": b.hash
        })
    rebuild_merkle_state()
    seed_users()

def rebuild_merkle_state():
    global current_leaves, record_hash_map
    records = get_all_records()
    current_leaves.clear()
    record_hash_map.clear()
    for r in records:
        h = r["record_hash"]
        current_leaves.append(h)
        record_hash_map[r["record_id"]] = h
    
    tree = MerkleTree(current_leaves)
    return tree.get_root(), [r["record_id"] for r in records]

load_state_from_db()

# --- Auth Dependencies ---

async def get_current_user(token: str = Depends(oauth2_scheme)):
    payload = decode_access_token(token)
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    username = payload.get("sub")
    if username is None:
        raise HTTPException(status_code=401, detail="Invalid token payload")
    
    user = get_user_by_username(username)
    if user is None:
        raise HTTPException(status_code=401, detail="User not found")
    
    return user

def require_roles(roles: List[str]):
    async def role_checker(user: dict = Depends(get_current_user)):
        if user["role"] not in roles:
            log_audit(user["username"], "unauthorized_access", "FAILED")
            raise HTTPException(status_code=403, detail="Not enough permissions")
        return user
    return role_checker

# --- Auth Endpoints ---

class UserRegister(BaseModel):
    username: str
    password: str
    role: str

class UserLogin(BaseModel):
    username: str
    password: str

@app.post("/auth/register")
def register_user(user_in: UserRegister):
    valid_roles = ["PATIENT", "DOCTOR", "LAB", "ADMIN"]
    if user_in.role not in valid_roles:
        raise HTTPException(status_code=400, detail="Invalid role")
    
    if len(user_in.password) < 6:
        raise HTTPException(status_code=400, detail="Password must be at least 6 characters")
        
    existing = get_user_by_username(user_in.username)
    if existing:
        raise HTTPException(status_code=400, detail="Username already exists")
        
    now = datetime.now(timezone.utc).isoformat()
    new_user = {
        "user_id": str(uuid.uuid4()),
        "username": user_in.username,
        "password_hash": get_password_hash(user_in.password),
        "role": user_in.role,
        "created_at": now,
        "active": 1
    }
    insert_user(new_user)
    log_audit(new_user["username"], "registration", "SUCCESS")
    return {"message": "User registered successfully"}

@app.post("/auth/login")
def login_user(user_in: UserLogin):
    user = get_user_by_username(user_in.username)
    if not user or not verify_password(user_in.password, user["password_hash"]):
        log_audit(user_in.username, "login", "FAILED")
        raise HTTPException(status_code=401, detail="Incorrect username or password")
        
    token = create_access_token(data={"sub": user["username"], "role": user["role"]})
    log_audit(user["username"], "login", "SUCCESS")
    return {"access_token": token, "token_type": "bearer"}

@app.get("/auth/me")
def get_me(current_user: dict = Depends(get_current_user)):
    return {
        "user_id": current_user["user_id"],
        "username": current_user["username"],
        "role": current_user["role"]
    }

class PatientCreate(BaseModel):
    username: str
    password: str

class StaffCreate(BaseModel):
    username: str
    password: str
    role: str

@app.post("/admin/staff")
def create_staff(staff_in: StaffCreate, current_user: dict = Depends(require_roles(["ADMIN"]))):
    if staff_in.role not in ["DOCTOR", "LAB"]:
        raise HTTPException(status_code=400, detail="Invalid role. Must be DOCTOR or LAB.")
        
    existing = get_user_by_username(staff_in.username)
    if existing:
        raise HTTPException(status_code=400, detail="Username already exists")
        
    now = datetime.now(timezone.utc).isoformat()
    hashed = get_password_hash(staff_in.password)
    user_id = str(uuid.uuid4())
    insert_user({
        "user_id": user_id,
        "username": staff_in.username,
        "password_hash": hashed,
        "role": staff_in.role,
        "created_at": now,
        "active": 1
    })
    log_audit(current_user["username"], f"STAFF_CREATED", "SUCCESS", staff_in.username)
    return {"message": "Staff created successfully"}

@app.get("/admin/staff")
def list_staff(current_user: dict = Depends(require_roles(["ADMIN"]))):
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute('SELECT username, role, active, created_at FROM users WHERE role IN ("DOCTOR", "LAB")')
    staff = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return {"staff": staff}

@app.post("/patients")
def create_patient(patient_in: PatientCreate, current_user: dict = Depends(require_roles(["ADMIN"]))):
    existing = get_user_by_username(patient_in.username)
    if existing:
        raise HTTPException(status_code=400, detail="Username already exists")
    now = datetime.now(timezone.utc).isoformat()
    hashed = get_password_hash(patient_in.password)
    user_id = str(uuid.uuid4())
    insert_user({
        "user_id": user_id,
        "username": patient_in.username,
        "password_hash": hashed,
        "role": "PATIENT",
        "created_at": now,
        "active": 1
    })
    log_audit(current_user["username"], "PATIENT_CREATED", "SUCCESS", patient_in.username)
    return {"message": "Patient created successfully", "user_id": user_id}

@app.get("/patients")
def list_patients(current_user: dict = Depends(require_roles(["ADMIN", "DOCTOR", "LAB"]))):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('SELECT username FROM users WHERE role = "PATIENT"')
    patients = [{"username": row[0]} for row in cursor.fetchall()]
    conn.close()
    return {"patients": patients}

# --- Record Models ---

class RecordInput(BaseModel):
    patient_id: str
    record_type: str
    record_data: Dict[str, Any]

class UpdateRecordInput(BaseModel):
    record_data: Dict[str, Any]

class ShareRecordInput(BaseModel):
    recipient_user_id: str
    permission: str

# --- Core Endpoints ---

@app.post("/dev/reset")
def reset_system():
    clear_db()
    load_state_from_db()
    return {"message": "System fully reset to genesis state."}

def has_record_access(user, record, required_permission="VIEW") -> bool:
    if user["role"] == "PATIENT":
        return record["patient_id"] == user["username"]
    if user["role"] == "ADMIN":
        return False # Admins shouldn't automatically see medical contents
    if user["role"] in ["DOCTOR", "LAB"]:
        # Check sharing table
        share = get_share_for_user(record["record_id"], user["username"])
        if not share:
            # Maybe the doctor created it? Let's say doctor only has access if shared.
            # But the test says "Adding 3 healthcare records as DOCTOR..." 
            # Wait, if a doctor creates a record, they need access. 
            # We'll automatically create a share for them when they create the record!
            return False
        if required_permission == "EDIT" and share["permission"] != "EDIT":
            return False
        return True
    return False

@app.get("/records")
def list_records(current_user: dict = Depends(get_current_user)):
    records = get_all_records()
    results = []
    
    # Pre-fetch shares for doctors/labs
    allowed_records = []
    if current_user["role"] in ["DOCTOR", "LAB"]:
        allowed_records = get_shared_records_for_user(current_user["username"])

    for r in records:
        permission = None
        if current_user["role"] == "PATIENT":
            if r["patient_id"] != current_user["username"]:
                continue
            permission = "OWNER"
        elif current_user["role"] in ["DOCTOR", "LAB"]:
            if r["record_id"] not in allowed_records:
                continue
            share = get_share_for_user(r["record_id"], current_user["username"])
            permission = share["permission"] if share else None
        elif current_user["role"] == "ADMIN":
            continue # Admins don't view medical data by default in this prototype
            
        # Decrypt it for view
        try:
            plaintext_data = decrypt_record_data(r)
        except InvalidTag:
            plaintext_data = {"ERROR": "Decryption Failed - Data Tampered"}
            log_audit(current_user["username"], "DECRYPTION_FAILURE", "FAILED", r["record_id"])
            
        r_out = {
            "record_id": r["record_id"],
            "patient_id": r["patient_id"],
            "record_type": r["record_type"],
            "record_data": plaintext_data,
            "created_at": r["created_at"],
            "updated_at": r["updated_at"],
            "permission": permission
        }
        results.append({
            "record": r_out,
            "hash": r.get("record_hash")
        })
        
    return {"records": results}

@app.post("/records")
def add_record(record_in: RecordInput, current_user: dict = Depends(require_roles(["DOCTOR", "LAB"]))):
    # Validate Patient
    patient = get_user_by_username(record_in.patient_id)
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")
    if patient["role"] != "PATIENT":
        raise HTTPException(status_code=400, detail="Invalid patient identity")

    now = datetime.now(timezone.utc).isoformat()
    record_id = str(uuid.uuid4())
    
    # Encrypt
    try:
        enc_metadata = encrypt_record_data(record_in.record_data)
    except Exception as e:
        log_audit(current_user["username"], "ENCRYPTION_FAILURE", "FAILED")
        raise HTTPException(status_code=500, detail="Failed to encrypt data")
        
    # Canonical structure for SHA256 (MUST match what verify_record decrypts into)
    canonical_dict = {
        "record_id": record_id,
        "patient_id": record_in.patient_id,
        "record_type": record_in.record_type,
        "record_data": record_in.record_data,
        "created_at": now,
        "updated_at": now
    }
    record_hash = canonical_record_hash(canonical_dict)
    
    db_record = {
        "record_id": record_id,
        "patient_id": record_in.patient_id,
        "record_type": record_in.record_type,
        "encrypted_data": enc_metadata["encrypted_data"],
        "data_nonce": enc_metadata["data_nonce"],
        "data_tag": enc_metadata["data_tag"],
        "encrypted_dek": enc_metadata["encrypted_dek"],
        "dek_nonce": enc_metadata["dek_nonce"],
        "dek_tag": enc_metadata["dek_tag"],
        "record_hash": record_hash,
        "created_at": now,
        "updated_at": now
    }
    
    insert_record(db_record)
    log_audit(current_user["username"], "RECORD_CREATED", "SUCCESS", record_id)
    
    # Auto-share with creator (EDIT)
    insert_share({
        "share_id": str(uuid.uuid4()),
        "record_id": record_id,
        "owner_user_id": record_in.patient_id,
        "recipient_user_id": current_user["username"],
        "permission": "EDIT",
        "created_at": now,
        "active": 1
    })
    
    merkle_root, record_ids = rebuild_merkle_state()
    block = blockchain.add_block(merkle_root, record_ids)
    insert_block({
        "index": block.index,
        "previous_hash": block.previous_hash,
        "merkle_root": block.merkle_root,
        "record_ids": block.record_ids,
        "timestamp": block.timestamp,
        "hash": block.hash
    })
    
    return {"record": canonical_dict, "record_hash": record_hash}

@app.put("/records/{record_id}")
def update_record(record_id: str, update_in: UpdateRecordInput, current_user: dict = Depends(get_current_user)):
    if current_user["role"] == "PATIENT":
        log_audit(current_user["username"], "UNAUTHORIZED_RECORD_ACCESS", "FAILED", record_id)
        raise HTTPException(status_code=403, detail="Patients cannot edit official medical records.")
        
    if current_user["role"] not in ["DOCTOR", "LAB"]:
        raise HTTPException(status_code=403, detail="Not authorized to edit this record")

    record = get_record(record_id)
    if not record:
        raise HTTPException(status_code=404, detail="Record not found")
        
    if not has_record_access(current_user, record, "EDIT"):
        log_audit(current_user["username"], "UNAUTHORIZED_RECORD_ACCESS", "FAILED", record_id)
        raise HTTPException(status_code=403, detail="Not authorized to edit this record")
        
    now = datetime.now(timezone.utc).isoformat()
    
    enc_metadata = encrypt_record_data(update_in.record_data)
    
    canonical_dict = {
        "record_id": record["record_id"],
        "patient_id": record["patient_id"],
        "record_type": record["record_type"],
        "record_data": update_in.record_data,
        "created_at": record["created_at"],
        "updated_at": now
    }
    
    new_hash = canonical_record_hash(canonical_dict)
    
    update_record_legitimate(record_id, enc_metadata, new_hash, now)
    log_audit(current_user["username"], "RECORD_UPDATED", "SUCCESS", record_id)
    
    merkle_root, record_ids = rebuild_merkle_state()
    block = blockchain.add_block(merkle_root, record_ids)
    insert_block({
        "index": block.index,
        "previous_hash": block.previous_hash,
        "merkle_root": block.merkle_root,
        "record_ids": block.record_ids,
        "timestamp": block.timestamp,
        "hash": block.hash
    })
    
    return {"message": "Record successfully updated and anchored.", "new_hash": new_hash}

@app.delete("/records/{record_id}")
def delete_record_endpoint(record_id: str, current_user: dict = Depends(require_roles(["ADMIN", "DOCTOR"]))):
    record = get_record(record_id)
    if not record:
        raise HTTPException(status_code=404, detail="Record not found")
        
    # Assume ADMIN can delete, DOCTOR can delete if they have EDIT. 
    if current_user["role"] == "DOCTOR" and not has_record_access(current_user, record, "EDIT"):
        log_audit(current_user["username"], "UNAUTHORIZED_RECORD_ACCESS", "FAILED", record_id)
        raise HTTPException(status_code=403, detail="Not authorized to delete this record")
        
    delete_record(record_id)
    log_audit(current_user["username"], "RECORD_DELETED", "SUCCESS", record_id)
    
    merkle_root, record_ids = rebuild_merkle_state()
    block = blockchain.add_block(merkle_root, record_ids)
    insert_block({
        "index": block.index,
        "previous_hash": block.previous_hash,
        "merkle_root": block.merkle_root,
        "record_ids": block.record_ids,
        "timestamp": block.timestamp,
        "hash": block.hash
    })
    
    return {"message": "Record successfully deleted and deletion anchored."}

# --- Sharing Endpoints ---

@app.post("/records/{record_id}/share")
def share_record(record_id: str, share_in: ShareRecordInput, current_user: dict = Depends(require_roles(["PATIENT"]))):
    record = get_record(record_id)
    if not record:
        raise HTTPException(status_code=404, detail="Record not found")
        
    if record["patient_id"] != current_user["username"]:
        log_audit(current_user["username"], "UNAUTHORIZED_RECORD_ACCESS", "FAILED", record_id)
        raise HTTPException(status_code=403, detail="Cannot share another patient's record")
        
    # Check if recipient exists
    recip = get_user_by_username(share_in.recipient_user_id)
    if not recip:
        raise HTTPException(status_code=404, detail="Recipient user not found")
        
    now = datetime.now(timezone.utc).isoformat()
    share_id = str(uuid.uuid4())
    insert_share({
        "share_id": share_id,
        "record_id": record_id,
        "owner_user_id": current_user["username"],
        "recipient_user_id": share_in.recipient_user_id,
        "permission": share_in.permission,
        "created_at": now,
        "active": 1
    })
    log_audit(current_user["username"], "RECORD_SHARED", "SUCCESS", record_id)
    return {"message": "Record shared successfully", "share_id": share_id}

@app.delete("/records/{record_id}/share/{share_id}")
def revoke_record_share(record_id: str, share_id: str, current_user: dict = Depends(require_roles(["PATIENT"]))):
    record = get_record(record_id)
    if not record or record["patient_id"] != current_user["username"]:
        raise HTTPException(status_code=403, detail="Not authorized")
        
    revoke_share(share_id)
    log_audit(current_user["username"], "RECORD_SHARE_REVOKED", "SUCCESS", record_id)
    return {"message": "Share revoked successfully"}

@app.get("/records/{record_id}/shares")
def get_record_shares(record_id: str, current_user: dict = Depends(require_roles(["PATIENT"]))):
    record = get_record(record_id)
    if not record or record["patient_id"] != current_user["username"]:
        raise HTTPException(status_code=403, detail="Not authorized")
        
    shares = get_shares_for_record(record_id)
    return {"shares": shares}


@app.post("/verify/{record_id}")
def verify_record(record_id: str, current_user: dict = Depends(get_current_user)):
    record = get_record(record_id)
    if not record:
        raise HTTPException(status_code=404, detail="Record not found")
        
    if not has_record_access(current_user, record, "VIEW"):
        log_audit(current_user["username"], "UNAUTHORIZED_RECORD_ACCESS", "FAILED", record_id)
        raise HTTPException(status_code=403, detail="Not authorized to verify this record")
        
    log_audit(current_user["username"], "RECORD_VIEWED", "SUCCESS", record_id)
    
    # 1. Decrypt AES-GCM
    try:
        plaintext_data = decrypt_record_data(record)
    except InvalidTag:
        log_audit(current_user["username"], "DECRYPTION_FAILURE", "FAILED", record_id)
        # Even if decryption fails, we must simulate the pipeline failure so the user knows it's TAMPERED safely.
        # We'll just return TAMPERED directly since AES-GCM failed.
        return {"status": "TAMPERED", "detail": "Decryption failed (AES-GCM authentication tag mismatch)"}
        
    canonical_dict = {
        "record_id": record["record_id"],
        "patient_id": record["patient_id"],
        "record_type": record["record_type"],
        "record_data": plaintext_data,
        "created_at": record["created_at"],
        "updated_at": record["updated_at"]
    }
        
    current_hash = canonical_record_hash(canonical_dict)
    
    try:
        original_hash = record_hash_map[record_id]
        index = current_leaves.index(original_hash)
    except (KeyError, ValueError):
        return {"status": "TAMPERED", "detail": "Record not found in cryptographic history"}
        
    original_tree = MerkleTree(current_leaves)
    proof = original_tree.get_proof(index)
    
    latest_block = blockchain.get_latest_block()
    stored_root = latest_block.merkle_root
    
    is_valid = MerkleTree.verify_proof(current_hash, proof, stored_root)
    
    if is_valid:
        return {"status": "VALID", "current_hash": current_hash, "stored_root": stored_root}
    else:
        return {"status": "TAMPERED", "current_hash": current_hash, "stored_root": stored_root}

@app.post("/tamper/{record_id}")
def tamper_record(record_id: str, new_data: Dict[str, Any]):
    # Allow tampering for demonstration purposes
    record = get_record(record_id)
    if not record:
        raise HTTPException(status_code=404, detail="Record not found")
        
    update_record_tamper(record_id)
    return {"message": "Record tampered successfully in SQLite."}

@app.get("/blockchain")
def get_blockchain(current_user: dict = Depends(require_roles(["ADMIN"]))):
    return {"chain": [
        {
            "index": b.index,
            "hash": b.hash,
            "previous_hash": b.previous_hash,
            "merkle_root": b.merkle_root,
            "timestamp": b.timestamp,
            "record_ids": b.record_ids
        } for b in blockchain.chain
    ], "valid": blockchain.is_chain_valid()}

@app.get("/users")
def get_users(current_user: dict = Depends(get_current_user)):
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute('SELECT username, role FROM users WHERE active = 1')
    rows = cursor.fetchall()
    conn.close()
    return {"users": [dict(r) for r in rows]}

@app.get("/audit-logs")
def get_audit_logs(current_user: dict = Depends(require_roles(["ADMIN"]))):
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM audit_logs ORDER BY timestamp DESC')
    rows = cursor.fetchall()
    conn.close()
    return {"logs": [dict(r) for r in rows]}

@app.post("/admin/reset-demo-data")
def reset_demo_data(current_user: dict = Depends(require_roles(["ADMIN"]))):
    import shutil
    # 1. Backup Database
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    backup_path = DB_PATH.replace("healthcare.db", f"healthcare_backup_{timestamp}.db")
    shutil.copyfile(DB_PATH, backup_path)
    
    # 2. Reset Data
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM users WHERE role != 'ADMIN'")
    cursor.execute("DELETE FROM records")
    cursor.execute("DELETE FROM record_shares")
    cursor.execute("DELETE FROM audit_logs")
    cursor.execute("DELETE FROM blocks")
    # Reset auto-increment sequences safely
    cursor.execute("DELETE FROM sqlite_sequence WHERE name IN ('audit_logs')")
    conn.commit()
    conn.close()
    
    # 3. Reset in-memory cryptographic state
    global blockchain, current_leaves, record_hash_map
    blockchain = Blockchain()
    current_leaves = []
    record_hash_map = {}
    
    # 4. Insert new Genesis block
    b = blockchain.chain[0]
    insert_block({
        "index": b.index,
        "previous_hash": b.previous_hash,
        "merkle_root": b.merkle_root,
        "record_ids": b.record_ids,
        "timestamp": b.timestamp,
        "hash": b.hash
    })
    
    # 5. Log the reset action so it's not silent
    log_audit(current_user["username"], "DEMO_DATA_RESET", "SUCCESS")
    
    return {"message": "Demo data reset successfully", "backup": backup_path}

@app.get("/dashboard/stats")
def get_dashboard_stats(current_user: dict = Depends(get_current_user)):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    if current_user["role"] == "ADMIN":
        cursor.execute('SELECT COUNT(*) FROM records')
        total_records = cursor.fetchone()[0]
        cursor.execute('SELECT COUNT(*) FROM record_shares WHERE active = 1')
        active_shares = cursor.fetchone()[0]
    elif current_user["role"] == "PATIENT":
        cursor.execute('SELECT COUNT(*) FROM records WHERE patient_id = ?', (current_user["username"],))
        total_records = cursor.fetchone()[0]
        cursor.execute('SELECT COUNT(*) FROM record_shares WHERE owner_user_id = ? AND active = 1', (current_user["username"],))
        active_shares = cursor.fetchone()[0]
    else:
        # DOCTOR / LAB get a rough count based on their active shares
        cursor.execute('SELECT COUNT(*) FROM record_shares WHERE recipient_user_id = ? AND active = 1', (current_user["username"],))
        active_shares = cursor.fetchone()[0]
        total_records = active_shares
    conn.close()
    
    return {
        "total_records": total_records,
        "blocks": len(blockchain.chain),
        "active_shares": active_shares,
        "chain_valid": blockchain.is_chain_valid(),
        "merkle_root": blockchain.get_latest_block().merkle_root if len(blockchain.chain) > 0 else ""
    }

@app.get("/merkle/tree")
def get_merkle_tree(current_user: dict = Depends(get_current_user)):
    # Returns the full merkle tree to render
    tree = MerkleTree(current_leaves)
    return {
        "root": tree.get_root(),
        "leaves": current_leaves,
        "levels": tree.get_tree_structure(),
        "record_map": {v: k for k, v in record_hash_map.items()} # map hash to record_id
    }
