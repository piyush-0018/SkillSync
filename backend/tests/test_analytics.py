from datetime import datetime, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.interview_question import InterviewQuestion
from app.models.interview_session import InterviewSession
from app.models.job_match import JobMatch
from app.models.resume import Resume
from app.models.resume_analysis import ResumeAnalysis
from app.models.user import User


def register(client, email="analytics@example.com"):
    response = client.post(
        "/api/auth/register",
        json={"full_name": "Anika Rao", "email": email, "password": "SecurePass1"},
    )
    assert response.status_code == 201
    client.patch(
        "/api/users/profile",
        json={"full_name": "Anika Rao", "target_role": "Backend Engineer", "experience_level": "fresher"},
    )


def evaluation(communication=2):
    values = {
        "accuracy": 3,
        "relevance": 4,
        "clarity": 3,
        "completeness": 2,
        "communication": communication,
    }
    return {
        "overall_score": sum(value * 5 for value in values.values()),
        "rubric_scores": [
            {
                "key": key,
                "label": key.title(),
                "rating": value,
                "score": value * 5,
                "max_score": 20,
                "feedback": f"Stored {key} feedback.",
            }
            for key, value in values.items()
        ],
        "strengths": ["Relevant response"],
        "improvements": ["Add more detail"],
        "coaching_feedback": "Use one concrete example in the next answer.",
    }


def add_analytics_data(database_engine, email="analytics@example.com"):
    base_time = datetime(2026, 8, 1, tzinfo=timezone.utc)
    with Session(database_engine) as database:
        user = database.scalar(select(User).where(User.email == email))
        resume = Resume(
            user_id=user.id,
            original_filename="resume.pdf",
            stored_filename=f"{user.id:032x}.pdf",
            file_size=1000,
            parsed_text="Backend resume",
            structured_data={"technical_skills": ["Python", "FastAPI", "PostgreSQL"]},
            parsing_status="parsed",
        )
        database.add(resume)
        database.flush()
        categories_one = [
            {"key": "skills_relevance", "label": "Skills relevance", "score": 14},
            {"key": "project_quality", "label": "Project quality", "score": 9},
            {"key": "experience_relevance", "label": "Experience relevance", "score": 12},
            {"key": "resume_completeness", "label": "Resume completeness", "score": 15},
            {"key": "clarity_structure", "label": "Clarity and structure", "score": 13},
        ]
        for index, score in enumerate((63, 72)):
            database.add(ResumeAnalysis(
                resume_id=resume.id,
                resume_fingerprint=str(index) * 64,
                overall_score=score,
                category_scores=categories_one,
                analysis_result={"improvement_recommendations": ["Add clearer project evidence."]},
                provider="gemini",
                model_name="test-model",
                rubric_version="1.0",
                created_at=base_time + timedelta(days=index),
            ))
        matches = [
            (60, ["Python", "FastAPI"], ["Docker", "Kubernetes"], ["AWS"]),
            (80, ["Python", "PostgreSQL"], ["Docker"], ["Redis"]),
        ]
        for index, (score, matched, required, preferred) in enumerate(matches):
            database.add(JobMatch(
                user_id=user.id,
                resume_id=resume.id,
                input_fingerprint=str(index + 2) * 64,
                job_title="Backend Engineer",
                job_description="Stored job description",
                parsed_job_requirements={},
                match_result={
                    "matched_skills": matched,
                    "missing_required_skills": required,
                    "missing_preferred_skills": preferred,
                },
                overall_score=score,
                provider="gemini",
                model_name="test-model",
                embedding_model="test-embedding",
                scoring_version="1.0",
                created_at=base_time + timedelta(days=index),
            ))
        for index, score in enumerate((70, 90)):
            session = InterviewSession(
                user_id=user.id,
                target_role="Backend Engineer",
                difficulty="intermediate",
                interview_type="mixed",
                status="completed",
                question_limit=5,
                overall_score=score,
                final_feedback={"summary": "Stored feedback"},
                provider="gemini",
                model_name="test-model",
                started_at=base_time + timedelta(days=index),
                completed_at=base_time + timedelta(days=index, hours=1),
            )
            session.questions.append(InterviewQuestion(
                sequence_number=1,
                question_text="Stored question",
                focus_area="Backend",
                answer_text="Stored answer",
                evaluation=evaluation(communication=1 + index),
                score=score,
                answered_at=base_time + timedelta(days=index, minutes=10),
            ))
            database.add(session)
        database.commit()


def test_dashboard_uses_only_saved_metrics(client, database_engine):
    register(client)
    add_analytics_data(database_engine)

    response = client.get("/api/analytics/dashboard")

    assert response.status_code == 200
    data = response.json()
    assert data["latest_resume_score"] == {"value": 72, "sample_size": 2}
    assert [point["score"] for point in data["resume_score_trend"]] == [63, 72]
    assert data["job_analyses_completed"] == 2
    assert data["average_job_match"] == {"value": 70.0, "sample_size": 2}
    assert data["interviews_completed"] == 2
    assert data["interview_average_score"] == {"value": 80.0, "sample_size": 2}
    assert [point["score"] for point in data["interview_performance_trend"]] == [70, 90]
    assert data["strongest_skills"][0] == {"name": "Python", "match_count": 2, "in_resume": True}
    assert data["common_missing_skills"][0] == {
        "name": "Docker",
        "count": 2,
        "required_count": 2,
        "preferred_count": 0,
    }
    action_titles = [action["title"] for action in data["next_actions"]]
    assert "Improve project quality" in action_titles
    assert "Build evidence for Docker" in action_titles
    assert "Practice interview communication" in action_titles


def test_empty_dashboard_returns_null_metrics_and_real_next_steps(client):
    register(client)

    response = client.get("/api/analytics/dashboard")

    assert response.status_code == 200
    data = response.json()
    assert data["latest_resume_score"]["value"] is None
    assert data["average_job_match"]["value"] is None
    assert data["interview_average_score"]["value"] is None
    assert data["resume_score_trend"] == []
    assert data["strongest_skills"] == []
    assert [action["title"] for action in data["next_actions"]] == [
        "Upload your resume",
        "Complete a mock interview",
    ]


def test_dashboard_data_is_isolated_by_user(client, database_engine):
    register(client, "data-owner@example.com")
    add_analytics_data(database_engine, "data-owner@example.com")
    client.post("/api/auth/logout")
    register(client, "empty-user@example.com")

    data = client.get("/api/analytics/dashboard").json()

    assert data["job_analyses_completed"] == 0
    assert data["interviews_completed"] == 0
    assert data["resume_score_trend"] == []
    assert data["common_missing_skills"] == []


def test_dashboard_requires_authentication(client):
    assert client.get("/api/analytics/dashboard").status_code == 401
