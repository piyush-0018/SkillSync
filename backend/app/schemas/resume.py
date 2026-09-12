from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class ContactDetails(BaseModel):
    email: str | None = None
    phone: str | None = None
    linkedin: str | None = None
    github: str | None = None


class ResumeStructuredData(BaseModel):
    name: str | None = None
    contact: ContactDetails = Field(default_factory=ContactDetails)
    education: list[str] = Field(default_factory=list)
    technical_skills: list[str] = Field(default_factory=list)
    projects: list[str] = Field(default_factory=list)
    experience: list[str] = Field(default_factory=list)
    certifications: list[str] = Field(default_factory=list)
    achievements: list[str] = Field(default_factory=list)


class ResumeResponse(BaseModel):
    id: int
    original_filename: str
    file_size: int
    uploaded_at: datetime
    parsing_status: Literal["parsed", "failed"]
    parsing_error: str | None
    structured_data: ResumeStructuredData

    model_config = ConfigDict(from_attributes=True)
