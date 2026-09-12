import os
from uuid import uuid4

import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session

from app.db.base import Base
from app.models.career_chunk import CareerChunk
from app.models.career_document import CareerDocument
from app.models.user import User
from app.services import career_context_service as context


@pytest.fixture
def pg_connection():
    url = os.environ.get("TEST_POSTGRES_URL")
    if not url:
        pytest.skip("Set TEST_POSTGRES_URL to a disposable PostgreSQL database with pgvector")
    engine = create_engine(url)
    with engine.connect() as connection:
        transaction = connection.begin()
        schema = "skillsync_test_" + uuid4().hex
        try:
            connection.execute(text(f'CREATE SCHEMA "{schema}"'))
            connection.execute(text(f'SET LOCAL search_path TO "{schema}", public'))
            connection = connection.execution_options(schema_translate_map={None: schema})
            Base.metadata.create_all(connection)
            yield connection
        finally:
            # DDL and test data live inside this transaction; no application tables are dropped.
            transaction.rollback()
    engine.dispose()


def test_pgvector_matches_python_ranking_and_isolates_users(pg_connection, monkeypatch):
    monkeypatch.setattr(context, "_embedding_batches", lambda *args: [[1.0, 0.0]])
    with Session(pg_connection) as database:
        owner = User(full_name="Demo Owner", email="owner@example.test", password_hash="test")
        other = User(full_name="Other Owner", email="other@example.test", password_hash="test")
        database.add_all([owner, other])
        database.flush()
        for index, (user_id, chunk_user_id, vector) in enumerate([
            (owner.id, owner.id, [0.6, 0.8]), (owner.id, owner.id, [1.0, 0.0]),
            (other.id, other.id, [1.0, 0.0]), (other.id, owner.id, [1.0, 0.0]),
            (owner.id, other.id, [1.0, 0.0]), (owner.id, owner.id, [1.0, 0.0, 0.0]),
        ]):
            document = CareerDocument(user_id=user_id, source_key=str(index), source_type="profile",
                                      title=str(index), content="evidence", content_fingerprint="a" * 64,
                                      source_attributes={})
            document.chunks.append(CareerChunk(user_id=chunk_user_id, chunk_index=0, content="evidence",
                                               embedding=vector, embedding_model=context.settings.gemini_embedding_model))
            database.add(document)
        database.flush()
        monkeypatch.setattr(context.settings, "rag_vector_backend", "python")
        expected = context.retrieve_context(database, owner.id, "query", object())
        monkeypatch.setattr(context.settings, "rag_vector_backend", "pgvector")
        actual = context.retrieve_context(database, owner.id, "query", object())
        assert [item.label for item in actual] == [item.label for item in expected] == ["1", "0"]
        assert [item.similarity for item in actual] == pytest.approx([item.similarity for item in expected])
