import requests
import json
import os

BASE_URL = "http://127.0.0.1:8001"

def test_e2e():
    print("0. Resetting Database and Blockchain...")
    requests.post(f"{BASE_URL}/dev/reset")

    print("\n[Auth] Logging in as DOCTOR, PATIENT1, LAB1, and ADMIN...")
    doc_token = requests.post(f"{BASE_URL}/auth/login", json={"username": "doctor1", "password": "password123"}).json()["access_token"]
    pat_token = requests.post(f"{BASE_URL}/auth/login", json={"username": "patient1", "password": "password123"}).json()["access_token"]
    lab_token = requests.post(f"{BASE_URL}/auth/login", json={"username": "lab1", "password": "password123"}).json()["access_token"]
    admin_token = requests.post(f"{BASE_URL}/auth/login", json={"username": "admin", "password": "password123"}).json()["access_token"]
    
    doc_headers = {"Authorization": f"Bearer {doc_token}"}
    pat_headers = {"Authorization": f"Bearer {pat_token}"}
    lab_headers = {"Authorization": f"Bearer {lab_token}"}
    admin_headers = {"Authorization": f"Bearer {admin_token}"}

    print("\n1. Adding 3 healthcare records as DOCTOR (Encrypted internally)...")
    records = []
    for i in range(1, 4):
        res = requests.post(f"{BASE_URL}/records", json={
            "patient_id": "patient1",
            "record_type": "Blood Test",
            "record_data": {"val": i}
        }, headers=doc_headers).json()
        print(f"Added encrypted record: {res['record']['record_id']}")
        records.append(res['record']['record_id'])
    
    print("\n2. Verifying every record before update as PATIENT1 (Decryption + Hash match)...")
    for rec_id in records:
        res = requests.post(f"{BASE_URL}/verify/{rec_id}", headers=pat_headers).json()
        assert res['status'] == 'VALID'
        
    print("\n3. Testing Legitimate Record Update as DOCTOR (Auto-shared on creation)...")
    res = requests.put(f"{BASE_URL}/records/{records[0]}", json={"record_data": {"val": 100}}, headers=doc_headers).json()
    assert "new_hash" in res
    
    print("\n4. Sharing record 0 with LAB1 (VIEW)...")
    share_res = requests.post(f"{BASE_URL}/records/{records[0]}/share", json={"recipient_user_id": "lab1", "permission": "VIEW"}, headers=pat_headers).json()
    share_id = share_res["share_id"]
    
    print("\n5. Verifying shared record as LAB1 (Should be VALID)...")
    res = requests.post(f"{BASE_URL}/verify/{records[0]}", headers=lab_headers).json()
    assert res['status'] == 'VALID'
    
    print("\n6. Revoking share with LAB1...")
    requests.delete(f"{BASE_URL}/records/{records[0]}/share/{share_id}", headers=pat_headers)
    
    print("\n7. Attempting to verify revoked record as LAB1 (Should be FORBIDDEN)...")
    res = requests.post(f"{BASE_URL}/verify/{records[0]}", headers=lab_headers)
    assert res.status_code == 403
    
    print("\n8. Tampering with record 2 (Corrupting AES Ciphertext directly in SQLite)...")
    requests.post(f"{BASE_URL}/tamper/{records[1]}", json={"val": "TAMPERED"})
    
    print("\n9. Verifying tampered record as PATIENT1 (Should be TAMPERED due to AES-GCM Auth Tag Mismatch)...")
    res_verify_tampered = requests.post(f"{BASE_URL}/verify/{records[1]}", headers=pat_headers).json()
    assert res_verify_tampered['status'] == 'TAMPERED'
    print(res_verify_tampered)
        
    print("\n10. Testing Legitimate Deletion as ADMIN...")
    requests.delete(f"{BASE_URL}/records/{records[2]}", headers=admin_headers)
    
    print("\n11. Testing blockchain validation after operations as ADMIN...")
    res = requests.get(f"{BASE_URL}/blockchain", headers=admin_headers).json()
    assert res['valid'] == True
    
    print(f"\nBlocks in chain: {len(res['chain'])}")
    
    print("\nAll Encryption, Sharing, Persistence, and Security Checks Passed!")

if __name__ == "__main__":
    test_e2e()
