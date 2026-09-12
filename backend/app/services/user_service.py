from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.security import hash_password, verify_password
from app.models.user import User
from app.schemas.auth import RegisterRequest
from app.schemas.user import UserProfileUpdate

DUMMY_PASSWORD_HASH = hash_password("SkillSync-login-timing-placeholder-1")


def get_user_by_email(database: Session, email: str) -> User | None:
    normalized_email = email.strip().lower()
    return database.scalar(select(User).where(User.email == normalized_email))


def get_user_by_id(database: Session, user_id: int) -> User | None:
    return database.get(User, user_id)


def create_user(database: Session, payload: RegisterRequest) -> User:
    user = User(
        full_name=payload.full_name,
        email=str(payload.email).lower(),
        password_hash=hash_password(payload.password),
    )
    database.add(user)
    database.commit()
    database.refresh(user)
    return user


def authenticate_user(database: Session, email: str, password: str) -> User | None:
    user = get_user_by_email(database, email)
    candidate_hash = user.password_hash if user else DUMMY_PASSWORD_HASH
    password_is_valid = verify_password(password, candidate_hash)
    if not user or not password_is_valid:
        return None
    return user


def update_user_profile(database: Session, user: User, payload: UserProfileUpdate) -> User:
    user.full_name = payload.full_name
    user.target_role = payload.target_role
    user.experience_level = payload.experience_level
    database.commit()
    database.refresh(user)
    return user
