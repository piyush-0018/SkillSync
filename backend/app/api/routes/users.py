from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.dependencies.auth import CurrentUser
from app.db.session import get_db
from app.schemas.user import UserProfileUpdate, UserResponse
from app.services.user_service import update_user_profile

router = APIRouter(prefix="/users", tags=["users"])
Database = Annotated[Session, Depends(get_db)]


@router.get("/profile", response_model=UserResponse)
def get_profile(user: CurrentUser) -> UserResponse:
    return UserResponse.model_validate(user)


@router.patch("/profile", response_model=UserResponse)
def update_profile(payload: UserProfileUpdate, user: CurrentUser, database: Database) -> UserResponse:
    updated_user = update_user_profile(database, user, payload)
    return UserResponse.model_validate(updated_user)
