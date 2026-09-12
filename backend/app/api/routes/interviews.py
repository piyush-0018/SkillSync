from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api.dependencies.auth import CurrentUser
from app.db.session import get_db
from app.schemas.interview import (
    InterviewAnswerRequest,
    InterviewAnswerResponse,
    InterviewHistoryResponse,
    InterviewSessionDetail,
    InterviewStartRequest,
)
from app.services import interview_service

router = APIRouter(prefix="/interviews", tags=["mock interviews"])
Database = Annotated[Session, Depends(get_db)]


def _run_ai_step(action):
    try:
        return action()
    except interview_service.InterviewConfigurationError as exc:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(exc)) from exc
    except interview_service.InterviewGenerationError as exc:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(exc)) from exc
    except interview_service.InterviewStateError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc


@router.post("", response_model=InterviewSessionDetail, status_code=status.HTTP_201_CREATED)
def start_interview(
    payload: InterviewStartRequest,
    user: CurrentUser,
    database: Database,
) -> InterviewSessionDetail:
    return _run_ai_step(
        lambda: interview_service.start_interview(
            database,
            user,
            target_role=payload.target_role,
            difficulty=payload.difficulty,
            interview_type=payload.interview_type,
            response_mode=payload.response_mode,
        )
    )


@router.get("", response_model=InterviewHistoryResponse)
def interview_history(
    user: CurrentUser,
    database: Database,
    limit: Annotated[int, Query(ge=1, le=50)] = 20,
) -> InterviewHistoryResponse:
    return InterviewHistoryResponse(items=interview_service.list_interviews(database, user.id, limit))


@router.get("/{session_id}", response_model=InterviewSessionDetail)
def interview_detail(
    session_id: int,
    user: CurrentUser,
    database: Database,
) -> InterviewSessionDetail:
    result = interview_service.get_interview(database, user.id, session_id)
    if not result:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Interview session not found.")
    return result


@router.post("/{session_id}/answers", response_model=InterviewAnswerResponse)
def answer_question(
    session_id: int,
    payload: InterviewAnswerRequest,
    user: CurrentUser,
    database: Database,
) -> InterviewAnswerResponse:
    result = _run_ai_step(
        lambda: interview_service.submit_answer(database, user, session_id, payload.answer)
    )
    if not result:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Interview session not found.")
    return result


@router.post("/{session_id}/finish", response_model=InterviewSessionDetail)
def finish_interview(
    session_id: int,
    user: CurrentUser,
    database: Database,
) -> InterviewSessionDetail:
    result = _run_ai_step(lambda: interview_service.finish_interview(database, user, session_id))
    if not result:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Interview session not found.")
    return result
