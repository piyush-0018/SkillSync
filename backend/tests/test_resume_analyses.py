import pymupdf
from fastapi.testclient import TestClient
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.resume_analysis import ResumeAnalysis
from app.schemas.resume_analysis import ResumeAnalysisLLMOutput, ResumeAnalysisNarrative
from app.services import resume_analysis_service


def register_and_upload(client: TestClient) -> None:
    client.post(
        "/api/auth/register",
        json={"full_name": "Aarav Sharma", "email": "aarav@example.com", "password": "SecurePass1"},
    )
    client.patch(
        "/api/users/profile",
        json={"full_name": "Aarav Sharma", "target_role": "Backend Engineer", "experience_level": "fresher"},
    )
    document = pymupdf.open()
    page = document.new_page()
    page.insert_textbox(
        pymupdf.Rect(50, 50, 540, 790),
        """Aarav Sharma
aarav@example.com | +91 98765 43210 | github.com/aarav

EDUCATION
B.Tech Computer Science, Example Institute, 2026

TECHNICAL SKILLS
Python, FastAPI, PostgreSQL, React

PROJECTS
Built SkillSync with FastAPI and PostgreSQL for 200 students
Reduced resume review time by 35%

EXPERIENCE
Developed Python APIs during a software engineering internship
Improved endpoint response time by 20%

CERTIFICATIONS
Cloud Fundamentals
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


def feedback() -> ResumeAnalysisNarrative:
    return ResumeAnalysisNarrative(
        profile_summary="A fresher with relevant backend projects and a clear technical foundation.",
        technical_skills_evaluation="The listed stack is relevant, but evidence should be tied to specific outcomes.",
        projects_evaluation="The projects show applied development work and include useful measurable context.",
        experience_evaluation="The internship supports the target role, though responsibilities need more detail.",
        education_evaluation="The degree and graduation year are clearly presented for an early-career profile.",
        strengths=["Relevant backend stack", "Quantified project and internship outcomes"],
        weaknesses=["Limited detail about individual technical decisions"],
        missing_information=["Deployment links for the main project"],
        improvement_recommendations=["Add two bullets explaining architecture choices and personal contribution."],
        suggested_skills=["Testing with pytest", "Docker"],
        ats_observations=["Use standard section headings and keep technologies in context."],
    )


def test_analysis_is_scored_stored_and_reused(client: TestClient, database_engine, monkeypatch):
    register_and_upload(client)
    calls = 0

    def fake_generate(resume, user, scores):
        nonlocal calls
        calls += 1
        assert len(scores) == 5
        return resume_analysis_service.GeneratedFeedback(feedback(), f"response-{calls}")

    monkeypatch.setattr(resume_analysis_service, "generate_resume_feedback", fake_generate)

    created = client.post("/api/resume-analyses")
    assert created.status_code == 201
    payload = created.json()
    assert payload["overall_score"] == sum(item["score"] for item in payload["category_scores"])
    assert [item["key"] for item in payload["category_scores"]] == [
        "skills_relevance",
        "project_quality",
        "experience_relevance",
        "resume_completeness",
        "clarity_structure",
    ]
    assert payload["is_cached"] is False
    assert "proprietary ATS" in payload["disclaimer"]
    assert payload["analysis"]["strengths"]

    reused = client.post("/api/resume-analyses")
    assert reused.status_code == 201
    assert reused.json()["id"] == payload["id"]
    assert reused.json()["is_cached"] is True
    assert calls == 1

    refreshed = client.post("/api/resume-analyses?refresh=true")
    assert refreshed.status_code == 201
    assert refreshed.json()["id"] != payload["id"]
    assert calls == 2

    history = client.get("/api/resume-analyses").json()["items"]
    assert len(history) == 2
    assert client.get("/api/resume-analyses/latest").json()["id"] == refreshed.json()["id"]

    assert client.delete("/api/resumes/current").status_code == 204

    with Session(database_engine) as database:
        assert database.scalar(select(func.count()).select_from(ResumeAnalysis)) == 0


def test_changed_target_role_invalidates_saved_analysis(client, monkeypatch):
    register_and_upload(client)
    monkeypatch.setattr(resume_analysis_service, 'generate_resume_feedback',
                        lambda *args: resume_analysis_service.GeneratedFeedback(feedback(), None))
    original = client.post('/api/resume-analyses').json()
    client.patch('/api/users/profile', json={
        'full_name': 'Aarav Sharma', 'target_role': 'Frontend Engineer', 'experience_level': 'fresher',
    })
    assert client.get('/api/resume-analyses/latest').status_code == 404
    changed = client.post('/api/resume-analyses').json()
    assert changed['id'] != original['id']
    assert changed['is_cached'] is False
    assert len(client.get('/api/resume-analyses').json()['items']) == 2


def test_analysis_requires_a_readable_resume_and_authentication(client: TestClient):
    assert client.post("/api/resume-analyses").status_code == 401
    client.post(
        "/api/auth/register",
        json={"full_name": "Aarav Sharma", "email": "aarav@example.com", "password": "SecurePass1"},
    )
    response = client.post("/api/resume-analyses")
    assert response.status_code == 409
    assert "Upload a resume" in response.json()["detail"]


def test_malformed_model_output_returns_retryable_error(client: TestClient, database_engine, monkeypatch):
    register_and_upload(client)

    class FakeAIClient:
        def chat_structured(self, **kwargs):
            return kwargs["response_model"].model_validate({"profile_summary": "Incomplete"})

    monkeypatch.setattr(resume_analysis_service, "_client", lambda: FakeAIClient())

    response = client.post("/api/resume-analyses")
    assert response.status_code == 502
    assert response.json()["detail"] == "The AI analysis could not be completed. Please retry in a moment."
    with Session(database_engine) as database:
        assert database.scalar(select(func.count()).select_from(ResumeAnalysis)) == 0


def test_model_overproduction_is_deduplicated_and_bounded():
    output = feedback().model_dump()
    output["strengths"] = [f"Strength {index}" for index in range(20)] + ["Strength 1"]
    output["improvement_recommendations"] = [
        f"Recommendation {index}" for index in range(20)
    ]

    normalized = ResumeAnalysisLLMOutput.model_validate(output)

    assert len(normalized.strengths) == 8
    assert len(normalized.improvement_recommendations) == 10
    assert len(normalized.strengths) == len(set(normalized.strengths))
