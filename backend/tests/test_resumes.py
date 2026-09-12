import pymupdf
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.resume import Resume
from app.models.user import User
from app.models.career_document import CareerDocument
from app.models.career_chunk import CareerChunk
from app.services.career_context_service import sync_user_documents


def register(client: TestClient, email: str = "aarav@example.com"):
    return client.post(
        "/api/auth/register",
        json={"full_name": "Aarav Sharma", "email": email, "password": "SecurePass1"},
    )


def make_resume_pdf(name: str = "Aarav Sharma", include_text: bool = True) -> bytes:
    document = pymupdf.open()
    page = document.new_page()
    if include_text:
        text = f"""{name}
aarav@example.com | +91 98765 43210
linkedin.com/in/aarav-sharma

EDUCATION
B.Tech Computer Science, Example Institute, 2026

TECHNICAL SKILLS
Python, FastAPI, PostgreSQL, React

PROJECTS
SkillSync - Career preparation platform

EXPERIENCE
Software Engineering Intern, Example Labs

CERTIFICATIONS
Cloud Fundamentals

ACHIEVEMENTS
Finalist, University Hackathon
"""
        page.insert_textbox(pymupdf.Rect(50, 50, 540, 790), text, fontsize=10)
    pdf_bytes = document.tobytes()
    document.close()
    return pdf_bytes


def test_upload_parse_replace_and_delete_resume(client: TestClient, database_engine):
    assert register(client).status_code == 201
    first_pdf = make_resume_pdf()

    upload_response = client.post(
        "/api/resumes",
        files={"file": ("Aarav Resume.pdf", first_pdf, "application/pdf")},
    )
    assert upload_response.status_code == 201
    payload = upload_response.json()
    assert payload["parsing_status"] == "parsed"
    assert payload["structured_data"]["name"] == "Aarav Sharma"
    assert "Python" in payload["structured_data"]["technical_skills"]
    assert "stored_filename" not in payload
    assert "parsed_text" not in payload

    with Session(database_engine) as database:
        first_resume = database.scalar(select(Resume))
        first_stored_filename = first_resume.stored_filename
        assert first_resume.id == payload["id"]
        assert first_resume.user_id is not None
        assert (settings.resume_storage_dir / first_stored_filename).exists()

    replacement_response = client.post(
        "/api/resumes",
        files={"file": ("Updated Resume.PDF", make_resume_pdf("Aarav S. Sharma"), "application/pdf")},
    )
    assert replacement_response.status_code == 201
    assert replacement_response.json()["id"] == payload["id"]

    with Session(database_engine) as database:
        resumes = list(database.scalars(select(Resume)))
        assert len(resumes) == 1
        assert resumes[0].stored_filename != first_stored_filename
        assert not (settings.resume_storage_dir / first_stored_filename).exists()

    assert client.get("/api/resumes/current").status_code == 200
    assert client.delete("/api/resumes/current").status_code == 204
    assert client.get("/api/resumes/current").status_code == 404
    assert not any(settings.resume_storage_dir.iterdir())


def test_resume_upload_validation(client: TestClient, monkeypatch):
    register(client)
    valid_pdf = make_resume_pdf()

    wrong_extension = client.post(
        "/api/resumes",
        files={"file": ("resume.txt", valid_pdf, "application/pdf")},
    )
    assert wrong_extension.status_code == 400

    wrong_mime = client.post(
        "/api/resumes",
        files={"file": ("resume.pdf", valid_pdf, "text/plain")},
    )
    assert wrong_mime.status_code == 400

    fake_pdf = client.post(
        "/api/resumes",
        files={"file": ("resume.pdf", b"This is not a PDF", "application/pdf")},
    )
    assert fake_pdf.status_code == 422

    monkeypatch.setattr(settings, "max_resume_size_mb", 1)
    oversized = client.post(
        "/api/resumes",
        files={"file": ("resume.pdf", b"%PDF-" + b"0" * (1024 * 1024), "application/pdf")},
    )
    assert oversized.status_code == 413

    monkeypatch.setattr(settings, "max_resume_pages", 1)
    document = pymupdf.open()
    document.new_page()
    document.new_page()
    too_many_pages = document.tobytes()
    document.close()
    page_limit = client.post(
        "/api/resumes",
        files={"file": ("resume.pdf", too_many_pages, "application/pdf")},
    )
    assert page_limit.status_code == 422
    assert "more than 1 pages" in page_limit.json()["detail"]


