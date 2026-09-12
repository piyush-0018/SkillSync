from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.interview_question import InterviewQuestion
from app.models.interview_session import InterviewSession
from app.schemas.interview import (
    AnswerEvaluationLLMOutput,
    CriterionAssessment,
    FinalInterviewLLMOutput,
    InterviewQuestionLLMOutput,
)
from app.services import interview_service
from app.services.ai_client import AIError


def register(client, email="interview@example.com"):
    response = client.post(
        "/api/auth/register",
        json={"full_name": "Riya Kapoor", "email": email, "password": "SecurePass1"},
    )
    assert response.status_code == 201
    client.patch(
        "/api/users/profile",
        json={
            "full_name": "Riya Kapoor",
            "target_role": "Backend Engineer",
            "experience_level": "fresher",
        },
    )


def assessment(rating, feedback):
    return CriterionAssessment(rating=rating, feedback=feedback)


def answer_output(next_question=True):
    return AnswerEvaluationLLMOutput(
        accuracy=assessment(3, "The core technical explanation is correct."),
        relevance=assessment(4, "The response directly addresses the question."),
        clarity=assessment(3, "The response follows a clear structure."),
        completeness=assessment(2, "One concrete trade-off is still missing."),
        communication=assessment(4, "The language is concise and professional."),
        strengths=["Direct explanation", "Good terminology"],
        improvements=["Add one production example"],
        coaching_feedback="Keep the structure and support the decision with one measurable example.",
        next_question=InterviewQuestionLLMOutput(
            question="How would you handle database transactions when one operation fails?",
            focus_area="Transactions",
        ) if next_question else None,
    )


class FakeInterviewClient:
    def __init__(self, outputs):
        self.outputs = list(outputs)
        self.prompts = []

    def chat_structured(self, **kwargs):
        self.prompts.append(kwargs["prompt"])
        return self.outputs.pop(0)


def configure(monkeypatch, outputs):
    fake = FakeInterviewClient(outputs)
    monkeypatch.setattr(interview_service, "_client", lambda: fake)
    return fake


def first_question():
    return InterviewQuestionLLMOutput(
        question="Explain how dependency injection helps structure a FastAPI application.",
        focus_area="FastAPI architecture",
    )


def final_feedback():
    return FinalInterviewLLMOutput(
        summary="You gave relevant answers with clear terminology, but examples need more depth.",
        technical_strengths=["FastAPI fundamentals"],
        weak_areas=["Production trade-offs"],
        communication_feedback="Your answers were concise and logically ordered.",
        topics_to_revise=["Database transactions"],
        suggested_next_steps=["Practice explaining one project with measurable outcomes."],
    )


def test_full_interview_flow_uses_fixed_rubric_scoring(client, monkeypatch):
    register(client)
    fake = configure(monkeypatch, [first_question(), answer_output(), final_feedback()])

    started = client.post(
        "/api/interviews",
        json={
            "target_role": "Backend Engineer",
            "difficulty": "intermediate",
            "interview_type": "mixed",
            "response_mode": "video",
        },
    )
    assert started.status_code == 201
    session_id = started.json()["id"]
    assert started.json()["questions"][0]["sequence_number"] == 1
    assert started.json()["response_mode"] == "video"

    answered = client.post(
        f"/api/interviews/{session_id}/answers",
        json={"answer": "I use dependencies to share validation and database lifecycle logic."},
    )
    assert answered.status_code == 200
    evaluation = answered.json()["evaluated_question"]["evaluation"]
    assert evaluation["overall_score"] == 80
    assert [item["score"] for item in evaluation["rubric_scores"]] == [15, 20, 15, 10, 20]
    assert answered.json()["next_question"]["sequence_number"] == 2

    finished = client.post(f"/api/interviews/{session_id}/finish")
    assert finished.status_code == 200
    assert finished.json()["status"] == "completed"
    assert finished.json()["overall_score"] == 80
    assert finished.json()["final_feedback"]["topics_to_revise"] == ["Database transactions"]
    assert "fixed rubric" not in fake.prompts[-1].lower()

    history = client.get("/api/interviews").json()["items"]
    assert history[0]["id"] == session_id
    assert history[0]["answered_count"] == 1
    assert history[0]["response_mode"] == "video"


