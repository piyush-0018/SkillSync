from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.dependencies.auth import CurrentUser
from app.db.session import get_db
from app.schemas.analytics import CareerAnalyticsDashboard
from app.services.analytics_service import build_dashboard

router = APIRouter(prefix="/analytics", tags=["career analytics"])
Database = Annotated[Session, Depends(get_db)]


@router.get("/dashboard", response_model=CareerAnalyticsDashboard)
def career_dashboard(user: CurrentUser, database: Database) -> CareerAnalyticsDashboard:
    return build_dashboard(database, user)
