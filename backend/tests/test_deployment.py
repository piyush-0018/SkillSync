import json
import logging
import os
import subprocess
import sys

import pytest
from fastapi import FastAPI, HTTPException
from fastapi.testclient import TestClient
from pydantic import ValidationError
from sqlalchemy.dialects import postgresql
from sqlalchemy.exc import OperationalError

from app.api.routes.health import readiness_check
from app.core.config import Settings
from app.core.frontend import FrontendFiles
from app.core.logging import RequestLogFormatter
from app.services.career_context_service import _pgvector_query


@pytest.mark.parametrize("prefix", ["postgres://", "postgresql://", "postgresql+psycopg://"])
def test_hosted_database_url_uses_psycopg_and_preserves_escaping(prefix):
    config = Settings(_env_file=None, database_url=prefix + "user:p%40ss@db.example/skillsync?sslmode=require")
    assert config.database_url == "postgresql+psycopg://user:p%40ss@db.example/skillsync?sslmode=require"


def test_pgvector_rejects_non_postgres_database():
    with pytest.raises(ValidationError, match="requires PostgreSQL"):
        Settings(_env_file=None, database_url="sqlite://", rag_vector_backend="pgvector")


def test_provider_secret_is_redacted():
    config = Settings(_env_file=None, gemini_api_key="private-test-provider-key")
    assert "private-test-provider-key" not in repr(config)


def test_spa_fallback_does_not_swallow_api_assets_or_private_files(tmp_path):
    dist = tmp_path / "dist"
    dist.mkdir()
    (dist / "index.html").write_text("<html>SkillSync</html>", encoding="utf-8")
    (dist / "assets").mkdir()
    (dist / "assets" / "app.js").write_text("export {}", encoding="utf-8")
    (tmp_path / "private.txt").write_text("secret", encoding="utf-8")
    app = FastAPI()
    app.mount("/", FrontendFiles(dist))
    with TestClient(app) as client:
        for path in ["/", "/dashboard", "/interviews/1/results"]:
            assert client.get(path).text == "<html>SkillSync</html>"
        for path in ["/api", "/api/missing", "/assets/missing.js", "/assets/missing", "/%2e%2e/private.txt"]:
            assert client.get(path).status_code == 404
        assert client.get("/assets/app.js").status_code == 200
        assert client.post("/dashboard").status_code == 405


def test_request_logs_have_allowlisted_fields_only():
    record = logging.makeLogRecord({"msg": "request_completed", "levelname": "INFO", "route": "/api/auth/login",
                                     "password": "secret-password", "query": "token=secret"})
    output = RequestLogFormatter().format(record)
    assert json.loads(output)["route"] == "/api/auth/login"
    assert "secret" not in output


def test_readiness_and_request_id(client):
    response = client.get("/api/ready")
    assert response.status_code == 200
    assert len(response.headers["X-Request-ID"]) == 32


def test_readiness_error_hides_database_details():
    class UnavailableDatabase:
        def execute(self, statement):
            raise OperationalError("private-host", {}, Exception("private-password"))
    with pytest.raises(HTTPException) as failure:
        readiness_check(UnavailableDatabase())
    assert failure.value.status_code == 503
    assert failure.value.detail == "Service dependencies are not ready"


def test_production_app_serves_spa_but_preserves_api_security(tmp_path):
    (tmp_path / "index.html").write_text("<html>Built frontend</html>", encoding="utf-8")
    env = os.environ | {
        "APP_ENV": "production", "AUTH_COOKIE_SECURE": "true",
        "FRONTEND_ORIGIN": "https://skillsync.example", "FRONTEND_DIST_DIR": str(tmp_path),
    }
    script = """
from fastapi.testclient import TestClient
from app.main import app
with TestClient(app) as client:
    assert client.get('/dashboard').text == '<html>Built frontend</html>'
    assert client.get('/api/health').status_code == 200
    assert client.get('/api/resumes/current').status_code == 401
    assert client.get('/api/unknown').status_code == 404
    assert client.get('/openapi.json').status_code == 404
    assert client.get('/api/docs').status_code == 404
    assert client.get('/api/health').headers['cache-control'] == 'no-store'
"""
    result = subprocess.run([sys.executable, "-c", script], env=env, capture_output=True, text=True, timeout=30)
    assert result.returncode == 0, result.stdout + result.stderr


def test_pgvector_sql_binds_vectors_and_scopes_both_owners():
    query = _pgvector_query(42, [1.0, 0.0]).compile(dialect=postgresql.dialect())
    sql = str(query)
    assert "career_chunks.user_id =" in sql
    assert "career_documents.user_id =" in sql
    assert "<=>" in sql
    assert "[1.0, 0.0]" not in sql
    assert query.params["query_vector"] == "[1.0, 0.0]"
