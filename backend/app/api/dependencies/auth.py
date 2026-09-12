from typing import Annotated

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jwt.exceptions import ExpiredSignatureError, InvalidTokenError
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.security import decode_access_token
from app.db.session import get_db
from app.models.user import User
from app.services.user_service import get_user_by_id

bearer_scheme = HTTPBearer(auto_error=False)


def authentication_error(detail: str) -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail=detail,
        headers={"WWW-Authenticate": "Bearer"},
    )


def get_current_user(
    request: Request,
    database: Annotated[Session, Depends(get_db)],
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer_scheme)],
) -> User:
    token = credentials.credentials if credentials else request.cookies.get(settings.auth_cookie_name)
    if not token:
        raise authentication_error("Authentication required")

    try:
        payload = decode_access_token(token)
        if payload.get("type") != "access":
            raise authentication_error("Invalid authentication token")
        subject = payload.get("sub", "")
        if not isinstance(subject, str) or not subject.isascii() or not subject.isdigit() or len(subject) > 10:
            raise authentication_error("Invalid authentication token")
        user_id = int(subject)
        if not 0 < user_id <= 2_147_483_647:
            raise authentication_error("Invalid authentication token")
    except ExpiredSignatureError as exc:
        raise authentication_error("Session expired. Please sign in again") from exc
    except (InvalidTokenError, TypeError, ValueError) as exc:
        raise authentication_error("Invalid authentication token") from exc

    user = get_user_by_id(database, user_id)
    if not user:
        raise authentication_error("Invalid authentication token")
    return user


CurrentUser = Annotated[User, Depends(get_current_user)]
