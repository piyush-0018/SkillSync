import os

os.environ["APP_ENV"] = "test"
os.environ["DATABASE_URL"] = "sqlite+pysqlite:///:memory:"
os.environ["JWT_SECRET"] = "test-secret-that-is-long-enough-for-local-tests"
os.environ["AUTH_COOKIE_SECURE"] = "false"
os.environ["FRONTEND_ORIGIN"] = "http://localhost:5173"
os.environ["RAG_VECTOR_BACKEND"] = "python"
os.environ["GEMINI_API_KEY"] = "test-gemini-key"
os.environ.pop("FRONTEND_DIST_DIR", None)

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.config import settings
from app.db.session import Base, get_db
from app.main import app

test_engine = create_engine(
    "sqlite+pysqlite:///:memory:",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSession = sessionmaker(bind=test_engine, autoflush=False, expire_on_commit=False)


@event.listens_for(test_engine, "connect")
def enable_foreign_keys(connection, record):
    connection.execute("PRAGMA foreign_keys=ON")


def override_database():
    database = TestingSession()
    try:
        yield database
    finally:
        database.close()


app.dependency_overrides[get_db] = override_database


@pytest.fixture(autouse=True)
def reset_application_state(tmp_path, monkeypatch):
    middleware = app.middleware_stack
    while middleware is not None:
        if hasattr(middleware, "auth_attempts"):
            middleware.auth_attempts.clear()
        middleware = getattr(middleware, "app", None)
    Base.metadata.drop_all(test_engine)
    Base.metadata.create_all(test_engine)
    monkeypatch.setattr(settings, "resume_storage_dir", tmp_path / "resumes")
    yield


@pytest.fixture
def client():
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture
def database_engine():
    return test_engine
