from datetime import datetime, timezone

from pydantic import ValidationError
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.career_conversation import CareerConversation
from app.models.career_message import CareerMessage
from app.models.user import User
from app.prompts.career_assistant import SYSTEM_PROMPT, build_career_prompt
from app.schemas.career_assistant import (
    CareerAssistantLLMOutput,
    CareerConversationDetail,
    CareerConversationResponse,
    CareerMessageResponse,
    CareerSourceResponse,
    CareerTurnResponse,
)
from app.services.career_context_service import (
    ContextIndexError,
    RetrievedContext,
    retrieve_context,
    sync_user_documents,
)
from app.services.ai_client import (
    AIClient,
    AIConfigurationError,
    AIConnectionError,
    AIError,
    AIModelNotFoundError,
    create_ai_client,
)

PROVIDER = "gemini"
HISTORY_CHARACTER_LIMIT = 6_000


class CareerAssistantConfigurationError(Exception):
    pass


class CareerAssistantGenerationError(Exception):
    pass


def _client() -> AIClient:
    try:
        return create_ai_client(settings)
    except AIConfigurationError as exc:
        raise CareerAssistantConfigurationError(str(exc)) from exc


def _owned_conversation(database: Session, user_id: int, conversation_id: int) -> CareerConversation | None:
    return database.scalar(
        select(CareerConversation).where(
            CareerConversation.id == conversation_id,
            CareerConversation.user_id == user_id,
        )
    )


def _conversation_response(conversation: CareerConversation) -> CareerConversationResponse:
    return CareerConversationResponse.model_validate(conversation)


def _message_response(message: CareerMessage) -> CareerMessageResponse:
    return CareerMessageResponse(
        id=message.id,
        role=message.role,
        content=message.content,
        created_at=message.created_at,
        grounding_mode=message.grounding_mode,
        sources=[CareerSourceResponse.model_validate(source) for source in (message.sources or [])],
        provider=message.provider,
        model=message.model_name,
    )


def list_conversations(database: Session, user_id: int, limit: int) -> list[CareerConversationResponse]:
    conversations = database.scalars(
        select(CareerConversation)
        .where(CareerConversation.user_id == user_id)
        .order_by(CareerConversation.updated_at.desc(), CareerConversation.id.desc())
        .limit(limit)
    ).all()
    return [_conversation_response(conversation) for conversation in conversations]


def get_conversation(
    database: Session,
    user_id: int,
    conversation_id: int,
) -> CareerConversationDetail | None:
    conversation = _owned_conversation(database, user_id, conversation_id)
    if not conversation:
        return None
    messages = database.scalars(
        select(CareerMessage)
        .where(CareerMessage.conversation_id == conversation.id)
        .order_by(CareerMessage.created_at, CareerMessage.id)
    ).all()
    return CareerConversationDetail(
        conversation=_conversation_response(conversation),
        messages=[_message_response(message) for message in messages],
    )


def delete_conversation(database: Session, user_id: int, conversation_id: int) -> bool:
    conversation = _owned_conversation(database, user_id, conversation_id)
    if not conversation:
        return False
    database.delete(conversation)
    database.commit()
    return True


def _recent_messages(database: Session, conversation: CareerConversation | None) -> list[CareerMessage]:
    if not conversation:
        return []
    messages = database.scalars(
        select(CareerMessage)
        .where(CareerMessage.conversation_id == conversation.id)
        .order_by(CareerMessage.created_at.desc(), CareerMessage.id.desc())
        .limit(settings.rag_history_limit)
    ).all()
    return list(reversed(messages))


def _prompt_history(messages: list[CareerMessage]) -> list[dict[str, str]]:
    selected: list[dict[str, str]] = []
    used_characters = 0
    for message in reversed(messages):
        remaining = HISTORY_CHARACTER_LIMIT - used_characters
        if remaining <= 0:
            break
        content = message.content[-remaining:]
        selected.append({"role": message.role, "content": content})
        used_characters += len(content)
    return list(reversed(selected))


def _retrieval_query(question: str, messages: list[CareerMessage]) -> str:
    previous_question = next((message.content for message in reversed(messages) if message.role == "user"), None)
    if not previous_question:
        return question
    return f"Previous question: {previous_question[-800:]}\nCurrent question: {question}"


