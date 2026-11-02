"""
Tests for Submissions, File Validation, and Threshold Counting.
"""

from io import BytesIO


def register_and_login(client, email: str, name: str) -> str:
    client.post("/api/v1/auth/register", json={
        "display_name": name,
        "email": email,
        "password": "Password123!",
        "confirm_password": "Password123!",
    })
    r = client.post("/api/v1/auth/login", json={"email": email, "password": "Password123!"})
    return r.json()["data"]["access_token"]


def test_file_validation_rules(client):
    token = register_and_login(client, "student1@test.com", "Student 1")
    c_resp = client.post(
        "/api/v1/classrooms",
        json={"title": "Algorithms 101"},
        headers={"Authorization": f"Bearer {token}"},
    )
    classroom_id = c_resp.json()["data"]["id"]

    # 1. Reject non-.cpp extension
    r_py = client.post(
        f"/api/v1/classrooms/{classroom_id}/submissions",
        files={"file": ("solution.py", b"print('hello')", "text/x-python")},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert r_py.status_code == 400

    # 2. Reject empty file
    r_empty = client.post(
        f"/api/v1/classrooms/{classroom_id}/submissions",
        files={"file": ("solution.cpp", b"", "text/plain")},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert r_empty.status_code == 400

    # 3. Reject executable (ELF magic)
    r_elf = client.post(
        f"/api/v1/classrooms/{classroom_id}/submissions",
        files={"file": ("solution.cpp", b"\x7fELFsomebinarydata", "application/octet-stream")},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert r_elf.status_code == 400

    # 4. Reject archive (ZIP magic)
    r_zip = client.post(
        f"/api/v1/classrooms/{classroom_id}/submissions",
        files={"file": ("solution.cpp", b"PK\x03\x04archivecontents", "application/zip")},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert r_zip.status_code == 400

    # 5. Accept valid C++ file
    valid_cpp = b"#include <iostream>\nint main() { return 0; }\n"
    r_valid = client.post(
        f"/api/v1/classrooms/{classroom_id}/submissions",
        files={"file": ("solution.cpp", valid_cpp, "text/plain")},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert r_valid.status_code == 200
    data = r_valid.json()["data"]
    assert data["current_version"]["version_number"] == 1
    assert data["current_version"]["original_filename"] == "solution.cpp"

    # 6. Resubmit replacement: increment version number, participant submission count remains 1
    valid_cpp_v2 = b"#include <iostream>\nint main() { std::cout << 42; return 0; }\n"
    r_v2 = client.post(
        f"/api/v1/classrooms/{classroom_id}/submissions/me/resubmit",
        files={"file": ("solution.cpp", valid_cpp_v2, "text/plain")},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert r_v2.status_code == 200
    assert r_v2.json()["data"]["current_version"]["version_number"] == 2

    # Check status: valid_submission_count is still 1 (counted by participant, not files)
    status_resp = client.get(
        f"/api/v1/classrooms/{classroom_id}/status",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert status_resp.json()["data"]["valid_submission_count"] == 1


def test_custom_min_submission_threshold(client):
    # Test that creator can configure threshold (e.g. min 2 submissions)
    token1 = register_and_login(client, "alice_custom@test.com", "Alice Custom")
    token2 = register_and_login(client, "bob_custom@test.com", "Bob Custom")

    c_resp = client.post(
        "/api/v1/classrooms",
        json={"title": "Small Study Group (2 students)", "min_submissions": 2},
        headers={"Authorization": f"Bearer {token1}"},
    )
    assert c_resp.status_code == 200
    c_data = c_resp.json()["data"]
    classroom_id = c_data["id"]
    join_token = c_data["join_url"].split("/join/")[-1]
    assert c_data["min_submissions"] == 2

    # Bob joins
    client.post(f"/api/v1/classrooms/join/{join_token}", headers={"Authorization": f"Bearer {token2}"})

    # Student 1 uploads
    r1 = client.post(
        f"/api/v1/classrooms/{classroom_id}/submissions",
        files={"file": ("sol1.cpp", b"int main() { return 0; }", "text/plain")},
        headers={"Authorization": f"Bearer {token1}"},
    )
    assert r1.status_code == 200

    # Status before second submission: 1/2, threshold not met
    s1 = client.get(f"/api/v1/classrooms/{classroom_id}/status", headers={"Authorization": f"Bearer {token1}"})
    assert s1.json()["data"]["threshold"] == 2
    assert s1.json()["data"]["valid_submission_count"] == 1
    assert s1.json()["data"]["threshold_met"] is False

    # Student 2 uploads -> reaches 2/2 threshold!
    r2 = client.post(
        f"/api/v1/classrooms/{classroom_id}/submissions",
        files={"file": ("sol2.cpp", b"int main() { return 1; }", "text/plain")},
        headers={"Authorization": f"Bearer {token2}"},
    )
    assert r2.status_code == 200

    # Status now shows threshold met!
    s2 = client.get(f"/api/v1/classrooms/{classroom_id}/status", headers={"Authorization": f"Bearer {token1}"})
    assert s2.json()["data"]["valid_submission_count"] == 2
    assert s2.json()["data"]["threshold_met"] is True
