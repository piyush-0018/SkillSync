from functools import lru_cache
from pathlib import Path
from typing import Literal
from urllib.parse import urlsplit

from pydantic import Field, SecretStr, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "SkillSync"
    app_env: Literal["development", "test", "production"] = "development"
    api_prefix: str = "/api"
    frontend_dist_dir: Path | None = None
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR"] = "INFO"
    database_url: str
    frontend_origin: str = "http://localhost:5173"
    jwt_secret: str = Field(min_length=32)
    jwt_algorithm: Literal["HS256"] = "HS256"
    access_token_expire_minutes: int = Field(default=60, ge=5, le=1440)
    auth_cookie_name: str = "skillsync_session"
    auth_cookie_secure: bool = False
    auth_requests_per_minute: int = Field(default=20, ge=1, le=300)
    max_api_body_kb: int = Field(default=128, ge=32, le=1024)
    resume_storage_dir: Path = Path("storage/resumes")
    max_resume_size_mb: int = Field(default=5, ge=1, le=25)
    max_resume_pages: int = Field(default=50, ge=1, le=100)
    gemini_api_key: SecretStr = SecretStr("")
    gemini_model: str = "gemini-3.1-flash-lite"
    gemini_embedding_model: str = "gemini-embedding-001"
    ai_timeout_seconds: float = Field(default=120.0, ge=1, le=300)
    ai_max_output_tokens: int = Field(default=1536, ge=128, le=8192)
    resume_analysis_max_characters: int = Field(default=40_000, ge=1_000, le=500_000)
    rag_chunk_size: int = Field(default=900, ge=200, le=4_000)
    rag_chunk_overlap: int = Field(default=120, ge=0, le=1_000)
    rag_top_k: int = Field(default=6, ge=1, le=20)
    rag_max_context_characters: int = Field(default=8_000, ge=500, le=40_000)
    rag_history_limit: int = Field(default=8, ge=0, le=30)
    rag_embedding_dimensions: int = Field(default=768, ge=1, le=8_192)
    rag_min_similarity: float = Field(default=0.2, ge=-1, le=1)
    rag_vector_backend: Literal["python", "pgvector"] = "python"
    interview_question_limit: int = Field(default=5, ge=1, le=10)

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    @field_validator("database_url")
    @classmethod
    def normalize_database_url(cls, value: str) -> str:
        # Managed services supply URLs without the SQLAlchemy psycopg driver name.
        for prefix in ("postgres://", "postgresql://"):
            if value.startswith(prefix):
                return "postgresql+psycopg://" + value[len(prefix):]
        return value

    @field_validator("frontend_origin")
    @classmethod
    def validate_frontend_origin(cls, value: str) -> str:
        origin = value.strip().rstrip("/")
        parsed = urlsplit(origin)
        if (
            parsed.scheme not in {"http", "https"}
            or not parsed.netloc
            or parsed.username
            or parsed.password
            or parsed.path
            or parsed.query
            or parsed.fragment
        ):
            raise ValueError("FRONTEND_ORIGIN must be one HTTP(S) origin without a path")
        return origin

    @model_validator(mode="after")
    def validate_security_settings(self) -> "Settings":
        if self.jwt_secret == "replace-with-a-long-random-secret":
            raise ValueError("JWT_SECRET must be replaced with a generated secret")
        if self.app_env == "production" and not self.auth_cookie_secure:
            raise ValueError("AUTH_COOKIE_SECURE must be true in production")
        if self.app_env == "production" and not self.frontend_origin.startswith("https://"):
            raise ValueError("FRONTEND_ORIGIN must use HTTPS in production")
        if self.rag_chunk_overlap >= self.rag_chunk_size:
            raise ValueError("RAG_CHUNK_OVERLAP must be smaller than RAG_CHUNK_SIZE")
        if self.rag_vector_backend == "pgvector" and not self.database_url.startswith("postgresql+psycopg://"):
            raise ValueError("RAG_VECTOR_BACKEND=pgvector requires PostgreSQL")
        return self


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
