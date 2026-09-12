import pymupdf
from fastapi.testclient import TestClient
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.job_match import JobMatch
from app.schemas.job_match import JobMatchNarrative, JobRequirements
from app.services import job_match_service


JOB_DESCRIPTION = """Backend Engineer
We are looking for a backend engineer to build reliable APIs for our career platform.

Required skills:
- Strong Python and FastAPI development experience
- PostgreSQL and REST API design
- Docker for local and production workflows

Preferred skills:
- ReactJS familiarity
- Kubernetes experience

Candidates should have at least 1 year of software development experience and a bachelor's degree in computer science or a related field. Responsibilities include designing services, reviewing code, improving API performance, writing tests, and collaborating with frontend engineers.
"""


def register_and_upload(client: TestClient, email: str = "aarav@example.com") -> None:
    client.post(
        "/api/auth/register",
        json={"full_name": "Aarav Sharma", "email": email, "password": "SecurePass1"},
    )
    client.patch(
        "/api/users/profile",
        json={"full_name": "Aarav Sharma", "target_role": "Backend Engineer", "experience_level": "1-3 years"},
    )
    document = pymupdf.open()
    page = document.new_page()
    page.insert_textbox(
        pymupdf.Rect(50, 50, 540, 790),
        """Aarav Sharma
aarav@example.com | +91 98765 43210

EDUCATION
B.Tech Computer Science, Example Institute, 2026

TECHNICAL SKILLS
Python, FastAPI, PostgreSQL, REST, React

PROJECTS
Built SkillSync APIs using Python, FastAPI, PostgreSQL, and React for 200 students

EXPERIENCE
Developed REST APIs during a 1 year software engineering internship
Improved endpoint response time by 20%
""",
        fontsize=10,
    )
    pdf_bytes = document.tobytes()
    document.close()
    response = client.post(
        "/api/resumes",
        files={"file": ("resume.pdf", pdf_bytes, "application/pdf")},
    )
    assert response.status_code == 201


def interpreted_job():
    requirements = JobRequirements(
        job_title="Backend Engineer",
        required_skills=["Python", "FastAPI", "PostgreSQL", "REST API", "Docker"],
        preferred_skills=["ReactJS", "Kubernetes"],
        experience_requirement="At least 1 year of software development experience.",
        minimum_years_experience=1,
        education_requirements=["Bachelor's degree in computer science or a related field"],
        responsibilities=["Design services", "Improve API performance", "Write tests", "Review code"],
        tools_technologies=["Python", "FastAPI", "PostgreSQL", "Docker", "Kubernetes"],
    )
    narrative = JobMatchNarrative(
        experience_alignment="The internship provides directly relevant API development experience for this backend role.",
        education_alignment="The B.Tech Computer Science degree aligns with the stated bachelor's-level requirement.",
        project_relevance="SkillSync demonstrates relevant API, database, and frontend integration work for the role.",
        recommendations=[
            "Build and document a Docker workflow for the main backend project.",
            "Add automated API tests and describe their coverage in the resume.",
        ],
    )
    return requirements, narrative, "response-job-1"


def test_job_match_is_hybrid_scored_saved_and_cached(client: TestClient, database_engine, monkeypatch):
    register_and_upload(client)
    calls = 0

    def fake_interpret(client, job_description, resume, user):
        nonlocal calls
        calls += 1
        return interpreted_job()

    monkeypatch.setattr(job_match_service, "_interpret_job", fake_interpret)
    monkeypatch.setattr(job_match_service, "_semantic_similarity", lambda client, requirements, resume: 0.72)

    response = client.post("/api/job-matches", json={"job_description": JOB_DESCRIPTION})
    assert response.status_code == 201
    payload = response.json()
    assert payload["job_title"] == "Backend Engineer"
    assert payload["result"]["overall_score"] == sum(
        category["score"] for category in payload["result"]["category_scores"]
    )
    assert payload["result"]["required_skill_match"] == 80
    assert payload["result"]["preferred_skill_match"] == 50
    assert "Docker" in payload["result"]["missing_required_skills"]
    assert "Kubernetes" in payload["result"]["missing_preferred_skills"]
    assert "ReactJS" in payload["result"]["matched_skills"]
    assert payload["result"]["semantic_similarity"] == 0.72
    assert payload["result"]["experience_alignment"] == next(
        item["explanation"] for item in payload["result"]["category_scores"] if item["key"] == "experience"
    )
    assert any("Docker" in item for item in payload["result"]["recommendations"])
    assert "internship provides" not in payload["result"]["experience_alignment"]
    assert payload["is_cached"] is False

    cached = client.post("/api/job-matches", json={"job_description": JOB_DESCRIPTION})
    assert cached.status_code == 201
    assert cached.json()["id"] == payload["id"]
    assert cached.json()["is_cached"] is True
    assert calls == 1

    history = client.get("/api/job-matches").json()["items"]
    assert len(history) == 1
    assert history[0]["job_description"] == JOB_DESCRIPTION.strip()
    assert client.get(f"/api/job-matches/{payload['id']}").status_code == 200

    with Session(database_engine) as database:
        stored = database.scalar(select(JobMatch))
        assert stored.user_id is not None
        assert stored.parsed_job_requirements["required_skills"]
        assert stored.match_result["missing_required_skills"] == ["Docker"]


def test_job_matching_requires_auth_and_a_readable_resume(client: TestClient):
    assert client.post("/api/job-matches", json={"job_description": JOB_DESCRIPTION}).status_code == 401
    client.post(
        "/api/auth/register",
        json={"full_name": "Aarav Sharma", "email": "aarav@example.com", "password": "SecurePass1"},
    )
    response = client.post("/api/job-matches", json={"job_description": JOB_DESCRIPTION})
    assert response.status_code == 409
    assert "Upload a resume" in response.json()["detail"]
    assert client.post("/api/job-matches", json={"job_description": "Too short"}).status_code == 422


def test_job_match_failure_does_not_store_a_result(client: TestClient, database_engine, monkeypatch):
    register_and_upload(client)
    def fail_interpret(client, job_description, resume, user):
        raise job_match_service.JobMatchGenerationError("The model did not return usable job requirements. Please retry.")

    monkeypatch.setattr(job_match_service, "_interpret_job", fail_interpret)
    response = client.post("/api/job-matches", json={"job_description": JOB_DESCRIPTION})
    assert response.status_code == 502
    assert "Please retry" in response.json()["detail"]
    with Session(database_engine) as database:
        assert database.scalar(select(func.count()).select_from(JobMatch)) == 0


def test_job_match_history_is_private(client: TestClient, monkeypatch):
    register_and_upload(client, "first@example.com")
    monkeypatch.setattr(job_match_service, "_interpret_job", lambda client, job_description, resume, user: interpreted_job())
    monkeypatch.setattr(job_match_service, "_semantic_similarity", lambda client, requirements, resume: 0.65)
    created = client.post("/api/job-matches", json={"job_description": JOB_DESCRIPTION})
    assert created.status_code == 201
    match_id = created.json()["id"]
    client.post("/api/auth/logout")

    client.post(
        "/api/auth/register",
        json={"full_name": "Meera Rao", "email": "second@example.com", "password": "SecurePass1"},
    )
    assert client.get("/api/job-matches").json()["items"] == []
    assert client.get(f"/api/job-matches/{match_id}").status_code == 404
