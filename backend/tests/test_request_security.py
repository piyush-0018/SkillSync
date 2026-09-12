import asyncio

import pytest
from fastapi.testclient import TestClient

from app.core.config import settings
from app.core.request_security import RequestSecurityMiddleware
from app.main import app


@pytest.mark.parametrize('path', ['/api/auth/login', '/api/auth/logout', '/api/resumes', '/api/job-matches'])
@pytest.mark.parametrize('origin', ['https://attacker.example', 'null', 'http://localhost:5173.attacker.example'])
def test_disallowed_origin_cannot_execute_writes(client, path, origin):
    response = client.post(path, headers={'Origin': origin})
    assert response.status_code == 403
    assert response.headers['cache-control'] == 'no-store'


def test_cookie_write_and_cors_work_for_configured_frontend(client):
    response = client.post('/api/auth/register', headers={'Origin': settings.frontend_origin}, json={
        'full_name': 'Test Student', 'email': 'origin@example.com', 'password': 'StrongPass1',
    })
    assert response.status_code == 201
    assert response.headers['access-control-allow-origin'] == settings.frontend_origin
    response = client.patch('/api/users/profile', headers={'Origin': 'https://attacker.example'}, json={
        'full_name': 'Attacker Name',
    })
    assert response.status_code == 403
    assert client.get('/api/auth/me').json()['full_name'] == 'Test Student'


def test_missing_origin_with_cross_site_fetch_metadata_is_rejected(client):
    assert client.post('/api/auth/logout', headers={'Sec-Fetch-Site': 'cross-site'}).status_code == 403


def test_auth_throttling_is_per_client_and_has_retry_header(client, monkeypatch):
    monkeypatch.setattr(settings, 'auth_requests_per_minute', 2)
    payload = {'email': 'nobody@example.com', 'password': 'WrongPassword1'}
    assert client.post('/api/auth/login', json=payload).status_code == 401
    assert client.post('/api/auth/login', json=payload).status_code == 401
    response = client.post('/api/auth/login', json=payload)
    assert response.status_code == 429
    assert response.headers['retry-after'] == '60'
    assert client.get('/api/health').status_code == 200


def test_oversized_body_is_rejected_before_validation(client):
    response = client.post('/api/auth/login', content=b'x' * (settings.max_api_body_kb * 1024 + 1))
    assert response.status_code == 413


def test_chunked_upload_is_bounded_without_content_length(monkeypatch):
    monkeypatch.setattr(settings, 'max_resume_size_mb', 1)
    reached_application = False
    sent = []
    chunks = iter([
        {'type': 'http.request', 'body': b'x' * (600 * 1024), 'more_body': True},
        {'type': 'http.request', 'body': b'x' * (600 * 1024), 'more_body': False},
    ])

    async def downstream(scope, receive, send):
        nonlocal reached_application
        reached_application = True

    async def receive():
        return next(chunks)

    async def send(message):
        sent.append(message)

    middleware = RequestSecurityMiddleware(downstream, [settings.frontend_origin])
    asyncio.run(middleware({'type': 'http', 'method': 'POST', 'path': '/api/resumes', 'headers': []}, receive, send))
    assert not reached_application
    assert sent[0]['status'] == 413


def test_validation_response_does_not_echo_password(client):
    response = client.post('/api/auth/register', json={
        'full_name': 'Test Student', 'email': 'test@example.com', 'password': 'sensitive-invalid-password',
    })
    assert response.status_code == 422
    assert 'sensitive-invalid-password' not in response.text
    assert all('input' not in error and 'ctx' not in error for error in response.json()['detail'])


def test_unexpected_errors_do_not_expose_internal_details(monkeypatch):
    from app.services import user_service

    def fail(*args):
        raise RuntimeError('postgres://private-credential@internal-db')

    monkeypatch.setattr(user_service, 'get_user_by_email', fail)
    with TestClient(app, raise_server_exceptions=False) as client:
        response = client.post('/api/auth/login', json={'email': 'test@example.com', 'password': 'SecurePass1'})
    assert response.status_code == 500
    assert 'private-credential' not in response.text
