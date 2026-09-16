import sqlite3
import json
from typing import List, Dict, Any
import os

DB_PATH = os.path.join(os.path.dirname(__file__), "healthcare.db")

def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('PRAGMA foreign_keys = ON')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS records (
            record_id TEXT PRIMARY KEY,
            patient_id TEXT REFERENCES users(username),
            record_type TEXT,
            encrypted_data TEXT,
            data_nonce TEXT,
            data_tag TEXT,
            encrypted_dek TEXT,
            dek_nonce TEXT,
            dek_tag TEXT,
            record_hash TEXT,
            created_at TEXT,
            updated_at TEXT
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS record_shares (
            share_id TEXT PRIMARY KEY,
            record_id TEXT,
            owner_user_id TEXT,
            recipient_user_id TEXT,
            permission TEXT,
            created_at TEXT,
            active INTEGER
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS blocks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            block_index INTEGER,
            previous_hash TEXT,
            merkle_root TEXT,
            record_ids TEXT,
            timestamp REAL,
            block_hash TEXT
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            user_id TEXT PRIMARY KEY,
            username TEXT UNIQUE,
            password_hash TEXT,
            role TEXT,
            created_at TEXT,
            active INTEGER
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS audit_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT,
            username TEXT,
            action TEXT,
            record_id TEXT,
            status TEXT
        )
    ''')
    conn.commit()
    conn.close()

def clear_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('DROP TABLE IF EXISTS records')
    cursor.execute('DROP TABLE IF EXISTS record_shares')
    cursor.execute('DROP TABLE IF EXISTS blocks')
    cursor.execute('DROP TABLE IF EXISTS users')
    cursor.execute('DROP TABLE IF EXISTS audit_logs')
    conn.commit()
    conn.close()
    init_db()

# --- Users ---

def insert_user(user: dict):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO users (user_id, username, password_hash, role, created_at, active)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (user['user_id'], user['username'], user['password_hash'], user['role'], user['created_at'], user['active']))
    conn.commit()
    conn.close()

def get_user_by_username(username: str) -> dict:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM users WHERE username = ?', (username,))
    row = cursor.fetchone()
    conn.close()
    if row:
        return dict(row)
    return None

# --- Audit Logs ---
def log_audit(username: str, action: str, status: str, record_id: str = None):
    from datetime import datetime, timezone
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO audit_logs (timestamp, username, action, record_id, status)
        VALUES (?, ?, ?, ?, ?)
    ''', (datetime.now(timezone.utc).isoformat(), username, action, record_id, status))
    conn.commit()
    conn.close()

# --- Blocks ---

def insert_block(block: dict):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO blocks (block_index, previous_hash, merkle_root, record_ids, timestamp, block_hash)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (block['index'], block['previous_hash'], block['merkle_root'], json.dumps(block['record_ids']), block['timestamp'], block['hash']))
    conn.commit()
    conn.close()

def get_all_blocks() -> List[dict]:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM blocks ORDER BY block_index ASC')
    rows = cursor.fetchall()
    conn.close()
    blocks = []
    for r in rows:
        blocks.append({
            "index": r["block_index"],
            "previous_hash": r["previous_hash"],
            "merkle_root": r["merkle_root"],
            "record_ids": json.loads(r["record_ids"]),
            "timestamp": r["timestamp"],
            "hash": r["block_hash"]
        })
    return blocks

# --- Records ---

def insert_record(record: dict):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO records (
            record_id, patient_id, record_type, 
            encrypted_data, data_nonce, data_tag, 
            encrypted_dek, dek_nonce, dek_tag, 
            record_hash, created_at, updated_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        record['record_id'], record['patient_id'], record['record_type'], 
        record['encrypted_data'], record['data_nonce'], record['data_tag'], 
        record['encrypted_dek'], record['dek_nonce'], record['dek_tag'], 
        record.get('record_hash', ''), record['created_at'], record['updated_at']
    ))
    conn.commit()
    conn.close()

def update_record_legitimate(record_id: str, encryption_metadata: dict, new_hash: str, updated_at: str):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        UPDATE records 
        SET encrypted_data = ?, data_nonce = ?, data_tag = ?,
            encrypted_dek = ?, dek_nonce = ?, dek_tag = ?,
            record_hash = ?, updated_at = ?
        WHERE record_id = ?
    ''', (
        encryption_metadata['encrypted_data'], encryption_metadata['data_nonce'], encryption_metadata['data_tag'],
        encryption_metadata['encrypted_dek'], encryption_metadata['dek_nonce'], encryption_metadata['dek_tag'],
        new_hash, updated_at, record_id
    ))
    conn.commit()
    conn.close()

def delete_record(record_id: str):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('DELETE FROM records WHERE record_id = ?', (record_id,))
    cursor.execute('DELETE FROM record_shares WHERE record_id = ?', (record_id,))
    conn.commit()
    conn.close()

def get_record(record_id: str) -> dict:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM records WHERE record_id = ?', (record_id,))
    row = cursor.fetchone()
    conn.close()
    if row:
        return dict(row)
    return None

def get_all_records() -> List[dict]:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM records ORDER BY created_at ASC')
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]

def update_record_tamper(record_id: str):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    # Explicitly DO NOT update record_hash. Simulating a DB-level tamper.
    # We corrupt the encrypted_data by changing the first few characters.
    cursor.execute('SELECT encrypted_data FROM records WHERE record_id = ?', (record_id,))
    row = cursor.fetchone()
    if row:
        tampered_hex = '0000' + row[0][4:] if len(row[0]) >= 4 else '0000'
        cursor.execute('UPDATE records SET encrypted_data = ? WHERE record_id = ?', (tampered_hex, record_id))
    conn.commit()
    conn.close()

# --- Sharing ---

def insert_share(share: dict):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO record_shares (share_id, record_id, owner_user_id, recipient_user_id, permission, created_at, active)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (share['share_id'], share['record_id'], share['owner_user_id'], share['recipient_user_id'], share['permission'], share['created_at'], share['active']))
    conn.commit()
    conn.close()

def revoke_share(share_id: str):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('UPDATE record_shares SET active = 0 WHERE share_id = ?', (share_id,))
    conn.commit()
    conn.close()

def get_shares_for_record(record_id: str) -> List[dict]:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM record_shares WHERE record_id = ? AND active = 1', (record_id,))
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]

def get_share_for_user(record_id: str, recipient_user_id: str) -> dict:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute('SELECT permission FROM record_shares WHERE record_id = ? AND recipient_user_id = ? AND active = 1', (record_id, recipient_user_id))
    rows = cursor.fetchall()
    conn.close()
    
    if not rows:
        return None
        
    permissions = [r["permission"] for r in rows]
    if "EDIT" in permissions:
        return {"permission": "EDIT"}
    elif "VIEW" in permissions:
        return {"permission": "VIEW"}
    return None

def get_shared_records_for_user(recipient_user_id: str) -> List[str]:
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('SELECT record_id FROM record_shares WHERE recipient_user_id = ? AND active = 1', (recipient_user_id,))
    rows = cursor.fetchall()
    conn.close()
    return [r[0] for r in rows]
