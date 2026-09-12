from datetime import datetime, timedelta, timezone

import jwt
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.user import User
from app.services import user_service


def registration_payload():
    return {
        "full_name": "Aarav Sharma",
        "email": "aarav@example.com",
        "password": "SecurePass1",
    }


def test_complete_authentication_flow(client: TestClient, database_engine):
    register_response = client.post("/api/auth/register", json=registration_payload())
    assert register_response.status_code == 201
    assert register_response.json()["user"]["email"] == "aarav@example.com"
    assert settings.auth_cookie_name in register_response.cookies
    session_cookie = register_response.headers["set-cookie"].lower()
    assert "httponly" in session_cookie
    assert "samesite=lax" in session_cookie
    assert "path=/api" in session_cookie

    with Session(database_engine) as database:
        saved_user = database.scalar(select(User).where(User.email == "aarav@example.com"))
        assert saved_user is not None
        assert saved_user.password_hash != "SecurePass1"

    profile_response = client.patch(
        "/api/users/profile",
        json={
            "full_name": "Aarav Sharma",
            "target_role": "Backend Developer",
            "experience_level": "student",
        },
    )
    assert profile_response.status_code == 200
    assert profile_response.json()["target_role"] == "Backend Developer"

    current_user_response = client.get("/api/auth/me")
    assert current_user_response.status_code == 200
    assert current_user_response.json()["experience_level"] == "student"

    logout_response = client.post("/api/auth/logout")
    assert logout_response.status_code == 200
    assert client.get("/api/auth/me").status_code == 401

    login_response = client.post(
        "/api/auth/login",
        json={"email": "aarav@example.com", "password": "SecurePass1"},
    )
    assert login_response.status_code == 200
    assert client.get("/api/users/profile").status_code == 200


def test_duplicate_email_is_rejected(client: TestClient):
    assert client.post("/api/auth/register", json=registration_payload()).status_code == 201
    response = client.post("/api/auth/register", json=registration_payload())
    assert response.status_code == 409
    assert response.json()["detail"] == "An account with this email already exists"


def test_incorrect_password_is_rejected(client: TestClient):
    client.post("/api/auth/register", json=registration_payload())
    client.post("/api/auth/logout")
    response = client.post(
        "/api/auth/login",
        json={"email": "aarav@example.com", "password": "WrongPassword1"},
    )
    assert response.status_code == 401
    assert response.json()["detail"] == "Email or password is incorrect"


def test_unknown_email_still_performs_password_verification(client: TestClient, monkeypatch):
    checked_hashes = []

    def record_verification(password, password_hash):
        checked_hashes.append(password_hash)
        return False

    monkeypatch.setattr(user_service, "verify_password", record_verification)
    response = client.post(
        "/api/auth/login",
        json={"email": "missing@example.com", "password": "WrongPassword1"},
    )

    assert response.status_code == 401
    assert checked_hashes == [user_service.DUMMY_PASSWORD_HASH]


def test_password_requirements_are_enforced(client: TestClient):
    payload = registration_payload() | {"password": "weakpass"}
    response = client.post("/api/auth/register", json=payload)
    assert response.status_code == 422


def test_invalid_and_expired_tokens_are_rejected(client: TestClient):
    invalid_response = client.get("/api/auth/me", headers={"Authorization": "Bearer not-a-token"})
    assert invalid_response.status_code == 401
    assert invalid_response.json()["detail"] == "Invalid authentication token"

    expired_token = jwt.encode(
        {
            "sub": "1",
            "type": "access",
            "iat": datetime.now(timezone.utc) - timedelta(minutes=2),
            "exp": datetime.now(timezone.utc) - timedelta(minutes=1),
        },
        settings.jwt_secret,
        algorithm=settings.jwt_algorithm,
    )
    expired_response = client.get("/api/auth/me", headers={"Authorization": f"Bearer {expired_token}"})
    assert expired_response.status_code == 401
    assert expired_response.json()["detail"] == "Session expired. Please sign in again"

    missing_claims = jwt.encode(
        {"sub": "1", "exp": datetime.now(timezone.utc) + timedelta(minutes=5)},
        settings.jwt_secret,
        algorithm=settings.jwt_algorithm,
    )
    response = client.get("/api/auth/me", headers={"Authorization": f"Bearer {missing_claims}"})
    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid authentication token"


def test_api_responses_disable_caching_and_sniffing(client: TestClient):
    response = client.get("/api/health")

    assert response.headers["cache-control"] == "no-store"
    assert response.headers["x-content-type-options"] == "nosniff"
    assert response.headers["x-frame-options"] == "DENY"


@pytest.mark.parametrize('name', ['   ', ' A ', 123, None])
def test_registration_rejects_invalid_normalized_names(client, name):
    response = client.post('/api/auth/register', json=registration_payload() | {'full_name': name})
    assert response.status_code == 422


def test_profile_rejects_blank_name_and_preserves_existing_profile(client):
    client.post('/api/auth/register', json=registration_payload())
    assert client.patch('/api/users/profile', json={'full_name': '  '}).status_code == 422
    assert client.get('/api/auth/me').json()['full_name'] == 'Aarav Sharma'


@pytest.mark.parametrize('subject', ['0', '-1', '999999999999999999999999', '2147483648', '1 OR 1=1'])
def test_invalid_token_subject_never_reaches_database(client, subject):
    now = datetime.now(timezone.utc)
    token = jwt.encode({'sub': subject, 'type': 'access', 'iat': now, 'exp': now + timedelta(minutes=5)},
                       settings.jwt_secret, algorithm=settings.jwt_algorithm)
    assert client.get('/api/auth/me', headers={'Authorization': f'Bearer {token}'}).status_code == 401


@pytest.mark.parametrize('method,path,payload', [
    ('get', '/api/analytics/dashboard', None),
    ('get', '/api/job-matches', None),
    ('post', '/api/job-matches', {'job_description': 'A complete job description. ' * 20}),
    ('post', '/api/resume-analyses', None),
    ('get', '/api/career-assistant/conversations', None),
    ('post', '/api/career-assistant/messages', {'content': 'What should I learn?'}),
    ('get', '/api/interviews', None),
    ('post', '/api/interviews/1/answers', {'answer': 'My answer to the question.'}),
    ('post', '/api/interviews/1/finish', None),
])
def test_protected_endpoints_reject_anonymous_requests(client, method, path, payload):
    assert client.request(method, path, json=payload).status_code == 401
