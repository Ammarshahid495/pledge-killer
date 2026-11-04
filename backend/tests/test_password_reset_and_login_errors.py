"""
Tests for specific login error messages and the password reset flow.
"""

from datetime import datetime, timedelta, timezone
from urllib.parse import parse_qs, urlparse

from app.models.user import PasswordResetToken

EMAIL = "alice@university.edu"
OLD_PASSWORD = "OldPassword123!"
NEW_PASSWORD = "BrandNewPass456!"


def register(client, email: str = EMAIL, password: str = OLD_PASSWORD):
    return client.post("/api/v1/auth/register", json={
        "display_name": "Alice",
        "email": email,
        "password": password,
        "confirm_password": password,
    })


def login(client, email: str = EMAIL, password: str = OLD_PASSWORD):
    return client.post("/api/v1/auth/login", json={"email": email, "password": password})


def capture_reset_emails(monkeypatch):
    """Replaces the email sender so tests can read the reset link."""
    sent = []

    def fake_send(to_email, display_name, reset_link):
        sent.append({"to": to_email, "name": display_name, "link": reset_link})

    monkeypatch.setattr("app.api.v1.auth.send_password_reset_email", fake_send)
    return sent


def token_from_link(link: str) -> str:
    return parse_qs(urlparse(link).query)["token"][0]


# ---------- login errors ----------

def test_login_with_unknown_email_says_account_does_not_exist(client):
    r = login(client, email="nobody@university.edu")
    assert r.status_code == 404
    detail = r.json()["detail"]
    assert detail["code"] == "ACCOUNT_NOT_FOUND"
    assert "no account" in detail["message"].lower()


def test_login_with_wrong_password_says_password_is_incorrect(client):
    register(client)
    r = login(client, password="WrongPassword999!")
    assert r.status_code == 401
    detail = r.json()["detail"]
    assert detail["code"] == "INCORRECT_PASSWORD"
    assert "incorrect password" in detail["message"].lower()


def test_login_with_correct_credentials_still_works(client):
    register(client)
    assert login(client).status_code == 200


# ---------- forgot password ----------

def test_forgot_password_for_unknown_email_says_account_does_not_exist(client, monkeypatch):
    sent = capture_reset_emails(monkeypatch)
    r = client.post("/api/v1/auth/forgot-password", json={"email": "nobody@university.edu"})
    assert r.status_code == 404
    assert r.json()["detail"]["code"] == "ACCOUNT_NOT_FOUND"
    assert sent == []


def test_forgot_password_sends_a_link_to_the_account_email(client, monkeypatch):
    register(client)
    sent = capture_reset_emails(monkeypatch)
    r = client.post("/api/v1/auth/forgot-password", json={"email": EMAIL})
    assert r.status_code == 200
    assert r.json()["success"] is True
    assert len(sent) == 1
    assert sent[0]["to"] == EMAIL
    assert "/reset-password?token=" in sent[0]["link"]


def test_forgot_password_cannot_be_spammed(client, monkeypatch):
    register(client)
    sent = capture_reset_emails(monkeypatch)
    assert client.post("/api/v1/auth/forgot-password", json={"email": EMAIL}).status_code == 200
    r = client.post("/api/v1/auth/forgot-password", json={"email": EMAIL})
    assert r.status_code == 429
    assert r.json()["detail"]["code"] == "RESET_TOO_SOON"
    assert len(sent) == 1


# ---------- reset password ----------

def test_full_reset_flow_changes_the_password(client, monkeypatch):
    register(client)
    refresh_token = login(client).json()["data"]["refresh_token"]
    sent = capture_reset_emails(monkeypatch)
    client.post("/api/v1/auth/forgot-password", json={"email": EMAIL})
    token = token_from_link(sent[0]["link"])

    r = client.post("/api/v1/auth/reset-password", json={
        "token": token, "password": NEW_PASSWORD, "confirm_password": NEW_PASSWORD,
    })
    assert r.status_code == 200
    assert r.json()["success"] is True

    # Old password no longer works, new one does.
    assert login(client, password=OLD_PASSWORD).json()["detail"]["code"] == "INCORRECT_PASSWORD"
    assert login(client, password=NEW_PASSWORD).status_code == 200

    # Sessions that existed before the reset were signed out.
    r_refresh = client.post("/api/v1/auth/refresh", json={"refresh_token": refresh_token})
    assert r_refresh.status_code == 401


def test_reset_link_can_only_be_used_once(client, monkeypatch):
    register(client)
    sent = capture_reset_emails(monkeypatch)
    client.post("/api/v1/auth/forgot-password", json={"email": EMAIL})
    token = token_from_link(sent[0]["link"])
    body = {"token": token, "password": NEW_PASSWORD, "confirm_password": NEW_PASSWORD}

    assert client.post("/api/v1/auth/reset-password", json=body).status_code == 200
    again = client.post("/api/v1/auth/reset-password", json=body)
    assert again.status_code == 400
    assert again.json()["detail"]["code"] == "INVALID_RESET_TOKEN"


