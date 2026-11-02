"""
Authentication Tests.
"""

import pytest


def test_registration_and_login(client):
    # 1. Register User
    reg_payload = {
        "display_name": "Alice Developer",
        "email": "alice@university.edu",
        "password": "SecurePassword123!",
        "confirm_password": "SecurePassword123!",
    }
    r = client.post("/api/v1/auth/register", json=reg_payload)
    assert r.status_code == 200
    data = r.json()
    assert data["success"] is True
    assert data["data"]["email"] == "alice@university.edu"
    assert data["data"]["display_name"] == "Alice Developer"

    # 2. Reject duplicate registration
    r2 = client.post("/api/v1/auth/register", json=reg_payload)
    assert r2.status_code == 400

    # 3. Reject password mismatch
    mismatch_payload = {
        "display_name": "Bob",
        "email": "bob@university.edu",
        "password": "Password1!",
        "confirm_password": "Password2!",
    }
    r_mismatch = client.post("/api/v1/auth/register", json=mismatch_payload)
    assert r_mismatch.status_code == 422

    # 4. Login with Argon2id verification
    login_payload = {
        "email": "alice@university.edu",
        "password": "SecurePassword123!",
    }
    r_login = client.post("/api/v1/auth/login", json=login_payload)
    assert r_login.status_code == 200
    login_data = r_login.json()
    assert login_data["success"] is True
    assert "access_token" in login_data["data"]
    access_token = login_data["data"]["access_token"]
    refresh_token = login_data["data"]["refresh_token"]

    # 5. Access protected route with Bearer token
    headers = {"Authorization": f"Bearer {access_token}"}
    r_me = client.get("/api/v1/auth/me", headers=headers)
    assert r_me.status_code == 200
    assert r_me.json()["data"]["email"] == "alice@university.edu"

    # 6. Rotate refresh token
    r_refresh = client.post("/api/v1/auth/refresh", json={"refresh_token": refresh_token})
    assert r_refresh.status_code == 200
    new_refresh = r_refresh.json()["data"]["refresh_token"]
    assert new_refresh != refresh_token

    # 7. Old refresh token revoked
    r_old_refresh = client.post("/api/v1/auth/refresh", json={"refresh_token": refresh_token})
    assert r_old_refresh.status_code == 401

    # 8. Logout revokes active session
    r_logout = client.post("/api/v1/auth/logout", json={"refresh_token": new_refresh})
    assert r_logout.status_code == 200
