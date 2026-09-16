import pytest
import os
from crypto import hash_data, canonical_record_hash, MerkleTree, Blockchain
from fastapi.testclient import TestClient
from main import app, blockchain, current_leaves, record_hash_map

# Provide test key
os.environ["HEALTHCARE_ENCRYPTION_KEY"] = "b49a9884c3deb3f9ef932d0cd6c01e0fad6497b477993bb77e6f41bdc9627eb1"

client = TestClient(app)

def test_sha256_consistency():
    data = "test data"
    hash1 = hash_data(data)
    hash2 = hash_data(data)
    assert hash1 == hash2

def test_canonical_hash():
    record1 = {"a": 1, "b": 2, "record_hash": "ignore_me"}
    record2 = {"b": 2, "a": 1, "record_hash": "ignore_me_too"}
    assert canonical_record_hash(record1) == canonical_record_hash(record2)

def test_merkle_tree():
    leaves = [hash_data("A"), hash_data("B"), hash_data("C")]
    tree = MerkleTree(leaves)
    root = tree.get_root()
    proof = tree.get_proof(0)
    assert MerkleTree.verify_proof(leaves[0], proof, root) == True
    assert MerkleTree.verify_proof(hash_data("D"), proof, root) == False

def test_blockchain_validation():
    bc = Blockchain()
    bc.add_block("root1", ["r1"])
    bc.add_block("root2", ["r2"])
    assert bc.is_chain_valid() == True
    
    bc.chain[1].merkle_root = "tampered"
    assert bc.is_chain_valid() == False

def test_api_workflow_encryption_sharing():
    client.post("/dev/reset")
    
    res_login = client.post("/auth/login", json={"username": "doctor1", "password": "password123"})
    doc_token = res_login.json()["access_token"]
    doc_headers = {"Authorization": f"Bearer {doc_token}"}
    
    # Doctor creates record for patient1
    res = client.post("/records", json={
        "patient_id": "patient1",
        "record_type": "Blood Test",
        "record_data": {"blood_type": "O-"}
    }, headers=doc_headers)
    assert res.status_code == 200
    record_id = res.json()["record"]["record_id"]
    
    # Patient1 logs in
    pat_token = client.post("/auth/login", json={"username": "patient1", "password": "password123"}).json()["access_token"]
    pat_headers = {"Authorization": f"Bearer {pat_token}"}
    
    # Patient1 verifies successfully (tests decryption + AES-GCM + Merkle)
    res_verify = client.post(f"/verify/{record_id}", headers=pat_headers)
    assert res_verify.status_code == 200
    assert res_verify.json()["status"] == "VALID"
    
    # Patient1 shares with lab1 (VIEW)
    share_res = client.post(f"/records/{record_id}/share", json={"recipient_user_id": "lab1", "permission": "VIEW"}, headers=pat_headers)
    assert share_res.status_code == 200
    share_id = share_res.json()["share_id"]
    
    # Lab1 logs in, retrieves shared record
    lab_token = client.post("/auth/login", json={"username": "lab1", "password": "password123"}).json()["access_token"]
    lab_headers = {"Authorization": f"Bearer {lab_token}"}
    
    res_verify_lab = client.post(f"/verify/{record_id}", headers=lab_headers)
    assert res_verify_lab.status_code == 200 # Access granted due to share
    
    # Lab1 tries to PUT (edit) -> Should be 403 because lab only has VIEW (and only DOCTORS can edit anyway)
    # Let's test doctor with VIEW editing
    # Share with doctor2 (assume patient1 shares)
    client.post("/auth/register", json={"username": "doctor2", "password": "password123", "role": "DOCTOR"})
    doc2_token = client.post("/auth/login", json={"username": "doctor2", "password": "password123"}).json()["access_token"]
    doc2_headers = {"Authorization": f"Bearer {doc2_token}"}
    
    client.post(f"/records/{record_id}/share", json={"recipient_user_id": "doctor2", "permission": "VIEW"}, headers=pat_headers)
    
    res_put = client.put(f"/records/{record_id}", json={"record_data": {"blood_type": "A+"}}, headers=doc2_headers)
    assert res_put.status_code == 403 # Only VIEW permission
    
    # Patient1 revokes lab1
    client.delete(f"/records/{record_id}/share/{share_id}", headers=pat_headers)
    
    # Lab1 access now blocked
    res_verify_lab2 = client.post(f"/verify/{record_id}", headers=lab_headers)
    assert res_verify_lab2.status_code == 403
    
    # Tamper with the encrypted SQLite data directly
    client.post(f"/tamper/{record_id}", json={"blood_type": "AB+"}) # This endpoint now flips the hex in encrypted_data directly
    
    # Verify tampered detects AES-GCM tag mismatch
    res_verify_tampered = client.post(f"/verify/{record_id}", headers=pat_headers)
    assert res_verify_tampered.status_code == 200
    assert res_verify_tampered.json()["status"] == "TAMPERED"

def test_auth_rejection():
    # Attempt to access records without token
    res = client.get("/records")
    assert res.status_code == 401
    
    # Attempt to access blockchain without ADMIN
    res_login_pat = client.post("/auth/login", json={"username": "patient1", "password": "password123"})
    pat_token = res_login_pat.json()["access_token"]
    pat_headers = {"Authorization": f"Bearer {pat_token}"}
    
    res_bc = client.get("/blockchain", headers=pat_headers)
    assert res_bc.status_code == 403
    
    # Access blockchain with ADMIN
    res_login_admin = client.post("/auth/login", json={"username": "admin", "password": "password123"})
    admin_token = res_login_admin.json()["access_token"]
    admin_headers = {"Authorization": f"Bearer {admin_token}"}
    
    res_bc_admin = client.get("/blockchain", headers=admin_headers)
    assert res_bc_admin.status_code == 200
