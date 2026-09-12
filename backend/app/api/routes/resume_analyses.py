from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api.dependencies.auth import CurrentUser
from app.db.session import get_db
from app.models.resume import Resume
from app.schemas.resume_analysis import ResumeAnalysisHistory, ResumeAnalysisResponse
from app.services import resume_analysis_service
from app.services.resume_service import get_user_resume

router = APIRouter(prefix="/resume-analyses", tags=["resume analysis"])
Database = Annotated[Session, Depends(get_db)]


def _analysis_ready_resume(database: Session, user_id: int) -> Resume:
    resume = get_user_resume(database, user_id)
    if not resume:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Upload a resume before starting an analysis.")
    if resume.parsing_status != "parsed" or not resume.parsed_text.strip():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="This resume has no readable text. Replace it with a text-based PDF before starting an analysis.",
        )
    return resume


@router.post("", response_model=ResumeAnalysisResponse, status_code=status.HTTP_201_CREATED)
def create_analysis(
    user: CurrentUser,
    database: Database,
    refresh: Annotated[bool, Query(description="Run the model again even when an unchanged analysis exists")] = False,
) -> ResumeAnalysisResponse:
    resume = _analysis_ready_resume(database, user.id)
    try:
        return resume_analysis_service.analyze_resume(database, resume, user, refresh=refresh)
    except resume_analysis_service.AnalysisConfigurationError as exc:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(exc)) from exc
    except resume_analysis_service.AnalysisGenerationError as exc:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(exc)) from exc


@router.get("/latest", response_model=ResumeAnalysisResponse)
def current_analysis(user: CurrentUser, database: Database) -> ResumeAnalysisResponse:
    resume = _analysis_ready_resume(database, user.id)
    analysis = resume_analysis_service.get_latest_analysis(database, resume)
    if not analysis:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No analysis exists for the current resume.")
    return analysis


@router.get("", response_model=ResumeAnalysisHistory)
def analysis_history(
    user: CurrentUser,
    database: Database,
    limit: Annotated[int, Query(ge=1, le=20)] = 10,
) -> ResumeAnalysisHistory:
    resume = _analysis_ready_resume(database, user.id)
    return ResumeAnalysisHistory(items=resume_analysis_service.get_analysis_history(database, resume, limit))
