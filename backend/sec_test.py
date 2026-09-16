import urllib.request
import urllib.error
import json
import sqlite3

BASE_URL = "http://127.0.0.1:8001"
DB_PATH = "healthcare.db"

def test_security():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    # Get record id
    record = c.execute("SELECT record_id, record_hash FROM records WHERE patient_id='patient101'").fetchone()
    if not record:
        print("Record not found for patient101")
        return
    record_id, initial_hash = record
    
    initial_blocks = c.execute("SELECT COUNT(*) FROM blocks").fetchone()[0]
    initial_merkle_root = c.execute("SELECT merkle_root FROM blocks ORDER BY \"index\" DESC LIMIT 1").fetchone()[0]
    
    # Login as doctor2
    data = json.dumps({"username": "doctor2", "password": "password123"}).encode('utf-8')
    req = urllib.request.Request(f"{BASE_URL}/auth/login", data=data, headers={'Content-Type': 'application/json'})
    with urllib.request.urlopen(req) as response:
        token = json.loads(response.read())["access_token"]
    
    # Attempt PUT
    put_data = json.dumps({"record_data": {"note": "hacked"}, "record_type": "Blood Test"}).encode('utf-8')
    req_put = urllib.request.Request(
        f"{BASE_URL}/records/{record_id}", 
        data=put_data, 
        headers={'Content-Type': 'application/json', 'Authorization': f'Bearer {token}'}, 
        method='PUT'
    )
    
    status_code = None
    resp_body = None
    try:
        with urllib.request.urlopen(req_put) as response:
            status_code = response.getcode()
            resp_body = response.read()
    except urllib.error.HTTPError as e:
        status_code = e.code
        resp_body = e.read()
        
    print(f"HTTP Status: {status_code}")
    print(f"Response: {resp_body.decode('utf-8')}")
    
    # Check conditions
    final_record = c.execute("SELECT record_hash FROM records WHERE record_id=?", (record_id,)).fetchone()
    final_hash = final_record[0]
    
    final_blocks = c.execute("SELECT COUNT(*) FROM blocks").fetchone()[0]
    final_merkle_root = c.execute("SELECT merkle_root FROM blocks ORDER BY \"index\" DESC LIMIT 1").fetchone()[0]
    
    audit_log = c.execute("SELECT action, status FROM audit_logs WHERE username='doctor2' ORDER BY timestamp DESC LIMIT 1").fetchone()
    
    print("\n--- RESULTS ---")
    print(f"1. HTTP 403 Forbidden: {'PASS' if status_code == 403 else 'FAIL'}")
    print(f"2. SHA-256 Hash unchanged: {'PASS' if initial_hash == final_hash else 'FAIL'}")
    print(f"3. Merkle root unchanged: {'PASS' if initial_merkle_root == final_merkle_root else 'FAIL'}")
    print(f"4. No new block created: {'PASS' if initial_blocks == final_blocks else 'FAIL'}")
    
    if audit_log and audit_log[0] == "UNAUTHORIZED_RECORD_ACCESS" and audit_log[1] == "FAILED":
        print("5. Unauthorized-access audit event recorded: PASS")
    else:
        print(f"5. Unauthorized-access audit event recorded: FAIL (Found {audit_log})")
        
    conn.close()

if __name__ == "__main__":
    test_security()