def test_textless_pdf_reports_parsing_failure(client: TestClient):
    register(client)
    response = client.post(
        "/api/resumes",
        files={"file": ("scanned-resume.pdf", make_resume_pdf(include_text=False), "application/pdf")},
    )
    assert response.status_code == 201
    assert response.json()["parsing_status"] == "failed"
    assert "text-based PDF" in response.json()["parsing_error"]


def test_resume_is_private_to_its_owner(client: TestClient):
    register(client, "first@example.com")
    assert client.post(
        "/api/resumes",
        files={"file": ("resume.pdf", make_resume_pdf(), "application/pdf")},
    ).status_code == 201
    client.post("/api/auth/logout")

    register(client, "second@example.com")
    assert client.get("/api/resumes/current").status_code == 404


def test_resume_endpoints_require_authentication(client: TestClient):
    assert client.get("/api/resumes/current").status_code == 401
    assert client.delete("/api/resumes/current").status_code == 401


def test_file_cleanup_failure_does_not_undo_committed_delete(client: TestClient, database_engine, monkeypatch):
    register(client)
    assert client.post(
        "/api/resumes",
        files={"file": ("resume.pdf", make_resume_pdf(), "application/pdf")},
    ).status_code == 201

    def fail_to_remove_file(*args, **kwargs):
        raise OSError("locked")

    monkeypatch.setattr("app.services.resume_service.Path.unlink", fail_to_remove_file)
    response = client.delete("/api/resumes/current")

    assert response.status_code == 204
    with Session(database_engine) as database:
        assert database.scalar(select(Resume)) is None


@pytest.mark.parametrize('operation', ['replace', 'delete'])
def test_resume_change_removes_only_owners_derived_context(client, database_engine, operation):
    class Embeddings:
        def embed(self, *, model, inputs):
            return [[1.0] + [0.0] * 767 for _ in inputs]

    owner_ids = []
    for email in ['other@example.com', 'owner@example.com']:
        owner_ids.append(register(client, email).json()['user']['id'])
        assert client.post('/api/resumes', files={'file': ('resume.pdf', make_resume_pdf(), 'application/pdf')}).status_code == 201
        with Session(database_engine) as database:
            sync_user_documents(database, database.get(User, owner_ids[-1]), Embeddings())
    if operation == 'replace':
        assert client.post('/api/resumes', files={'file': ('new.pdf', make_resume_pdf(), 'application/pdf')}).status_code == 201
    else:
        assert client.delete('/api/resumes/current').status_code == 204
    with Session(database_engine) as database:
        assert database.scalar(select(CareerDocument).where(CareerDocument.user_id == owner_ids[-1])) is None
        assert database.scalar(select(CareerChunk).where(CareerChunk.user_id == owner_ids[-1])) is None
        assert database.scalar(select(CareerDocument).where(CareerDocument.user_id == owner_ids[0])) is not None
        assert database.scalar(select(CareerChunk).where(CareerChunk.user_id == owner_ids[0])) is not None


def test_invalid_replacement_preserves_existing_resume(client):
    register(client)
    saved = client.post('/api/resumes', files={'file': ('original.pdf', make_resume_pdf(), 'application/pdf')}).json()
    assert client.post('/api/resumes', files={'file': ('fake.pdf', b'invalid', 'application/pdf')}).status_code == 422
    assert client.get('/api/resumes/current').json()['id'] == saved['id']
    assert client.get('/api/resumes/current').json()['original_filename'] == 'original.pdf'
    assert len(list(settings.resume_storage_dir.iterdir())) == 1


def test_unauthenticated_upload_does_not_write_storage(client):
    assert client.post('/api/resumes', files={'file': ('resume.pdf', make_resume_pdf(), 'application/pdf')}).status_code == 401
    assert not settings.resume_storage_dir.exists()
