from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, ValidationInfo, field_validator


class ResumeAnalysisNarrative(BaseModel):
    profile_summary: str = Field(min_length=20, max_length=1200)
    technical_skills_evaluation: str = Field(min_length=20, max_length=1200)
    projects_evaluation: str = Field(min_length=20, max_length=1200)
    experience_evaluation: str = Field(min_length=20, max_length=1200)
    education_evaluation: str = Field(min_length=20, max_length=1200)
    strengths: list[str] = Field(min_length=1, max_length=8)
    weaknesses: list[str] = Field(max_length=8)
    missing_information: list[str] = Field(max_length=8)
    improvement_recommendations: list[str] = Field(min_length=1, max_length=10)
    suggested_skills: list[str] = Field(max_length=10)
    ats_observations: list[str] = Field(max_length=8)

    model_config = ConfigDict(extra="forbid")


class ResumeAnalysisLLMOutput(ResumeAnalysisNarrative):
    @field_validator(
        "strengths",
        "weaknesses",
        "missing_information",
        "improvement_recommendations",
        "suggested_skills",
        "ats_observations",
        mode="before",
    )
    @classmethod
    def normalize_generated_lists(cls, value: object, info: ValidationInfo) -> object:
        if not isinstance(value, list):
            return value
        limits = {
            "strengths": 8,
            "weaknesses": 8,
            "missing_information": 8,
            "improvement_recommendations": 10,
            "suggested_skills": 10,
            "ats_observations": 8,
        }
        cleaned: list[str] = []
        seen: set[str] = set()
        for item in value:
            if not isinstance(item, str):
                continue
            text = " ".join(item.split())[:300]
            key = text.casefold()
            if text and key not in seen:
                cleaned.append(text)
                seen.add(key)
            if len(cleaned) == limits[info.field_name]:
                break
        return cleaned


class CategoryScore(BaseModel):
    key: str
    label: str
    score: int = Field(ge=0, le=20)
    max_score: int = Field(default=20, ge=20, le=20)
    rubric: str
    explanation: str


class ResumeAnalysisResponse(BaseModel):
    id: int
    resume_id: int
    overall_score: int = Field(ge=0, le=100)
    category_scores: list[CategoryScore] = Field(min_length=5, max_length=5)
    analysis: ResumeAnalysisNarrative
    created_at: datetime
    provider: str
    model: str
    rubric_version: str
    is_cached: bool = False
    disclaimer: str = "AI-generated resume-readiness analysis. It is not a proprietary ATS score."


class ResumeAnalysisHistory(BaseModel):
    items: list[ResumeAnalysisResponse]
