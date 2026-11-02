"""
Tests for Classroom System and Strict Equal Permissions.
"""

def register_and_login(client, email: str, name: str) -> str:
    client.post("/api/v1/auth/register", json={
        "display_name": name,
        "email": email,
        "password": "Password123!",
        "confirm_password": "Password123!",
    })
    r = client.post("/api/v1/auth/login", json={"email": email, "password": "Password123!"})
    return r.json()["data"]["access_token"]


def test_classroom_creation_and_joining(client):
    alice_token = register_and_login(client, "alice@test.com", "Alice")
    bob_token = register_and_login(client, "bob@test.com", "Bob")

    # Alice creates classroom
    create_resp = client.post(
        "/api/v1/classrooms",
        json={"title": "Data Structures Assignment 1", "description": "Binary Search Trees"},
        headers={"Authorization": f"Bearer {alice_token}"},
    )
    assert create_resp.status_code == 200
    c_data = create_resp.json()["data"]
    classroom_id = c_data["id"]
    join_url = c_data["join_url"]
    join_token = join_url.split("/join/")[-1]

    # Equal permissions: Alice is simply Peer A, NOT a teacher or owner
    assert c_data["my_anonymous_label"] == "Peer A"
    assert c_data["participant_count"] == 1

    # Bob joins through the link
    join_resp = client.post(
        f"/api/v1/classrooms/join/{join_token}",
        headers={"Authorization": f"Bearer {bob_token}"},
    )
    assert join_resp.status_code == 200
    bob_c_data = join_resp.json()["data"]
    assert bob_c_data["my_anonymous_label"] == "Peer B"
    assert bob_c_data["participant_count"] == 2

    # Verify members list does not leak private identities (only anonymous labels)
    members_resp = client.get(
        f"/api/v1/classrooms/{classroom_id}/members",
        headers={"Authorization": f"Bearer {alice_token}"},
    )
    assert members_resp.status_code == 200
    members = members_resp.json()["data"]
    assert len(members) == 2
    labels = [m["anonymous_label"] for m in members]
    assert "Peer A" in labels
    assert "Peer B" in labels
    # Verify no email or user_id leaked
    for m in members:
        assert "email" not in m
        assert "user_id" not in m
