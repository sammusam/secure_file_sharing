from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_ops_signup_and_login():
    # 1. Signup
    signup_response = client.post("/ops/signup", json={
        "email": "ops1@example.com",
        "password": "securepass",
        "role": "ops_user"
    })
    assert signup_response.status_code == 200

    # 2. Login
    login_response = client.post("/ops/login", json={
        "email": "ops1@example.com",
        "password": "securepass"
    })
    assert login_response.status_code == 200
    assert "access_token" in login_response.json()

    # 3. Upload file (optional test)
    # You can test upload here by creating a mock `.xlsx` or `.docx` file
    # with open("sample.xlsx", "rb") as f:
    #     files = {"file": ("sample.xlsx", f, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")}
    #     headers = {"Authorization": f"Bearer {login_response.json()['access_token']}"}
    #     upload_resp = client.post("/ops/upload", files=files, headers=headers)
    #     assert upload_resp.status_code == 200
