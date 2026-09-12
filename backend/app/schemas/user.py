from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator

ExperienceLevel = Literal["student", "fresher", "0-1 years", "1-3 years", "3+ years"]


class UserBase(BaseModel):
    full_name: str = Field(min_length=2, max_length=100)
    email: EmailStr

    @field_validator("full_name", mode="before")
    @classmethod
    def clean_full_name(cls, value: object) -> object:
        return " ".join(value.split()) if isinstance(value, str) else value


class UserProfileUpdate(BaseModel):
    full_name: str = Field(min_length=2, max_length=100)
    target_role: str | None = Field(default=None, max_length=100)
    experience_level: ExperienceLevel | None = None

    @field_validator("full_name", mode="before")
    @classmethod
    def clean_full_name(cls, value: object) -> object:
        return " ".join(value.split()) if isinstance(value, str) else value

    @field_validator("target_role")
    @classmethod
    def clean_target_role(cls, value: str | None) -> str | None:
        if value is None:
            return None
        cleaned = " ".join(value.split())
        return cleaned or None


class UserResponse(UserBase):
    id: int
    target_role: str | None
    experience_level: ExperienceLevel | None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
