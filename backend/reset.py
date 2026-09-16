import sqlite3
import os
import shutil

DB_PATH = os.path.join(os.path.dirname(__file__), "healthcare.db")
BACKUP_PATH = os.path.join(os.path.dirname(__file__), "healthcare_backup.db")

def reset_db():
    print(f"Creating backup at {BACKUP_PATH}")
    shutil.copyfile(DB_PATH, BACKUP_PATH)
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Check stats before reset
    cursor.execute("SELECT COUNT(*) FROM users WHERE role = 'PATIENT'")
    patients_count = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM users WHERE role = 'DOCTOR'")
    doctors_count = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM records")
    records_count = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM record_shares")
    shares_count = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM audit_logs")
    audit_count = cursor.fetchone()[0]
    
    # 2 & 3. Delete PATIENT and DOCTOR accounts
    cursor.execute("DELETE FROM users WHERE role IN ('PATIENT', 'DOCTOR')")
    
    # 2. Delete ALL records, shares, and audit entries
    cursor.execute("DELETE FROM record_shares")
    cursor.execute("DELETE FROM records")
    cursor.execute("DELETE FROM audit_logs")
    
    # 4. Reset Blockchain
    # The genesis block should be the only one remaining. In crypto.py / main.py 
    # it creates index 0 on init if no blocks. Let's delete all blocks and let main.py recreate or just keep index 0.
    # Actually, Blockchain() initializes genesis block at index 0 if chain is empty.
    # We will just DELETE ALL blocks so main.py will rebuild genesis on restart.
    cursor.execute("DELETE FROM blocks")
    
    conn.commit()
    
    # Verify deletions
    cursor.execute("SELECT COUNT(*) FROM records")
    assert cursor.fetchone()[0] == 0, "Records not cleared"
    
    cursor.execute("SELECT COUNT(*) FROM record_shares")
    assert cursor.fetchone()[0] == 0, "Shares not cleared"
    
    conn.close()
    
    print("--- Reset Complete ---")
    print(f"Patients removed: {patients_count}")
    print(f"Doctors removed: {doctors_count}")
    print(f"Records removed: {records_count}")
    print(f"Shares removed: {shares_count}")
    print(f"Audit entries removed: {audit_count}")

if __name__ == '__main__':
    reset_db()
