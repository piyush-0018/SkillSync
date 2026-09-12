from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

SourceType = Literal["profile", "resume", "resume_analysis", "job_match"]
MessageRole = Literal["user", "assistant"]
GroundingMode = Literal["user_data", "general", "mixed"]


class CareerQuestionRequest(BaseModel):
    conversation_id: int | None = Field(default=None, gt=0)
    content: str = Field(min_length=2, max_length=2_000)

    @field_validator("content", mode="before")
    @classmethod
    def clean_content(cls, value: object) -> object:
        return value.strip() if isinstance(value, str) else value


class CareerSourceResponse(BaseModel):
    context_id: str
    label: str
    source_type: SourceType
    source_record_id: int | None = None


class CareerConversationResponse(BaseModel):
    id: int
    title: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class CareerMessageResponse(BaseModel):
    id: int
    role: MessageRole
    content: str
    created_at: datetime
    grounding_mode: GroundingMode | None = None
    sources: list[CareerSourceResponse] = Field(default_factory=list)
    provider: str | None = None
    model: str | None = None


class CareerConversationList(BaseModel):
    items: list[CareerConversationResponse]


class CareerConversationDetail(BaseModel):
    conversation: CareerConversationResponse
    messages: list[CareerMessageResponse]


class CareerTurnResponse(BaseModel):
    conversation: CareerConversationResponse
    user_message: CareerMessageResponse
    assistant_message: CareerMessageResponse


class CareerAssistantLLMOutput(BaseModel):
    personalized_guidance: str | None = Field(default=None, max_length=5_000)
    general_guidance: str | None = Field(default=None, max_length=5_000)
    unavailable_information: list[str] = Field(default_factory=list, max_length=8)
    used_context_ids: list[str] = Field(default_factory=list, max_length=12)

    model_config = ConfigDict(extra="forbid")

    @field_validator("personalized_guidance", "general_guidance")
    @classmethod
    def empty_guidance_is_none(cls, value: str | None) -> str | None:
        if value is None:
            return None
        cleaned = value.strip()
        return cleaned or None

    @field_validator("unavailable_information", "used_context_ids")
    @classmethod
    def clean_list_values(cls, values: list[str]) -> list[str]:
        return list(dict.fromkeys(value.strip() for value in values if value.strip()))

    @model_validator(mode="after")
    def contains_an_answer(self) -> "CareerAssistantLLMOutput":
        if not self.personalized_guidance and not self.general_guidance:
            raise ValueError("The assistant response did not contain guidance")
        return self
