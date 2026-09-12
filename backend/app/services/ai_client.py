import math
from typing import TYPE_CHECKING, Protocol, TypeVar

from pydantic import BaseModel

if TYPE_CHECKING:
    from app.core.config import Settings

StructuredResult = TypeVar("StructuredResult", bound=BaseModel)


class AIError(Exception):
    pass


class AIConnectionError(AIError):
    pass


class AIModelNotFoundError(AIError):
    def __init__(self, model: str):
        self.model = model
        super().__init__(f'AI model "{model}" is unavailable.')


class AIConfigurationError(AIError):
    pass


class AIClient(Protocol):
    def chat_structured(
        self,
        *,
        model: str,
        system_prompt: str,
        prompt: str,
        response_model: type[StructuredResult],
    ) -> StructuredResult: ...

    def embed(self, *, model: str, inputs: list[str]) -> list[list[float]]: ...


def validate_embedding_matrix(
    embeddings: object,
    *,
    expected_count: int,
) -> list[list[float]]:
    if not isinstance(embeddings, list) or len(embeddings) != expected_count:
        raise AIError("AI provider returned invalid embeddings.")
    if any(not isinstance(vector, list) or not vector for vector in embeddings):
        raise AIError("AI provider returned invalid embeddings.")

    dimensions = len(embeddings[0]) if embeddings else 0
    if any(
        len(vector) != dimensions
        or any(type(value) not in (int, float) or not math.isfinite(value) for value in vector)
        or not any(vector)
        for vector in embeddings
    ):
        raise AIError("AI provider returned invalid embeddings.")
    return embeddings


def create_ai_client(config: "Settings") -> AIClient:
    from app.services.gemini_client import GeminiClient

    api_key = config.gemini_api_key.get_secret_value()
    if not api_key:
        raise AIConfigurationError("GEMINI_API_KEY is required for AI features.")
    return GeminiClient(
        api_key=api_key,
        timeout=config.ai_timeout_seconds,
        max_output_tokens=config.ai_max_output_tokens,
        embedding_dimensions=config.rag_embedding_dimensions,
    )
