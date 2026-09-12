from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.api.dependencies.auth import CurrentUser
from app.core.config import settings
from app.core.security import create_access_token
from app.db.session import get_db
from app.schemas.auth import AuthResponse, LoginRequest, MessageResponse, RegisterRequest
from app.schemas.user import UserResponse
from app.services.user_service import authenticate_user, create_user, get_user_by_email

router = APIRouter(prefix="/auth", tags=["authentication"])
Database = Annotated[Session, Depends(get_db)]


def set_session_cookie(response: Response, user_id: int) -> None:
    response.set_cookie(
        key=settings.auth_cookie_name,
        value=create_access_token(user_id),
        max_age=settings.access_token_expire_minutes * 60,
        httponly=True,
        secure=settings.auth_cookie_secure,
        samesite="lax",
        path=settings.api_prefix,
    )


@router.post("/register", response_model=AuthResponse, status_code=status.HTTP_201_CREATED)
def register(payload: RegisterRequest, response: Response, database: Database) -> AuthResponse:
    if get_user_by_email(database, str(payload.email)):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="An account with this email already exists")

    try:
        user = create_user(database, payload)
    except IntegrityError as exc:
        database.rollback()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="An account with this email already exists") from exc

    set_session_cookie(response, user.id)
    return AuthResponse(message="Account created successfully", user=UserResponse.model_validate(user))


@router.post("/login", response_model=AuthResponse)
def login(payload: LoginRequest, response: Response, database: Database) -> AuthResponse:
    user = authenticate_user(database, str(payload.email), payload.password)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Email or password is incorrect")

    set_session_cookie(response, user.id)
    return AuthResponse(message="Signed in successfully", user=UserResponse.model_validate(user))


@router.get("/me", response_model=UserResponse)
def current_user(user: CurrentUser) -> UserResponse:
    return UserResponse.model_validate(user)


@router.post("/logout", response_model=MessageResponse)
def logout(response: Response) -> MessageResponse:
    response.delete_cookie(
        key=settings.auth_cookie_name,
        path=settings.api_prefix,
        secure=settings.auth_cookie_secure,
        httponly=True,
        samesite="lax",
    )
    return MessageResponse(message="Signed out successfully")
