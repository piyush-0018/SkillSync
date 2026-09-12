from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy.orm import Session

from app.api.dependencies.auth import CurrentUser
from app.db.session import get_db
from app.schemas.career_assistant import (
    CareerConversationDetail,
    CareerConversationList,
    CareerQuestionRequest,
    CareerTurnResponse,
)
from app.services import career_assistant_service

router = APIRouter(prefix="/career-assistant", tags=["career assistant"])
Database = Annotated[Session, Depends(get_db)]


@router.get("/conversations", response_model=CareerConversationList)
def conversations(
    user: CurrentUser,
    database: Database,
    limit: Annotated[int, Query(ge=1, le=50)] = 30,
) -> CareerConversationList:
    return CareerConversationList(
        items=career_assistant_service.list_conversations(database, user.id, limit)
    )


@router.get("/conversations/{conversation_id}", response_model=CareerConversationDetail)
def conversation_detail(
    conversation_id: int,
    user: CurrentUser,
    database: Database,
) -> CareerConversationDetail:
    conversation = career_assistant_service.get_conversation(database, user.id, conversation_id)
    if not conversation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found.",
        )
    return conversation


@router.post("/messages", response_model=CareerTurnResponse, status_code=status.HTTP_201_CREATED)
def send_message(
    payload: CareerQuestionRequest,
    user: CurrentUser,
    database: Database,
) -> CareerTurnResponse:
    try:
        result = career_assistant_service.send_message(
            database,
            user,
            payload.content,
            payload.conversation_id,
        )
    except career_assistant_service.CareerAssistantConfigurationError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(exc),
        ) from exc
    except career_assistant_service.CareerAssistantGenerationError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=str(exc),
        ) from exc

    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found.",
        )
    return result


@router.delete("/conversations/{conversation_id}", status_code=status.HTTP_204_NO_CONTENT)
def clear_conversation(
    conversation_id: int,
    user: CurrentUser,
    database: Database,
) -> Response:
    if not career_assistant_service.delete_conversation(database, user.id, conversation_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found.",
        )
    return Response(status_code=status.HTTP_204_NO_CONTENT)