def test_repeated_follow_up_is_rejected_without_saving_answer(client, database_engine, monkeypatch):
    register(client)
    repeated = answer_output()
    repeated.next_question = first_question()
    configure(monkeypatch, [first_question(), repeated])
    session_id = client.post(
        "/api/interviews",
        json={"target_role": "Backend Engineer", "difficulty": "beginner", "interview_type": "technical"},
    ).json()["id"]

    response = client.post(
        f"/api/interviews/{session_id}/answers",
        json={"answer": "Dependencies provide values to path operations."},
    )
    assert response.status_code == 502
    with Session(database_engine) as database:
        questions = database.scalars(
            select(InterviewQuestion).where(InterviewQuestion.session_id == session_id)
        ).all()
        assert len(questions) == 1
        assert questions[0].answer_text is None


def test_missing_follow_up_uses_a_separate_generation_call(client, monkeypatch):
    register(client)
    fallback_question = InterviewQuestionLLMOutput(
        question="Describe how you would test a FastAPI dependency in isolation.",
        focus_area="Testing",
    )
    fake = configure(monkeypatch, [first_question(), answer_output(next_question=False), fallback_question])
    session_id = client.post(
        "/api/interviews",
        json={"target_role": "Backend Engineer", "difficulty": "intermediate", "interview_type": "mixed"},
    ).json()["id"]

    response = client.post(
        f"/api/interviews/{session_id}/answers",
        json={"answer": "I keep route concerns small and override dependencies in focused tests."},
    )

    assert response.status_code == 200
    assert response.json()["next_question"]["question_text"] == fallback_question.question
    assert len(fake.prompts) == 3


def test_failed_start_and_finish_do_not_store_partial_state(client, database_engine, monkeypatch):
    register(client)

    class FailingClient:
        def chat_structured(self, **kwargs):
            raise AIError("bad output")

    monkeypatch.setattr(interview_service, "_client", lambda: FailingClient())
    failed_start = client.post(
        "/api/interviews",
        json={"target_role": "Backend Engineer", "difficulty": "advanced", "interview_type": "technical"},
    )
    assert failed_start.status_code == 502
    with Session(database_engine) as database:
        assert database.scalar(select(func.count()).select_from(InterviewSession)) == 0

    configure(monkeypatch, [first_question(), answer_output()])
    session_id = client.post(
        "/api/interviews",
        json={"target_role": "Backend Engineer", "difficulty": "advanced", "interview_type": "technical"},
    ).json()["id"]
    client.post(f"/api/interviews/{session_id}/answers", json={"answer": "A detailed answer."})
    monkeypatch.setattr(interview_service, "_client", lambda: FailingClient())
    assert client.post(f"/api/interviews/{session_id}/finish").status_code == 502
    assert client.get(f"/api/interviews/{session_id}").json()["status"] == "active"


def test_interview_sessions_are_private(client, monkeypatch):
    configure(monkeypatch, [first_question()])
    register(client, "owner@example.com")
    session_id = client.post(
        "/api/interviews",
        json={"target_role": "Backend Engineer", "difficulty": "beginner", "interview_type": "behavioral"},
    ).json()["id"]
    client.post("/api/auth/logout")
    register(client, "other@example.com")

    assert client.get(f"/api/interviews/{session_id}").status_code == 404
    assert client.post(f"/api/interviews/{session_id}/answers", json={"answer": "Hidden"}).status_code == 404
    assert client.post(f"/api/interviews/{session_id}/finish").status_code == 404
    assert client.get("/api/interviews").json()["items"] == []


def test_interview_state_and_input_validation(client, monkeypatch):
    register(client)
    configure(monkeypatch, [first_question()])
    session_id = client.post(
        "/api/interviews",
        json={"target_role": "Backend Engineer", "difficulty": "intermediate", "interview_type": "resume_based"},
    ).json()["id"]

    assert client.post(f"/api/interviews/{session_id}/finish").status_code == 409
    assert client.post(f"/api/interviews/{session_id}/answers", json={"answer": " "}).status_code == 422
    assert client.post(
        "/api/interviews",
        json={"target_role": "Backend Engineer", "difficulty": "expert", "interview_type": "technical"},
    ).status_code == 422
    assert client.post(
        "/api/interviews",
        json={
            "target_role": "Backend Engineer",
            "difficulty": "beginner",
            "interview_type": "technical",
            "response_mode": "avatar",
        },
    ).status_code == 422


def test_interview_endpoints_require_authentication(client):
    assert client.get("/api/interviews").status_code == 401
    assert client.get("/api/interviews/1").status_code == 401
    assert client.post(
        "/api/interviews",
        json={"target_role": "Backend Engineer", "difficulty": "beginner", "interview_type": "technical"},
    ).status_code == 401
