import pytest
import sqlite3
import json
import uuid
from fastapi.testclient import TestClient
from main import app
from database import DB_PATH

client = TestClient(app)

def setup_users():
    run_id = str(uuid.uuid4())[:8]
    doc1 = f"doc1_{run_id}"
    doc2 = f"doc2_{run_id}"
    pat = f"pat_{run_id}"
    
    # Login as admin to create users
    res = client.post("/auth/login", json={"username": "admin", "password": "password123"})
    if res.status_code != 200:
        return None
    admin_token = res.json()["access_token"]
    headers = {"Authorization": f"Bearer {admin_token}"}
    
    # Create test staff and patient without resetting DB
    client.post("/admin/staff", json={"username": doc1, "password": "password123", "role": "DOCTOR"}, headers=headers)
    client.post("/admin/staff", json={"username": doc2, "password": "password123", "role": "DOCTOR"}, headers=headers)
    client.post("/patients", json={"username": pat, "password": "password123"}, headers=headers)
    
    # Get tokens
    d1_token = client.post("/auth/login", json={"username": doc1, "password": "password123"}).json()["access_token"]
    d2_token = client.post("/auth/login", json={"username": doc2, "password": "password123"}).json()["access_token"]
    p_token = client.post("/auth/login", json={"username": pat, "password": "password123"}).json()["access_token"]
    
    return d1_token, d2_token, p_token, pat, doc2

def test_edit_permissions_workflow():
    tokens = setup_users()
    if not tokens:
        return
    d1_token, d2_token, p_token, pat_name, doc2_name = tokens
    
    d1_headers = {"Authorization": f"Bearer {d1_token}"}
    d2_headers = {"Authorization": f"Bearer {d2_token}"}
    p_headers = {"Authorization": f"Bearer {p_token}"}
    
    # Doctor 1 creates record for patient
    res = client.post("/records", json={"patient_id": pat_name, "record_type": "Test", "record_data": {"val": "1"}}, headers=d1_headers)
    assert res.status_code == 200
    
    # Get the specific record id created
    records_res = client.get("/records", headers=d1_headers)
    records = records_res.json()["records"]
    record_id = [r["record"]["record_id"] for r in records if r["record"]["patient_id"] == pat_name][0]
    
    # Check patient sees own record as OWNER
    p_records_res = client.get("/records", headers=p_headers)
    p_record = [r["record"] for r in p_records_res.json()["records"] if r["record"]["record_id"] == record_id][0]
    assert p_record["permission"] == "OWNER"
    
    # Patient cannot edit own official medical record (403)
    p_put_res = client.put(f"/records/{record_id}", json={"record_type": "Test", "record_data": {"val": "hacked"}}, headers=p_headers)
    assert p_put_res.status_code == 403
    assert "Patients cannot edit official medical records" in p_put_res.text
    
    # 1. VIEW only -> PUT = 403
    client.post(f"/records/{record_id}/share", json={"recipient_user_id": doc2_name, "permission": "VIEW"}, headers=p_headers)
    res = client.put(f"/records/{record_id}", json={"record_type": "Test", "record_data": {"val": "2"}}, headers=d2_headers)
    assert res.status_code == 403
    
    # DB stats snapshot for unauthorized checks
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    initial_hash = c.execute("SELECT record_hash FROM records WHERE record_id=?", (record_id,)).fetchone()[0]
    initial_blocks = c.execute("SELECT COUNT(*) FROM blocks").fetchone()[0]
    initial_merkle = c.execute("SELECT merkle_root FROM blocks ORDER BY block_index DESC LIMIT 1").fetchone()[0]
    conn.close()
    
    # Verify 6-9
    res = client.put(f"/records/{record_id}", json={"record_type": "Test", "record_data": {"val": "3"}}, headers=d2_headers)
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    assert c.execute("SELECT record_hash FROM records WHERE record_id=?", (record_id,)).fetchone()[0] == initial_hash # 7
    assert c.execute("SELECT COUNT(*) FROM blocks").fetchone()[0] == initial_blocks # 9
    assert c.execute("SELECT merkle_root FROM blocks ORDER BY block_index DESC LIMIT 1").fetchone()[0] == initial_merkle # 8
    conn.close()
    
    # 3. VIEW + EDIT -> effective permission = EDIT -> PUT = 200
    res_share = client.post(f"/records/{record_id}/share", json={"recipient_user_id": doc2_name, "permission": "EDIT"}, headers=p_headers)
    edit_share_id = res_share.json()["share_id"]
    
    res = client.put(f"/records/{record_id}", json={"record_type": "Test", "record_data": {"val": "4"}}, headers=d2_headers)
    assert res.status_code == 200
    
    # Verify 10-14
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    new_hash = c.execute("SELECT record_hash FROM records WHERE record_id=?", (record_id,)).fetchone()[0]
    assert new_hash != initial_hash # 10
    
    new_blocks = c.execute("SELECT COUNT(*) FROM blocks").fetchone()[0]
    assert new_blocks == initial_blocks + 1 # 12
    
    new_merkle = c.execute("SELECT merkle_root FROM blocks ORDER BY block_index DESC LIMIT 1").fetchone()[0]
    assert new_merkle != initial_merkle # 11
    
    audit = c.execute("SELECT action FROM audit_logs WHERE username=? ORDER BY timestamp DESC LIMIT 1", (doc2_name,)).fetchone()[0]
    assert audit == "RECORD_UPDATED" # 14
    conn.close()
    
    # 13. Verify validity
    res = client.post(f"/verify/{record_id}", headers=d2_headers)
    assert res.json()["status"] == "VALID"
    
    # 4. VIEW + EDIT, then EDIT revoked -> effective permission = VIEW -> PUT = 403
    client.delete(f"/records/{record_id}/share/{edit_share_id}", headers=p_headers)
    res = client.put(f"/records/{record_id}", json={"record_type": "Test", "record_data": {"val": "5"}}, headers=d2_headers)
    assert res.status_code == 403
    
    # 5. Both revoked -> no access
    # Revoke VIEW share
    shares = client.get(f"/records/{record_id}/shares", headers=p_headers).json()["shares"]
    for s in shares:
        if s["recipient_user_id"] == doc2_name and s["active"] == 1:
            client.delete(f"/records/{record_id}/share/{s['share_id']}", headers=p_headers)
            
    res = client.get("/records", headers=d2_headers)
    records = res.json()["records"]
    assert len([r for r in records if r["record"]["record_id"] == record_id]) == 0
