import math

import pytest
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.career_chunk import CareerChunk
from app.models.career_document import CareerDocument
from app.models.user import User
from app.services import career_context_service


def user(email: str, role: str = "Backend Engineer") -> User:
    return User(
        full_name="Test Student",
        email=email,
        password_hash="hashed-password-must-never-be-indexed",
        target_role=role,
        experience_level="fresher",
    )


class EmbeddingClient:
    def __init__(self):
        self.calls = 0

    def embed(self, *, model, inputs):
        self.calls += 1
        return [[1.0] + [0.0] * 767 for _ in inputs]


def test_chunking_is_bounded_and_keeps_useful_overlap():
    text = " ".join(f"word-{index}" for index in range(500))
    chunks = career_context_service.chunk_text(text, chunk_size=300, overlap=50)

    assert len(chunks) > 2
    assert all(chunk.strip() for chunk in chunks)
    assert all(len(chunk) <= 300 for chunk in chunks)
    assert set(chunks[0].split()[-3:]) & set(chunks[1].split()[:10])


def test_sync_reuses_unchanged_vectors_and_updates_changed_profile(database_engine):
    client = EmbeddingClient()
    with Session(database_engine) as database:
        candidate = user("sync@example.com")
        database.add(candidate)
        database.commit()
        database.refresh(candidate)

        career_context_service.sync_user_documents(database, candidate, client)
        assert client.calls == 1
        assert database.scalar(select(func.count()).select_from(CareerDocument)) == 1
        assert database.scalar(select(func.count()).select_from(CareerChunk)) == 1

        career_context_service.sync_user_documents(database, candidate, client)
        assert client.calls == 1

        candidate.target_role = "AI Engineer"
        career_context_service.sync_user_documents(database, candidate, client)
        assert client.calls == 2
        document = database.scalar(select(CareerDocument).where(CareerDocument.user_id == candidate.id))
        assert "AI Engineer" in document.content
        assert "hashed-password" not in document.content


def test_retrieval_filters_by_user_before_similarity(database_engine, monkeypatch):
    with Session(database_engine) as database:
        first = user("first-vectors@example.com")
        second = user("second-vectors@example.com")
        database.add_all([first, second])
        database.flush()

        first_document = CareerDocument(
            user_id=first.id,
            source_type="profile",
            source_record_id=first.id,
            source_key="profile",
            title="First user's private profile",
            content="Private first-user context",
            content_fingerprint="a" * 64,
            source_attributes={},
        )
        second_document = CareerDocument(
            user_id=second.id,
            source_type="profile",
            source_record_id=second.id,
            source_key="profile",
            title="Second user's profile",
            content="Second-user context",
            content_fingerprint="b" * 64,
            source_attributes={},
        )
        database.add_all([first_document, second_document])
        database.flush()
        database.add_all(
            [
                CareerChunk(
                    document_id=first_document.id,
                    user_id=first.id,
                    chunk_index=0,
                    content=first_document.content,
                    embedding=[1.0, 0.0],
                    embedding_model="gemini-embedding-001",
                ),
                CareerChunk(
                    document_id=second_document.id,
                    user_id=second.id,
                    chunk_index=0,
                    content=second_document.content,
                    embedding=[0.6, 0.8],
                    embedding_model="gemini-embedding-001",
                ),
            ]
        )
        database.commit()

        monkeypatch.setattr(career_context_service, "_embedding_batches", lambda *args: [[1.0, 0.0]])
        contexts = career_context_service.retrieve_context(database, second.id, "private query", object())

        assert len(contexts) == 1
        assert contexts[0].label == "Second user's profile"
        assert "first-user" not in contexts[0].content
        assert math.isclose(contexts[0].similarity, 0.6)


def test_invalid_embedding_dimension_stops_indexing(database_engine):
    class InvalidClient:
        def embed(self, *, model, inputs):
            return [[0.1, 0.2] for _ in inputs]

    with Session(database_engine) as database:
        candidate = user("invalid-vector@example.com")
        database.add(candidate)
        database.commit()

        with pytest.raises(career_context_service.ContextIndexError, match="expected 768"):
            career_context_service.sync_user_documents(database, candidate, InvalidClient())

        assert database.scalar(select(func.count()).select_from(CareerDocument)) == 0


def test_chunk_configuration_change_rebuilds_index(database_engine, monkeypatch):
    client = EmbeddingClient()
    with Session(database_engine) as database:
        candidate = user('rechunk@example.com')
        database.add(candidate)
        database.commit()
        career_context_service.sync_user_documents(database, candidate, client)
        monkeypatch.setattr(career_context_service.settings, 'rag_chunk_size', 500)
        career_context_service.sync_user_documents(database, candidate, client)
        assert client.calls == 2


def test_mismatched_chunk_owner_cannot_expose_another_users_document(database_engine, monkeypatch):
    with Session(database_engine) as database:
        owner, other = user('owner@example.com'), user('other@example.com')
        database.add_all([owner, other])
        database.flush()
        document = CareerDocument(user_id=owner.id, source_type='profile', source_key='profile',
                                  title='Private', content='Private text', content_fingerprint='a' * 64,
                                  source_attributes={})
        document.chunks.append(CareerChunk(user_id=other.id, chunk_index=0, content='Private text',
                                          embedding=[1.0, 0.0], embedding_model='gemini-embedding-001'))
        database.add(document)
        database.commit()
        monkeypatch.setattr(career_context_service, '_embedding_batches', lambda *args: [[1.0, 0.0]])
        assert career_context_service.retrieve_context(database, other.id, 'query', object()) == []
        assert career_context_service.retrieve_context(database, owner.id, 'query', object()) == []
