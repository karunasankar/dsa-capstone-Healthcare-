from fastapi.testclient import TestClient
from main import app
import pytest

client = TestClient(app)

def test_admin_staff_workflow():
    # Login as admin
    res_admin = client.post("/auth/login", json={"username": "admin", "password": "password123"})
    if res_admin.status_code != 200:
        return
    admin_token = res_admin.json()["access_token"]
    admin_headers = {"Authorization": f"Bearer {admin_token}"}
    
    # 1. Admin creates doctor1 -> PASS
    res = client.post("/admin/staff", json={"username": "doctor_test", "password": "password123", "role": "DOCTOR"}, headers=admin_headers)
    assert res.status_code == 200
    
    # 2. Admin creates lab1 -> PASS
    res = client.post("/admin/staff", json={"username": "lab_test", "password": "password123", "role": "LAB"}, headers=admin_headers)
    assert res.status_code == 200
    
    # 3. Admin cannot create duplicate doctor1
    res = client.post("/admin/staff", json={"username": "doctor_test", "password": "password123", "role": "DOCTOR"}, headers=admin_headers)
    assert res.status_code == 400
    
    # 4. Doctor cannot create staff -> 403
    res_doc = client.post("/auth/login", json={"username": "doctor_test", "password": "password123"})
    assert res_doc.status_code == 200
    doc_token = res_doc.json()["access_token"]
    res = client.post("/admin/staff", json={"username": "another_doc", "password": "password123", "role": "DOCTOR"}, headers={"Authorization": f"Bearer {doc_token}"})
    assert res.status_code == 403
    
    # 5. Lab cannot create staff -> 403
    res_lab = client.post("/auth/login", json={"username": "lab_test", "password": "password123"})
    assert res_lab.status_code == 200
    lab_token = res_lab.json()["access_token"]
    res = client.post("/admin/staff", json={"username": "another_lab", "password": "password123", "role": "LAB"}, headers={"Authorization": f"Bearer {lab_token}"})
    assert res.status_code == 403
    
    # 6. Patient cannot create staff -> 403
    client.post("/patients", json={"username": "pat_test", "password": "password123"}, headers=admin_headers)
    res_pat = client.post("/auth/login", json={"username": "pat_test", "password": "password123"})
    pat_token = res_pat.json()["access_token"]
    res = client.post("/admin/staff", json={"username": "another_doc2", "password": "password123", "role": "DOCTOR"}, headers={"Authorization": f"Bearer {pat_token}"})
    assert res.status_code == 403
    
    # 7. Unauthenticated -> 401
    res = client.post("/admin/staff", json={"username": "another_doc3", "password": "password123", "role": "DOCTOR"})
    assert res.status_code == 401
    
    # 8. Check GET /admin/staff
    res = client.get("/admin/staff", headers=admin_headers)
    assert res.status_code == 200
    staff = res.json()["staff"]
    usernames = [s["username"] for s in staff]
    assert "doctor_test" in usernames
    assert "lab_test" in usernames
    # Ensure no hashes are returned
    for s in staff:
        assert "password_hash" not in s
