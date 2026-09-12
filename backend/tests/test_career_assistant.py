from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.career_conversation import CareerConversation
from app.models.career_message import CareerMessage
from app.schemas.career_assistant import CareerAssistantLLMOutput
from app.services import career_assistant_service
from app.services.career_context_service import RetrievedContext
from app.services.ai_client import AIConnectionError, AIError


def register(client, email="aarav@example.com"):
    response = client.post(
        "/api/auth/register",
        json={"full_name": "Aarav Sharma", "email": email, "password": "SecurePass1"},
    )
    assert response.status_code == 201
    client.patch(
        "/api/users/profile",
        json={
            "full_name": "Aarav Sharma",
            "target_role": "Backend Engineer",
            "experience_level": "fresher",
        },
    )


class FakeCareerClient:
    def __init__(self, output=None):
        self.output = output or CareerAssistantLLMOutput(
            personalized_guidance="Prioritize the API project because it supports your backend target.",
            general_guidance="Add measurable outcomes and a concise explanation of your decisions.",
            unavailable_information=[],
            used_context_ids=["C1"],
        )

    def chat_structured(self, **kwargs):
        return self.output


def configure_assistant(monkeypatch):
    monkeypatch.setattr(career_assistant_service, "_client", lambda: FakeCareerClient())
    monkeypatch.setattr(career_assistant_service, "sync_user_documents", lambda *args: None)
    monkeypatch.setattr(
        career_assistant_service,
        "retrieve_context",
        lambda *args: [
            RetrievedContext(
                context_id="C1",
                label="Resume · Projects",
                source_type="resume",
                source_record_id=7,
                content="Built a career platform API with FastAPI.",
                similarity=0.82,
            )
        ],
    )


def test_conversation_flow_is_saved_and_retrievable(client, monkeypatch):
    register(client)
    configure_assistant(monkeypatch)

    created = client.post(
        "/api/career-assistant/messages",
        json={"conversation_id": None, "content": "Which project should I highlight?"},
    )

    assert created.status_code == 201
    payload = created.json()
    conversation_id = payload["conversation"]["id"]
    assert payload["assistant_message"]["grounding_mode"] == "mixed"
    assert payload["assistant_message"]["sources"][0]["label"] == "Resume · Projects"
    assert "Based on your SkillSync data" in payload["assistant_message"]["content"]

    conversations = client.get("/api/career-assistant/conversations").json()["items"]
    assert [item["id"] for item in conversations] == [conversation_id]

    detail = client.get(f"/api/career-assistant/conversations/{conversation_id}")
    assert detail.status_code == 200
    assert [message["role"] for message in detail.json()["messages"]] == ["user", "assistant"]

    follow_up = client.post(
        "/api/career-assistant/messages",
        json={"conversation_id": conversation_id, "content": "How should I describe it?"},
    )
    assert follow_up.status_code == 201
    assert len(client.get(f"/api/career-assistant/conversations/{conversation_id}").json()["messages"]) == 4

    assert client.delete(f"/api/career-assistant/conversations/{conversation_id}").status_code == 204
    assert client.get(f"/api/career-assistant/conversations/{conversation_id}").status_code == 404


def test_conversations_are_private_between_users(client, monkeypatch):
    configure_assistant(monkeypatch)
    register(client, "first@example.com")
    first = client.post(
        "/api/career-assistant/messages",
        json={"conversation_id": None, "content": "What should I learn next?"},
    ).json()["conversation"]["id"]
    client.post("/api/auth/logout")

    register(client, "second@example.com")
    assert client.get("/api/career-assistant/conversations").json()["items"] == []
    assert client.get(f"/api/career-assistant/conversations/{first}").status_code == 404
    assert client.post(
        "/api/career-assistant/messages",
        json={"conversation_id": first, "content": "Show me this conversation."},
    ).status_code == 404
    assert client.delete(f"/api/career-assistant/conversations/{first}").status_code == 404


def test_failed_generation_does_not_store_partial_messages(client, database_engine, monkeypatch):
    register(client)
    monkeypatch.setattr(career_assistant_service, "sync_user_documents", lambda *args: None)
    monkeypatch.setattr(career_assistant_service, "retrieve_context", lambda *args: [])

    class FailingClient:
        def chat_structured(self, **kwargs):
            raise AIError("invalid output")

    monkeypatch.setattr(career_assistant_service, "_client", lambda: FailingClient())
    response = client.post(
        "/api/career-assistant/messages",
        json={"conversation_id": None, "content": "What should I learn next?"},
    )

    assert response.status_code == 502
    with Session(database_engine) as database:
        assert database.scalar(select(func.count()).select_from(CareerConversation)) == 0
        assert database.scalar(select(func.count()).select_from(CareerMessage)) == 0


def test_personalized_guidance_requires_valid_context_ids(client, database_engine, monkeypatch):
    register(client)
    monkeypatch.setattr(career_assistant_service, "sync_user_documents", lambda *args: None)
    monkeypatch.setattr(
        career_assistant_service,
        "retrieve_context",
        lambda *args: [
            RetrievedContext(
                context_id="C1",
                label="Resume · Projects",
                source_type="resume",
                source_record_id=7,
                content="Built a FastAPI service.",
                similarity=0.9,
            )
        ],
    )
    output = CareerAssistantLLMOutput(
        personalized_guidance="This claim pretends to use private context.",
        general_guidance=None,
        unavailable_information=[],
        used_context_ids=["C999"],
    )
    monkeypatch.setattr(career_assistant_service, "_client", lambda: FakeCareerClient(output))

    response = client.post(
        "/api/career-assistant/messages",
        json={"content": "Which project should I discuss?"},
    )

    assert response.status_code == 502
    assert "invalid source references" in response.json()["detail"]
    with Session(database_engine) as database:
        assert database.scalar(select(func.count()).select_from(CareerConversation)) == 0
        assert database.scalar(select(func.count()).select_from(CareerMessage)) == 0


def test_gemini_connection_error_is_actionable(client, monkeypatch):
    register(client)

    def fail_sync(*args):
        raise AIConnectionError("offline")

    monkeypatch.setattr(career_assistant_service, "sync_user_documents", fail_sync)
    response = client.post(
        "/api/career-assistant/messages",
        json={"conversation_id": None, "content": "Can you review my skills?"},
    )

    assert response.status_code == 503
    assert response.json()["detail"] == "Gemini is currently unreachable. Please retry shortly."


def test_assistant_requires_authentication_and_valid_content(client):
    assert client.get("/api/career-assistant/conversations").status_code == 401
    assert client.post(
        "/api/career-assistant/messages",
        json={"conversation_id": None, "content": "Question"},
    ).status_code == 401
    register(client)
    assert client.post(
        "/api/career-assistant/messages",
        json={"conversation_id": None, "content": " "},
    ).status_code == 422
