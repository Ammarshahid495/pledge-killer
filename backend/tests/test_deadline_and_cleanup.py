"""
Tests for the required classroom deadline and automatic deletion once it passes.
"""

from datetime import datetime, timedelta, timezone

from app.models.analysis import AnalysisJob
from app.models.classroom import Classroom, ClassroomMember
from app.models.submission import Submission, SubmissionVersion
from app.services.classroom_service import ClassroomService
from app.storage.local_storage import get_storage_driver


def iso_in(**delta) -> str:
    return (datetime.now(timezone.utc) + timedelta(**delta)).isoformat()


def register_and_login(client, email: str, name: str) -> str:
    client.post("/api/v1/auth/register", json={
        "display_name": name,
        "email": email,
        "password": "Password123!",
        "confirm_password": "Password123!",
    })
    r = client.post("/api/v1/auth/login", json={"email": email, "password": "Password123!"})
    return r.json()["data"]["access_token"]


def create_classroom(client, token: str, deadline: str, title: str = "Deadline Test Class"):
    return client.post(
        "/api/v1/classrooms",
        json={"title": title, "deadline": deadline},
        headers={"Authorization": f"Bearer {token}"},
    )


def test_deadline_is_required(client):
    token = register_and_login(client, "a@test.com", "Alice")
    r = client.post(
        "/api/v1/classrooms",
        json={"title": "No deadline here"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert r.status_code == 422
    assert any("deadline" in err["loc"] for err in r.json()["detail"])


def test_deadline_must_be_in_the_future(client):
    token = register_and_login(client, "a@test.com", "Alice")
    r = create_classroom(client, token, iso_in(hours=-1))
    assert r.status_code == 422
    assert "future" in r.json()["detail"][0]["msg"].lower()


def test_future_deadline_is_accepted_and_returned_in_utc(client):
    token = register_and_login(client, "a@test.com", "Alice")
    r = create_classroom(client, token, iso_in(days=2))
    assert r.status_code == 200
    assert r.json()["data"]["deadline"] is not None


def test_expired_classroom_is_deleted_with_all_its_data(client, db_session):
    token = register_and_login(client, "a@test.com", "Alice")
    classroom_id = create_classroom(client, token, iso_in(days=1)).json()["data"]["id"]

    up = client.post(
        f"/api/v1/classrooms/{classroom_id}/submissions",
        files={"file": ("solution.cpp", b"#include <iostream>\nint main() { return 0; }\n", "text/plain")},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert up.status_code == 200

    version = db_session.query(SubmissionVersion).first()
    storage = get_storage_driver()
    storage_key = version.storage_key
    assert storage.get_file_content(storage_key) is not None

    # Not expired yet: nothing is deleted.
    assert ClassroomService.purge_expired_classrooms(db_session) == 0
    assert db_session.query(Classroom).count() == 1

    # The deadline passes.
    classroom = db_session.query(Classroom).filter(Classroom.id == classroom_id).first()
    classroom.deadline = datetime.now(timezone.utc) - timedelta(seconds=1)
    db_session.commit()

    assert ClassroomService.purge_expired_classrooms(db_session) == 1

    assert db_session.query(Classroom).count() == 0
    assert db_session.query(ClassroomMember).count() == 0
    assert db_session.query(Submission).count() == 0
    assert db_session.query(SubmissionVersion).count() == 0
    assert db_session.query(AnalysisJob).count() == 0
    assert storage.get_file_content(storage_key) is None  # uploaded file removed from disk

    # The deleted classroom disappears from the user's list and cannot be opened.
    listing = client.get("/api/v1/classrooms", headers={"Authorization": f"Bearer {token}"})
    assert listing.json()["data"] == []
    detail = client.get(f"/api/v1/classrooms/{classroom_id}", headers={"Authorization": f"Bearer {token}"})
    assert detail.status_code == 403


def test_only_expired_classrooms_are_deleted(client, db_session):
    token = register_and_login(client, "a@test.com", "Alice")
    keep_id = create_classroom(client, token, iso_in(days=3), "Keep me").json()["data"]["id"]
    drop_id = create_classroom(client, token, iso_in(days=3), "Drop me").json()["data"]["id"]

    drop = db_session.query(Classroom).filter(Classroom.id == drop_id).first()
    drop.deadline = datetime.now(timezone.utc) - timedelta(minutes=5)
    db_session.commit()

    assert ClassroomService.purge_expired_classrooms(db_session) == 1
    remaining = [c.id for c in db_session.query(Classroom).all()]
    assert remaining == [keep_id]


def test_classroom_without_deadline_is_never_deleted(client, db_session):
    """Classrooms created before deadlines became required have no deadline and are left alone."""
    token = register_and_login(client, "a@test.com", "Alice")
    classroom_id = create_classroom(client, token, iso_in(days=3)).json()["data"]["id"]

    classroom = db_session.query(Classroom).filter(Classroom.id == classroom_id).first()
    classroom.deadline = None
    db_session.commit()

    assert ClassroomService.purge_expired_classrooms(db_session) == 0
    assert db_session.query(Classroom).count() == 1
