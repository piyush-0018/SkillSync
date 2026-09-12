from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator


class JobMatchRequest(BaseModel):
    job_description: str = Field(min_length=200, max_length=20_000)

    @field_validator("job_description", mode="before")
    @classmethod
    def clean_description(cls, value: object) -> object:
        return value.strip() if isinstance(value, str) else value


class JobRequirements(BaseModel):
    job_title: str | None = Field(default=None, max_length=160)
    required_skills: list[str] = Field(max_length=40)
    preferred_skills: list[str] = Field(max_length=40)
    experience_requirement: str | None = Field(default=None, max_length=600)
    minimum_years_experience: float | None = Field(default=None, ge=0, le=50)
    education_requirements: list[str] = Field(max_length=15)
    responsibilities: list[str] = Field(max_length=30)
    tools_technologies: list[str] = Field(max_length=40)

    model_config = ConfigDict(extra="forbid")


class JobMatchNarrative(BaseModel):
    experience_alignment: str = Field(min_length=20, max_length=1000)
    education_alignment: str = Field(min_length=20, max_length=1000)
    project_relevance: str = Field(min_length=20, max_length=1000)
    recommendations: list[str] = Field(min_length=1, max_length=10)

    model_config = ConfigDict(extra="forbid")


class JobInterpretationLLMOutput(BaseModel):
    job_title: str | None
    required_skills: list[str]
    preferred_skills: list[str]
    experience_requirement: str | None
    minimum_years_experience: float | None
    education_requirements: list[str]
    responsibilities: list[str]
    tools_technologies: list[str]
    experience_alignment: str
    education_alignment: str
    project_relevance: str
    recommendations: list[str]

    model_config = ConfigDict(extra="forbid")


class MatchCategoryScore(BaseModel):
    key: str
    label: str
    score: int = Field(ge=0)
    max_score: int = Field(gt=0)
    method: str
    explanation: str


class JobMatchResult(BaseModel):
    overall_score: int = Field(ge=0, le=100)
    required_skill_match: int = Field(ge=0, le=100)
    preferred_skill_match: int = Field(ge=0, le=100)
    matched_skills: list[str]
    missing_required_skills: list[str]
    missing_preferred_skills: list[str]
    category_scores: list[MatchCategoryScore] = Field(min_length=5, max_length=5)
    experience_alignment: str
    education_alignment: str
    project_relevance: str
    recommendations: list[str]
    semantic_similarity: float = Field(ge=-1, le=1)


class JobMatchResponse(BaseModel):
    id: int
    job_title: str | None
    job_description: str
    parsed_job: JobRequirements
    result: JobMatchResult
    created_at: datetime
    provider: str
    model: str
    embedding_model: str
    scoring_version: str
    is_cached: bool = False
    disclaimer: str = "SkillSync compatibility score using documented matching rules and AI-assisted interpretation."


class JobMatchHistory(BaseModel):
    items: list[JobMatchResponse]
