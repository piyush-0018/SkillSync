import httpx
import pytest
from pydantic import BaseModel

from app.services.ai_client import AIError, AIModelNotFoundError
from app.services.gemini_client import GeminiClient


class ExampleOutput(BaseModel):
    summary: str
    priorities: list[str]


def response(status_code: int, payload: dict) -> httpx.Response:
    request = httpx.Request("POST", "https://generativelanguage.googleapis.com/v1beta/models/test")
    return httpx.Response(status_code, json=payload, request=request)


def client() -> GeminiClient:
    return GeminiClient(
        api_key="test-gemini-key",
        timeout=30,
        max_output_tokens=512,
        embedding_dimensions=768,
    )


def test_structured_chat_sends_schema_and_validates_response(monkeypatch):
    captured = {}

    def fake_post(url, *, json, timeout, headers):
        captured.update(url=url, payload=json, timeout=timeout, headers=headers)
        return response(
            200,
            {
                "candidates": [
                    {
                        "content": {
                            "parts": [
                                {"text": '{"summary":"Focused profile","priorities":["Add evidence"]}'}
                            ]
                        }
                    }
                ]
            },
        )

    monkeypatch.setattr(httpx, "post", fake_post)
    result = client().chat_structured(
        model="gemini-test",
        system_prompt="Be concise.",
        prompt="Review this resume.",
        response_model=ExampleOutput,
    )

    assert result.summary == "Focused profile"
    assert captured["url"].endswith("/models/gemini-test:generateContent")
    assert captured["payload"]["generationConfig"]["responseJsonSchema"] == ExampleOutput.model_json_schema()
    assert captured["headers"] == {"x-goog-api-key": "test-gemini-key"}
    assert "test-gemini-key" not in str(captured["payload"])


def test_embeddings_use_configured_dimensions_and_preserve_order(monkeypatch):
    captured = {}

    def fake_post(url, **kwargs):
        captured.update(url=url, **kwargs)
        return response(200, {"embeddings": [{"values": [0.1, 0.2]}, {"values": [0.3, 0.4]}]})

    monkeypatch.setattr(httpx, "post", fake_post)
    embeddings = client().embed(model="gemini-embedding-001", inputs=["job", "project"])

    assert embeddings == [[0.1, 0.2], [0.3, 0.4]]
    assert captured["url"].endswith("/models/gemini-embedding-001:batchEmbedContents")
    assert [request["content"]["parts"][0]["text"] for request in captured["json"]["requests"]] == [
        "job",
        "project",
    ]
    assert all(request["outputDimensionality"] == 768 for request in captured["json"]["requests"])


def test_missing_model_has_a_specific_error(monkeypatch):
    monkeypatch.setattr(httpx, "post", lambda *args, **kwargs: response(404, {"error": "missing"}))

    with pytest.raises(AIModelNotFoundError) as error:
        client().embed(model="missing", inputs=["text"])

    assert error.value.model == "missing"


@pytest.mark.parametrize(
    "vectors",
    [
        [{"values": [True, 0.1]}],
        [{"values": [0.0, 0.0]}],
        [{"values": ["not-a-number", 0.1]}],
        [{"values": []}, {"values": []}],
        [{"values": [0.1]}, {"values": [0.2, 0.3]}],
    ],
)
def test_malformed_vectors_are_rejected(monkeypatch, vectors):
    monkeypatch.setattr(httpx, "post", lambda *args, **kwargs: response(200, {"embeddings": vectors}))

    with pytest.raises(AIError, match="invalid embeddings"):
        client().embed(model="test", inputs=["text"] * len(vectors))


def test_transport_failure_has_safe_error(monkeypatch):
    def fail(*args, **kwargs):
        raise httpx.RemoteProtocolError("private transport detail")

    monkeypatch.setattr(httpx, "post", fail)
    with pytest.raises(AIError, match="invalid transport response"):
        client().embed(model="test", inputs=["text"])
