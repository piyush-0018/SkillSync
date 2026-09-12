from typing import Annotated

from fastapi import APIRouter, Depends, File, HTTPException, Response, UploadFile, status
from sqlalchemy.orm import Session

from app.api.dependencies.auth import CurrentUser
from app.db.session import get_db
from app.schemas.resume import ResumeResponse
from app.services.resume_service import ResumeUploadError, delete_user_resume, get_user_resume, save_resume

router = APIRouter(prefix="/resumes", tags=["resumes"])
Database = Annotated[Session, Depends(get_db)]


@router.get("/current", response_model=ResumeResponse)
def current_resume(user: CurrentUser, database: Database) -> ResumeResponse:
    resume = get_user_resume(database, user.id)
    if not resume:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No resume has been uploaded")
    return ResumeResponse.model_validate(resume)


@router.post("", response_model=ResumeResponse, status_code=status.HTTP_201_CREATED)
def upload_resume(user: CurrentUser, database: Database, file: UploadFile = File(...)) -> ResumeResponse:
    try:
        resume = save_resume(database, user.id, file)
    except ResumeUploadError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.detail) from exc
    return ResumeResponse.model_validate(resume)


@router.delete("/current", status_code=status.HTTP_204_NO_CONTENT)
def delete_resume(user: CurrentUser, database: Database) -> Response:
    resume = get_user_resume(database, user.id)
    if not resume:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No resume has been uploaded")
    delete_user_resume(database, resume)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
