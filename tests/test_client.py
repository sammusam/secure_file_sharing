from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_client_signup_login_download_flow():
    # 1. Signup
    signup_resp = client.post("/client/signup", json={
        "email": "client1@example.com",
        "password": "securepass",
        "role": "client_user"
    })
    assert signup_resp.status_code == 200
    assert "link" in signup_resp.json()

    # 2. Email Verification
    verify_link = signup_resp.json()["link"]
    verify_resp = client.get(verify_link)
    assert verify_resp.status_code == 200

    # 3. Login
    login_resp = client.post("/client/login", json={
        "email": "client1@example.com",
        "password": "securepass"
    })
    assert login_resp.status_code == 200
    assert "access_token" in login_resp.json()

    # 4. List files (unauthorized initially)
    token = login_resp.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    files_resp = client.get("/client/list-files", headers=headers)
    assert files_resp.status_code in [200, 404]  # 404 if no files yet
