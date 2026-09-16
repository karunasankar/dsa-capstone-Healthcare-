import pytest
from fastapi.testclient import TestClient
from main import app
from database import init_db
import sqlite3
import os
import json

client = TestClient(app)

@pytest.fixture(autouse=True)
def setup_db():
    init_db()
    yield

def get_token(username, password):
    res = client.post("/auth/login", json={"username": username, "password": password})
    return res.json()["access_token"]

def test_patient_validation_and_creation():
    # Setup roles by registering them (allowed in test setup prototype)
    client.post("/auth/register", json={"username": "admin1", "password": "password123", "role": "ADMIN"})
    client.post("/auth/register", json={"username": "doc1", "password": "password123", "role": "DOCTOR"})
    client.post("/auth/register", json={"username": "lab1", "password": "password123", "role": "LAB"})
    client.post("/auth/register", json={"username": "pat1", "password": "password123", "role": "PATIENT"})
    
    admin_token = get_token("admin1", "password123")
    doc_token = get_token("doc1", "password123")
    lab_token = get_token("lab1", "password123")
    pat_token = get_token("pat1", "password123")
    
    # 1. Admin creates patient -> PASS
    res = client.post("/patients", json={"username": "new_pat", "password": "password123"}, headers={"Authorization": f"Bearer {admin_token}"})
    assert res.status_code == 200
    
    # 2. Duplicate patient -> REJECT
    res = client.post("/patients", json={"username": "new_pat", "password": "password1232"}, headers={"Authorization": f"Bearer {admin_token}"})
    assert res.status_code == 400
    
    # 3. Doctor creates patient -> 403
    res = client.post("/patients", json={"username": "new_pat2", "password": "password123"}, headers={"Authorization": f"Bearer {doc_token}"})
    assert res.status_code == 403
    
    # 4. Lab creates patient -> 403
    res = client.post("/patients", json={"username": "new_pat3", "password": "password123"}, headers={"Authorization": f"Bearer {lab_token}"})
    assert res.status_code == 403
    
    # 5. Patient creates patient -> 403
    res = client.post("/patients", json={"username": "new_pat4", "password": "password123"}, headers={"Authorization": f"Bearer {pat_token}"})
    assert res.status_code == 403
    
    # 6. Doctor creates record for existing patient -> PASS
    res = client.post("/records", json={"patient_id": "new_pat", "record_type": "Blood Test", "record_data": {"val": 1}}, headers={"Authorization": f"Bearer {doc_token}"})
    assert res.status_code == 200
    
    # 7. Doctor creates record for nonexistent patient -> REJECT
    res = client.post("/records", json={"patient_id": "ghost_pat", "record_type": "Blood Test", "record_data": {"val": 1}}, headers={"Authorization": f"Bearer {doc_token}"})
    assert res.status_code == 404
    
    # 8. Doctor creates record for doctor1 as patient -> REJECT
    res = client.post("/records", json={"patient_id": "doc1", "record_type": "Blood Test", "record_data": {"val": 1}}, headers={"Authorization": f"Bearer {doc_token}"})
    assert res.status_code == 400
    
    # 9. Patient sees only own records -> PASS
    res = client.get("/records", headers={"Authorization": f"Bearer {get_token('new_pat', 'password123')}"})
    assert len(res.json()["records"]) == 1
    
    res_pat1 = client.get("/records", headers={"Authorization": f"Bearer {pat_token}"})
    assert len(res_pat1.json()["records"]) == 0
    
    # Check GET /patients
    res_get_pat = client.get("/patients", headers={"Authorization": f"Bearer {doc_token}"})
    assert res_get_pat.status_code == 200
    assert any(p["username"] == "new_pat" for p in res_get_pat.json()["patients"])
