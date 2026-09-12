from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

Difficulty = Literal["beginner", "intermediate", "advanced"]
InterviewType = Literal["technical", "behavioral", "resume_based", "mixed"]
InterviewStatus = Literal["active", "completed"]
InterviewMode = Literal["text", "video"]


class InterviewStartRequest(BaseModel):
    target_role: str = Field(min_length=2, max_length=100)
    difficulty: Difficulty
    interview_type: InterviewType
    response_mode: InterviewMode = "text"

    @field_validator("target_role", mode="before")
    @classmethod
    def clean_role(cls, value: object) -> object:
        return value.strip() if isinstance(value, str) else value


class InterviewAnswerRequest(BaseModel):
    answer: str = Field(min_length=2, max_length=10_000)

    @field_validator("answer", mode="before")
    @classmethod
    def clean_answer(cls, value: object) -> object:
        return value.strip() if isinstance(value, str) else value


class InterviewQuestionLLMOutput(BaseModel):
    question: str = Field(min_length=10, max_length=1_000)
    focus_area: str = Field(min_length=2, max_length=120)

    model_config = ConfigDict(extra="forbid")

    @field_validator("question", "focus_area")
    @classmethod
    def clean_text(cls, value: str) -> str:
        return value.strip()


class CriterionAssessment(BaseModel):
    rating: Literal[0, 1, 2, 3, 4]
    feedback: str = Field(min_length=5, max_length=600)

    model_config = ConfigDict(extra="forbid")


class AnswerEvaluationLLMOutput(BaseModel):
    accuracy: CriterionAssessment
    relevance: CriterionAssessment
    clarity: CriterionAssessment
    completeness: CriterionAssessment
    communication: CriterionAssessment
    strengths: list[str] = Field(default_factory=list, max_length=5)
    improvements: list[str] = Field(default_factory=list, max_length=5)
    coaching_feedback: str = Field(min_length=10, max_length=1_500)
    next_question: InterviewQuestionLLMOutput | None = None

    model_config = ConfigDict(extra="forbid")


class FinalInterviewLLMOutput(BaseModel):
    summary: str = Field(min_length=20, max_length=1_500)
    technical_strengths: list[str] = Field(default_factory=list, max_length=8)
    weak_areas: list[str] = Field(default_factory=list, max_length=8)
    communication_feedback: str = Field(min_length=10, max_length=1_000)
    topics_to_revise: list[str] = Field(default_factory=list, max_length=10)
    suggested_next_steps: list[str] = Field(min_length=1, max_length=8)

    model_config = ConfigDict(extra="forbid")


class RubricScore(BaseModel):
    key: str
    label: str
    rating: int = Field(ge=0, le=4)
    score: int = Field(ge=0, le=20)
    max_score: int = 20
    feedback: str


class QuestionEvaluation(BaseModel):
    overall_score: int = Field(ge=0, le=100)
    rubric_scores: list[RubricScore] = Field(min_length=5, max_length=5)
    strengths: list[str]
    improvements: list[str]
    coaching_feedback: str


class InterviewQuestionResponse(BaseModel):
    id: int
    sequence_number: int
    question_text: str
    focus_area: str
    answer_text: str | None
    evaluation: QuestionEvaluation | None
    score: float | None
    asked_at: datetime
    answered_at: datetime | None


class FinalInterviewFeedback(BaseModel):
    summary: str
    technical_strengths: list[str]
    weak_areas: list[str]
    communication_feedback: str
    topics_to_revise: list[str]
    suggested_next_steps: list[str]


class InterviewSessionSummary(BaseModel):
    id: int
    target_role: str
    difficulty: Difficulty
    interview_type: InterviewType
    response_mode: InterviewMode
    status: InterviewStatus
    question_limit: int
    answered_count: int
    overall_score: float | None
    started_at: datetime
    completed_at: datetime | None


class InterviewSessionDetail(InterviewSessionSummary):
    questions: list[InterviewQuestionResponse]
    final_feedback: FinalInterviewFeedback | None
    provider: str
    model: str
    disclaimer: str = "SkillSync interview feedback is AI-assisted coaching, not a hiring decision."


class InterviewHistoryResponse(BaseModel):
    items: list[InterviewSessionSummary]


class InterviewAnswerResponse(BaseModel):
    session: InterviewSessionDetail
    evaluated_question: InterviewQuestionResponse
    next_question: InterviewQuestionResponse | None

    @model_validator(mode="after")
    def next_question_is_unanswered(self) -> "InterviewAnswerResponse":
        if self.next_question and self.next_question.answer_text is not None:
            raise ValueError("The next question must be unanswered")
        return self
