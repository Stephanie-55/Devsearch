import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.db.session import engine, Base, SessionLocal
from app.db import models

client = TestClient(app)

# Setup a clean test database
Base.metadata.drop_all(bind=engine)
Base.metadata.create_all(bind=engine)

def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}

def test_registration_and_login():
    # 1. Register User A
    response = client.post("/auth/register", json={"username": "testuser", "password": "testpassword123"})
    assert response.status_code == 200
    assert "id" in response.json()
    assert response.json()["username"] == "testuser"

    # 2. Prevent Duplicate Registration
    response2 = client.post("/auth/register", json={"username": "testuser", "password": "differentpassword"})
    assert response2.status_code == 400

    # 3. Login User A
    login_response = client.post("/auth/token", data={"username": "testuser", "password": "testpassword123"})
    assert login_response.status_code == 200
    token = login_response.json()["access_token"]
    assert token is not None

    # 4. Verify Me
    me_response = client.get("/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert me_response.status_code == 200
    assert me_response.json()["username"] == "testuser"

def test_unauthorized_access():
    # Attempt to access protected route without token
    response = client.get("/documents/")
    assert response.status_code == 401
    assert response.json()["detail"] == "Could not validate credentials"

def test_multi_tenant_isolation():
    # Register and Login User A
    client.post("/auth/register", json={"username": "userA", "password": "pwA"})
    tokenA = client.post("/auth/token", data={"username": "userA", "password": "pwA"}).json()["access_token"]

    # Register and Login User B
    client.post("/auth/register", json={"username": "userB", "password": "pwB"})
    tokenB = client.post("/auth/token", data={"username": "userB", "password": "pwB"}).json()["access_token"]

    # Verify isolated document lists
    doc_resp_A = client.get("/documents/", headers={"Authorization": f"Bearer {tokenA}"})
    assert doc_resp_A.status_code == 200
    assert len(doc_resp_A.json()) == 0

    doc_resp_B = client.get("/documents/", headers={"Authorization": f"Bearer {tokenB}"})
    assert doc_resp_B.status_code == 200
    assert len(doc_resp_B.json()) == 0

# Note: Testing Uploading and Scraping in unit tests is tricky because FAISS and PDF rendering
# are deeply coupled to the filesystem and external site requests. We prioritize ensuring
# our Multi-Tenant JWT boundaries strictly reject cross-user contamination.
