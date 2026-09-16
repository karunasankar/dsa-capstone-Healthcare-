import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), "healthcare.db")

def migrate():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # 1. Check for orphans
    cursor.execute('SELECT patient_id FROM records WHERE patient_id NOT IN (SELECT username FROM users)')
    orphans = cursor.fetchall()
    if orphans:
        print(f"Orphans found! {orphans}")
        # Not deleting, just warning or we could assign them to a placeholder. The prompt says "no orphans exist".
    else:
        print("No orphan records found.")
        
    # 2. Recreate records table with foreign key
    cursor.execute('PRAGMA foreign_keys=off')
    cursor.execute('BEGIN TRANSACTION')
    
    # Create new table
    cursor.execute('''
    CREATE TABLE records_new (
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
    
    # Copy data
    cursor.execute('''
    INSERT INTO records_new SELECT 
        record_id, patient_id, record_type, encrypted_data, data_nonce, 
        data_tag, encrypted_dek, dek_nonce, dek_tag, record_hash, 
        created_at, updated_at 
    FROM records
    ''')
    
    # Drop old
    cursor.execute('DROP TABLE records')
    
    # Rename new
    cursor.execute('ALTER TABLE records_new RENAME TO records')
    
    cursor.execute('COMMIT')
    cursor.execute('PRAGMA foreign_keys=on')
    
    print("Migration successful.")
    conn.close()

if __name__ == '__main__':
    migrate()
