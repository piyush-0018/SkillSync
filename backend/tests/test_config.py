import pytest
from pydantic import ValidationError

from app.core.config import Settings, settings
from app.main import cors_origins


def test_production_requires_secure_cookies_and_uses_only_configured_origin(monkeypatch):
    with pytest.raises(ValidationError, match="AUTH_COOKIE_SECURE"):
        Settings(
            _env_file=None,
            app_env="production",
            database_url="postgresql+psycopg://localhost/skillsync",
            frontend_origin="https://skillsync.example",
            jwt_secret="a" * 64,
            auth_cookie_secure=False,
        )

    monkeypatch.setattr(settings, "app_env", "production")
    monkeypatch.setattr(settings, "frontend_origin", "https://skillsync.example")
    assert cors_origins() == ["https://skillsync.example"]


def test_cors_rejects_an_unconfigured_origin(client):
    response = client.options(
        "/api/auth/login",
        headers={
            "Origin": "https://attacker.example",
            "Access-Control-Request-Method": "POST",
        },
    )

    assert response.status_code == 400
    assert "access-control-allow-origin" not in response.headers


@pytest.mark.parametrize(
    ("overrides", "message"),
    [
        ({"jwt_secret": "replace-with-a-long-random-secret"}, "JWT_SECRET"),
        ({"frontend_origin": "https://skillsync.example/app"}, "FRONTEND_ORIGIN"),
        ({"rag_chunk_size": 500, "rag_chunk_overlap": 500}, "RAG_CHUNK_OVERLAP"),
        ({"app_env": "production", "auth_cookie_secure": True, "frontend_origin": "http://skillsync.example"}, "HTTPS"),
    ],
)
def test_invalid_security_configuration_fails_fast(overrides, message):
    values = {
        "database_url": "postgresql+psycopg://localhost/skillsync",
        "frontend_origin": "http://localhost:5173",
        "jwt_secret": "b" * 64,
    }
    with pytest.raises(ValidationError, match=message):
        Settings(_env_file=None, **(values | overrides))


def test_gemini_models_have_deployment_safe_defaults():
    config = Settings(
        _env_file=None,
        database_url="postgresql+psycopg://localhost/skillsync",
        jwt_secret="b" * 64,
    )
    assert config.gemini_model == "gemini-3.1-flash-lite"
    assert config.gemini_embedding_model == "gemini-embedding-001"
    assert config.rag_embedding_dimensions == 768