def _compose_answer(output: CareerAssistantLLMOutput) -> str:
    sections = []
    if output.personalized_guidance:
        sections.append(f"### Based on your SkillSync data\n\n{output.personalized_guidance}")
    if output.general_guidance:
        sections.append(f"### General guidance\n\n{output.general_guidance}")
    if output.unavailable_information:
        missing = "\n".join(f"- {item}" for item in output.unavailable_information)
        sections.append(f"### Information not available\n\n{missing}")
    return "\n\n".join(sections)


def _source_references(
    output: CareerAssistantLLMOutput,
    contexts: list[RetrievedContext],
) -> list[dict[str, object]]:
    by_id = {context.context_id: context for context in contexts}
    used_ids = [context_id for context_id in output.used_context_ids if context_id in by_id]
    references = []
    seen = set()
    for context_id in used_ids:
        context = by_id[context_id]
        source_key = (context.source_type, context.source_record_id, context.label)
        if source_key in seen:
            continue
        seen.add(source_key)
        references.append(context.source_reference())
    return references


def _validate_grounding(
    output: CareerAssistantLLMOutput,
    contexts: list[RetrievedContext],
) -> None:
    available_ids = {context.context_id for context in contexts}
    used_ids = set(output.used_context_ids)
    if used_ids - available_ids:
        raise CareerAssistantGenerationError(
            "The Career Assistant returned invalid source references. Please retry in a moment."
        )
    if output.personalized_guidance and not used_ids:
        raise CareerAssistantGenerationError(
            "The Career Assistant could not ground its personalized guidance. Please retry in a moment."
        )


def _grounding_mode(output: CareerAssistantLLMOutput) -> str:
    if output.personalized_guidance and output.general_guidance:
        return "mixed"
    if output.personalized_guidance:
        return "user_data"
    return "general"


def send_message(
    database: Session,
    user: User,
    content: str,
    conversation_id: int | None,
) -> CareerTurnResponse | None:
    conversation = None
    if conversation_id is not None:
        conversation = _owned_conversation(database, user.id, conversation_id)
        if not conversation:
            return None

    client = _client()
    recent_messages = _recent_messages(database, conversation)
    try:
        sync_user_documents(database, user, client)
        contexts = retrieve_context(
            database,
            user.id,
            _retrieval_query(content, recent_messages),
            client,
        )
        output = client.chat_structured(
            model=settings.gemini_model,
            system_prompt=SYSTEM_PROMPT,
            prompt=build_career_prompt(
                question=content,
                contexts=contexts,
                history=_prompt_history(recent_messages),
            ),
            response_model=CareerAssistantLLMOutput,
        )
        _validate_grounding(output, contexts)
    except AIConnectionError as exc:
        raise CareerAssistantConfigurationError(
            "Gemini is currently unreachable. Please retry shortly."
        ) from exc
    except AIModelNotFoundError as exc:
        raise CareerAssistantConfigurationError(
            f'Gemini model "{exc.model}" is unavailable.'
        ) from exc
    except ContextIndexError as exc:
        raise CareerAssistantConfigurationError(str(exc)) from exc
    except CareerAssistantConfigurationError:
        raise
    except (AIError, ValidationError, TypeError, ValueError) as exc:
        raise CareerAssistantGenerationError(
            "The Career Assistant could not complete that response. Please retry in a moment."
        ) from exc

    answer = _compose_answer(output)
    source_references = _source_references(output, contexts)
    now = datetime.now(timezone.utc)
    if conversation is None:
        title = " ".join(content.split())
        if len(title) > 60:
            title = f"{title[:57].rstrip()}..."
        conversation = CareerConversation(user_id=user.id, title=title, updated_at=now)
        database.add(conversation)
        database.flush()
    else:
        conversation.updated_at = now

    user_message = CareerMessage(
        conversation_id=conversation.id,
        role="user",
        content=content,
        grounding_mode=None,
        sources=[],
    )
    assistant_message = CareerMessage(
        conversation_id=conversation.id,
        role="assistant",
        content=answer,
        grounding_mode=_grounding_mode(output),
        sources=source_references,
        provider=PROVIDER,
        model_name=settings.gemini_model,
    )
    database.add_all([user_message, assistant_message])
    try:
        database.commit()
        database.refresh(conversation)
        database.refresh(user_message)
        database.refresh(assistant_message)
    except Exception:
        database.rollback()
        raise

    return CareerTurnResponse(
        conversation=_conversation_response(conversation),
        user_message=_message_response(user_message),
        assistant_message=_message_response(assistant_message),
    )
