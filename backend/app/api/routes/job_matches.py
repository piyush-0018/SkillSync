from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api.dependencies.auth import CurrentUser
from app.db.session import get_db
from app.models.resume import Resume
from app.schemas.job_match import JobMatchHistory, JobMatchRequest, JobMatchResponse
from app.services import job_match_service
from app.services.resume_service import get_user_resume

router = APIRouter(prefix="/job-matches", tags=["job matching"])
Database = Annotated[Session, Depends(get_db)]


def _matching_ready_resume(database: Session, user_id: int) -> Resume:
    resume = get_user_resume(database, user_id)
    if not resume:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Upload a resume before matching a job.")
    if resume.parsing_status != "parsed" or not resume.parsed_text.strip():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="This resume has no readable text. Replace it with a text-based PDF before matching a job.",
        )
    return resume


@router.post("", response_model=JobMatchResponse, status_code=status.HTTP_201_CREATED)
def create_job_match(
    payload: JobMatchRequest,
    user: CurrentUser,
    database: Database,
    refresh: Annotated[bool, Query(description="Analyze again even when the job and resume are unchanged")] = False,
) -> JobMatchResponse:
    resume = _matching_ready_resume(database, user.id)
    try:
        return job_match_service.analyze_job_match(
            database,
            user,
            resume,
            payload.job_description,
            refresh=refresh,
        )
    except job_match_service.JobMatchConfigurationError as exc:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(exc)) from exc
    except job_match_service.JobMatchGenerationError as exc:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(exc)) from exc


@router.get("", response_model=JobMatchHistory)
def job_match_history(
    user: CurrentUser,
    database: Database,
    limit: Annotated[int, Query(ge=1, le=20)] = 10,
) -> JobMatchHistory:
    return JobMatchHistory(items=job_match_service.get_job_match_history(database, user.id, limit))


@router.get("/{match_id}", response_model=JobMatchResponse)
def job_match_detail(match_id: int, user: CurrentUser, database: Database) -> JobMatchResponse:
    result = job_match_service.get_job_match(database, user.id, match_id)
    if not result:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job analysis not found.")
    return result
