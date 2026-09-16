from fastapi.testclient import TestClient
from main import app
import pytest

client = TestClient(app)

def test_reset_demo_data_security():
    # 1. Unauthenticated -> 401
    res = client.post("/admin/reset-demo-data")
    assert res.status_code == 401

    # 2. PATIENT -> 403
    res_pat = client.post("/auth/login", json={"username": "patient1", "password": "password123"})
    # Only if patient1 exists, if not we skip or assert 401
    if res_pat.status_code == 200:
        pat_token = res_pat.json()["access_token"]
        res = client.post("/admin/reset-demo-data", headers={"Authorization": f"Bearer {pat_token}"})
        assert res.status_code == 403

    # 3. DOCTOR -> 403
    res_doc = client.post("/auth/login", json={"username": "doctor1", "password": "password123"})
    if res_doc.status_code == 200:
        doc_token = res_doc.json()["access_token"]
        res = client.post("/admin/reset-demo-data", headers={"Authorization": f"Bearer {doc_token}"})
        assert res.status_code == 403

    # 4. ADMIN -> 200 (Allowed)
    res_admin = client.post("/auth/login", json={"username": "admin", "password": "password123"})
    if res_admin.status_code == 200:
        admin_token = res_admin.json()["access_token"]
        res = client.post("/admin/reset-demo-data", headers={"Authorization": f"Bearer {admin_token}"})
        assert res.status_code == 200
        assert res.json()["message"] == "Demo data reset successfully"
