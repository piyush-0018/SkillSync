from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.session import get_db

from app.schemas.health import HealthResponse

router = APIRouter(tags=["system"])


@router.get("/health", response_model=HealthResponse)
def health_check() -> HealthResponse:
    return HealthResponse(status="healthy", application="SkillSync")


@router.get("/ready", response_model=HealthResponse)
def readiness_check(database: Session = Depends(get_db)) -> HealthResponse:
    try:
        database.execute(text("SELECT 1"))
        if settings.rag_vector_backend == "pgvector":
            database.execute(text("SELECT '[1,0]'::vector <=> '[1,0]'::vector"))
    except SQLAlchemyError:
        raise HTTPException(status_code=503, detail="Service dependencies are not ready") from None
    return HealthResponse(status="healthy", application="SkillSync")