def test_expired_reset_link_is_rejected(client, db_session, monkeypatch):
    register(client)
    sent = capture_reset_emails(monkeypatch)
    client.post("/api/v1/auth/forgot-password", json={"email": EMAIL})
    token = token_from_link(sent[0]["link"])

    record = db_session.query(PasswordResetToken).first()
    record.expires_at = datetime.now(timezone.utc) - timedelta(minutes=1)
    db_session.commit()

    r = client.post("/api/v1/auth/reset-password", json={
        "token": token, "password": NEW_PASSWORD, "confirm_password": NEW_PASSWORD,
    })
    assert r.status_code == 400
    assert "expired" in r.json()["detail"]["message"].lower()
    assert login(client, password=OLD_PASSWORD).status_code == 200  # password unchanged


def test_made_up_reset_token_is_rejected(client):
    r = client.post("/api/v1/auth/reset-password", json={
        "token": "this-token-does-not-exist-at-all",
        "password": NEW_PASSWORD,
        "confirm_password": NEW_PASSWORD,
    })
    assert r.status_code == 400
    assert r.json()["detail"]["code"] == "INVALID_RESET_TOKEN"


def test_reset_password_validates_the_new_password(client, monkeypatch):
    register(client)
    sent = capture_reset_emails(monkeypatch)
    client.post("/api/v1/auth/forgot-password", json={"email": EMAIL})
    token = token_from_link(sent[0]["link"])

    mismatch = client.post("/api/v1/auth/reset-password", json={
        "token": token, "password": NEW_PASSWORD, "confirm_password": "Different123!",
    })
    assert mismatch.status_code == 422

    too_short = client.post("/api/v1/auth/reset-password", json={
        "token": token, "password": "short", "confirm_password": "short",
    })
    assert too_short.status_code == 422

    # The link is still usable after failed validation attempts.
    ok = client.post("/api/v1/auth/reset-password", json={
        "token": token, "password": NEW_PASSWORD, "confirm_password": NEW_PASSWORD,
    })
    assert ok.status_code == 200


# ---------- email delivery ----------

def test_email_is_sent_over_smtp_when_configured(monkeypatch):
    from app.core.config import settings
    from app.services import email_service

    calls = []

    class FakeSMTP:
        def __init__(self, host, port, timeout=None):
            calls.append(("connect", host, port))

        def starttls(self, context=None):
            calls.append(("starttls",))

        def login(self, user, password):
            calls.append(("login", user, password))

        def send_message(self, msg):
            calls.append(("send", msg["To"], msg["From"], msg["Subject"], msg.get_content()))

        def __enter__(self):
            return self

        def __exit__(self, *exc):
            return False

    monkeypatch.setattr(email_service.smtplib, "SMTP", FakeSMTP)
    monkeypatch.setattr(settings, "SMTP_HOST", "smtp.example.com")
    monkeypatch.setattr(settings, "SMTP_PORT", 587)
    monkeypatch.setattr(settings, "SMTP_USER", "mailer@example.com")
    monkeypatch.setattr(settings, "SMTP_PASSWORD", "app-password")
    monkeypatch.setattr(settings, "SMTP_FROM", None)
    monkeypatch.setattr(settings, "SMTP_USE_TLS", True)
    monkeypatch.setattr(settings, "SMTP_USE_SSL", False)

    link = "https://example.com/reset-password?token=abc"
    email_service.send_password_reset_email("alice@university.edu", "Alice", link)

    kinds = [c[0] for c in calls]
    assert kinds == ["connect", "starttls", "login", "send"]
    send = calls[-1]
    assert send[1] == "alice@university.edu"
    assert send[2] == "mailer@example.com"  # From falls back to the SMTP user
    assert link in send[4]


def test_reset_link_goes_to_the_server_log_when_smtp_is_not_configured(monkeypatch, caplog):
    from app.core.config import settings
    from app.services import email_service

    monkeypatch.setattr(settings, "SMTP_HOST", None)
    link = "https://example.com/reset-password?token=abc"
    with caplog.at_level("WARNING"):
        email_service.send_password_reset_email("alice@university.edu", "Alice", link)
    assert link in caplog.text


def test_a_failing_mail_server_never_breaks_the_request(monkeypatch):
    from app.core.config import settings
    from app.services import email_service

    def boom(*args, **kwargs):
        raise OSError("mail server unreachable")

    monkeypatch.setattr(email_service.smtplib, "SMTP", boom)
    monkeypatch.setattr(settings, "SMTP_HOST", "smtp.example.com")
    # Must swallow the error (it is logged) instead of raising.
    email_service.send_password_reset_email("alice@university.edu", "Alice", "https://x/reset-password?token=abc")
