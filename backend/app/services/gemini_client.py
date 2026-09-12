from typing import Any
from urllib.parse import quote

import httpx

from app.services.ai_client import (
    AIConnectionError,
    AIError,
    AIModelNotFoundError,
    StructuredResult,
    validate_embedding_matrix,
)

GEMINI_API_BASE_URL = "https://generativelanguage.googleapis.com/v1beta"


class GeminiClient:
    def __init__(
        self,
        *,
        api_key: str,
        timeout: float,
        max_output_tokens: int,
        embedding_dimensions: int,
    ):
        self.timeout = timeout
        self.max_output_tokens = max_output_tokens
        self.embedding_dimensions = embedding_dimensions
        self._headers = {"x-goog-api-key": api_key}

    def _post(self, path: str, payload: dict[str, Any], *, model: str) -> dict[str, Any]:
        try:
            response = httpx.post(
                f"{GEMINI_API_BASE_URL}{path}",
                json=payload,
                timeout=self.timeout,
                headers=self._headers,
            )
        except (httpx.ConnectError, httpx.NetworkError) as exc:
            raise AIConnectionError("Could not connect to Gemini.") from exc
        except httpx.TimeoutException as exc:
            raise AIError("Gemini took too long to respond.") from exc
        except httpx.RequestError as exc:
            raise AIError("Gemini returned an invalid transport response.") from exc

        if response.status_code == 404:
            raise AIModelNotFoundError(model)
        try:
            response.raise_for_status()
            data = response.json()
        except (httpx.HTTPStatusError, ValueError) as exc:
            raise AIError("Gemini returned an invalid response.") from exc
        if not isinstance(data, dict):
            raise AIError("Gemini returned an invalid response.")
        return data

    def chat_structured(
        self,
        *,
        model: str,
        system_prompt: str,
        prompt: str,
        response_model: type[StructuredResult],
    ) -> StructuredResult:
        model_path = quote(model, safe="")
        data = self._post(
            f"/models/{model_path}:generateContent",
            {
                "systemInstruction": {"parts": [{"text": system_prompt}]},
                "contents": [{"role": "user", "parts": [{"text": prompt}]}],
                "generationConfig": {
                    "temperature": 0,
                    "maxOutputTokens": self.max_output_tokens,
                    "responseMimeType": "application/json",
                    "responseJsonSchema": response_model.model_json_schema(),
                },
            },
            model=model,
        )
        try:
            parts = data["candidates"][0]["content"]["parts"]
            content = "".join(part.get("text", "") for part in parts if isinstance(part, dict))
        except (KeyError, IndexError, TypeError) as exc:
            raise AIError("Gemini returned an invalid chat response.") from exc
        if not content:
            raise AIError("Gemini returned an invalid chat response.")
        return response_model.model_validate_json(content)

    def embed(self, *, model: str, inputs: list[str]) -> list[list[float]]:
        model_path = quote(model, safe="")
        model_resource = f"models/{model}"
        data = self._post(
            f"/models/{model_path}:batchEmbedContents",
            {
                "requests": [
                    {
                        "model": model_resource,
                        "content": {"parts": [{"text": value}]},
                        "taskType": "SEMANTIC_SIMILARITY",
                        "outputDimensionality": self.embedding_dimensions,
                    }
                    for value in inputs
                ]
            },
            model=model,
        )
        raw_embeddings = data.get("embeddings")
        if not isinstance(raw_embeddings, list):
            raise AIError("Gemini returned invalid embeddings.")
        embeddings = [item.get("values") if isinstance(item, dict) else None for item in raw_embeddings]
        return validate_embedding_matrix(embeddings, expected_count=len(inputs))
