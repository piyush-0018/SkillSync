from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


class AnalyticsMetric(BaseModel):
    value: float | int | None
    sample_size: int = Field(ge=0)


class ScoreTrendPoint(BaseModel):
    id: int
    score: float = Field(ge=0, le=100)
    recorded_at: datetime
    label: str


class SkillStrength(BaseModel):
    name: str
    match_count: int = Field(ge=0)
    in_resume: bool


class MissingSkillFrequency(BaseModel):
    name: str
    count: int = Field(gt=0)
    required_count: int = Field(ge=0)
    preferred_count: int = Field(ge=0)


class NextAction(BaseModel):
    key: str
    title: str
    description: str
    path: str
    source: Literal["resume", "resume_analysis", "job_matches", "interviews"]


class CareerAnalyticsDashboard(BaseModel):
    latest_resume_score: AnalyticsMetric
    resume_score_trend: list[ScoreTrendPoint]
    job_analyses_completed: int = Field(ge=0)
    average_job_match: AnalyticsMetric
    strongest_skills: list[SkillStrength]
    common_missing_skills: list[MissingSkillFrequency]
    interviews_completed: int = Field(ge=0)
    interview_average_score: AnalyticsMetric
    interview_performance_trend: list[ScoreTrendPoint]
    next_actions: list[NextAction]
    has_resume: bool
    resume_status: str | None
    generated_at: datetime
