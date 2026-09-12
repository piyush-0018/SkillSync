import hashlib
import json
import re
from dataclasses import dataclass
from typing import Any

from pydantic import ValidationError
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.resume import Resume
from app.models.resume_analysis import ResumeAnalysis
from app.models.user import User
from app.prompts.resume_analysis import SYSTEM_PROMPT, build_analysis_prompt
from app.schemas.resume_analysis import (
    CategoryScore,
    ResumeAnalysisLLMOutput,
    ResumeAnalysisNarrative,
    ResumeAnalysisResponse,
)
from app.services.ai_client import (
    AIConfigurationError,
    AIConnectionError,
    AIError,
    AIModelNotFoundError,
    AIClient,
    create_ai_client,
)

RUBRIC_VERSION = "1.0"
PROVIDER = "gemini"
TARGET_STOP_WORDS = {"and", "developer", "engineer", "intern", "junior", "senior", "the", "with"}
ACTION_VERBS = {
    "built", "created", "delivered", "designed", "developed", "implemented", "improved", "increased",
    "launched", "led", "optimized", "reduced", "resolved", "scaled", "shipped", "streamlined",
}


class AnalysisConfigurationError(Exception):
    pass


class AnalysisGenerationError(Exception):
    pass


@dataclass(frozen=True)
class GeneratedFeedback:
    narrative: ResumeAnalysisNarrative
    response_id: str | None


def _items(data: dict[str, Any], key: str) -> list[str]:
    value = data.get(key, [])
    return [str(item).strip() for item in value if str(item).strip()] if isinstance(value, list) else []


def _tokens(value: str) -> set[str]:
    return set(re.findall(r"[a-z][a-z0-9+#.-]{1,}", value.lower()))


def _phrase_hits(phrases: list[str], text: str, limit: int) -> int:
    normalized = text.lower()
    return min(limit, sum(1 for phrase in phrases if phrase.lower() in normalized))


def _target_hits(target_role: str | None, text: str, limit: int) -> int:
    if not target_role:
        return 0
    target_terms = _tokens(target_role) - TARGET_STOP_WORDS
    return min(limit, len(target_terms & _tokens(text)))


def _quantity_hits(text: str, limit: int) -> int:
    matches = re.findall(r"(?:₹|\$)?\b\d+(?:\.\d+)?%?\b", text)
    return min(limit, len(matches))


def _score(
    key: str,
    label: str,
    value: int,
    rubric: str,
    explanation: str,
) -> CategoryScore:
    return CategoryScore(
        key=key,
        label=label,
        score=min(20, max(0, value)),
        rubric=rubric,
        explanation=explanation,
    )


def calculate_resume_scores(resume: Resume, target_role: str | None) -> list[CategoryScore]:
    data = resume.structured_data or {}
    skills = _items(data, "technical_skills")
    projects = _items(data, "projects")
    experience = _items(data, "experience")
    education = _items(data, "education")
    certifications = _items(data, "certifications")
    achievements = _items(data, "achievements")
    contact = data.get("contact", {}) if isinstance(data.get("contact"), dict) else {}

    project_text = " ".join(projects)
    experience_text = " ".join(experience)
    evidence_text = f"{project_text} {experience_text}"
    resume_text = resume.parsed_text or ""

    skill_presence = 6 if skills else 0
    skill_breadth = min(6, len(skills))
    skill_evidence = _phrase_hits(skills, evidence_text, 4)
    skill_targeting = _target_hits(target_role, resume_text, 4)
    skills_score = skill_presence + skill_breadth + skill_evidence + skill_targeting

    project_presence = 6 if projects else 0
    project_detail = min(6, len(projects) * 2)
    project_tools = _phrase_hits(skills, project_text, 3)
    project_impact = _quantity_hits(project_text, 3)
    project_actions = 2 if ACTION_VERBS & _tokens(project_text) else 0
    projects_score = project_presence + project_detail + project_tools + project_impact + project_actions

    experience_presence = 6 if experience else 0
    experience_detail = min(5, len(experience))
    experience_targeting = _target_hits(target_role, experience_text, 4)
    experience_skills = _phrase_hits(skills, experience_text, 3)
    experience_impact = _quantity_hits(experience_text, 2)
    experience_score = (
        experience_presence + experience_detail + experience_targeting + experience_skills + experience_impact
    )

    completeness_checks = [
        bool(data.get("name")),
        bool(contact.get("email")),
        bool(contact.get("phone")),
        bool(education),
        bool(skills),
        bool(projects),
        bool(experience),
        bool(certifications or achievements),
        bool(contact.get("linkedin") or contact.get("github")),
        len(resume_text) >= 600,
    ]
    completeness_score = sum(completeness_checks) * 2

    represented_sections = sum(bool(section) for section in [education, skills, projects, experience, certifications or achievements])
    readable_length = 4 if 300 <= len(resume_text) <= 12_000 else 2 if len(resume_text) >= 120 else 0
    non_empty_lines = sum(bool(line.strip()) for line in resume_text.splitlines())
    line_structure = 2 if 8 <= non_empty_lines <= 180 else 0
    reachable = 2 if contact.get("email") or contact.get("phone") else 0
    quantified = min(2, _quantity_hits(f"{project_text} {experience_text}", 2))
    clarity_score = represented_sections * 2 + readable_length + line_structure + reachable + quantified

    return [
        _score(
            "skills_relevance",
            "Skills relevance",
            skills_score,
            "Section presence (6), breadth (6), evidence in work (4), target-role alignment (4).",
            f"Found {len(skills)} extracted skills; {skill_evidence} are evidenced in projects or experience.",
        ),
        _score(
            "project_quality",
            "Project quality",
            projects_score,
            "Project presence (6), detail (6), tools used (3), measurable impact (3), action language (2).",
            f"Found {len(projects)} project detail lines and {project_impact} measurable outcome indicators.",
        ),
        _score(
            "experience_relevance",
            "Experience relevance",
            experience_score,
            "Experience presence (6), detail (5), target alignment (4), skill evidence (3), impact (2).",
            f"Found {len(experience)} experience detail lines with {experience_impact} measurable outcome indicators.",
        ),
        _score(
            "resume_completeness",
            "Resume completeness",
            completeness_score,
            "Ten essential resume signals worth 2 points each, including contact, core sections, links, and content depth.",
            f"Detected {sum(completeness_checks)} of 10 essential resume signals.",
        ),
        _score(
            "clarity_structure",
            "Clarity and structure",
            clarity_score,
            "Core section coverage (10), readable length (4), line structure (2), contact visibility (2), quantification (2).",
            f"Detected {represented_sections} of 5 core content sections with readable text structure.",
        ),
    ]


def _fingerprint(resume: Resume) -> str:
    user = resume.user
    profile = {"target_role": user.target_role, "experience_level": user.experience_level} if user else {}
    source = f"{RUBRIC_VERSION}\n{resume.parsed_text}\n{json.dumps(resume.structured_data, sort_keys=True)}\n{json.dumps(profile, sort_keys=True)}"
    return hashlib.sha256(source.encode("utf-8")).hexdigest()


def _client() -> AIClient:
    try:
        return create_ai_client(settings)
    except AIConfigurationError as exc:
        raise AnalysisConfigurationError(str(exc)) from exc


def generate_resume_feedback(
    resume: Resume,
    user: User,
    scores: list[CategoryScore],
) -> GeneratedFeedback:
    prompt = build_analysis_prompt(
        resume_text=resume.parsed_text[: settings.resume_analysis_max_characters],
        structured_data=resume.structured_data or {},
        category_scores=scores,
        target_role=user.target_role,
        experience_level=user.experience_level,
    )

    try:
        structured_output = _client().chat_structured(
            model=settings.gemini_model,
            system_prompt=SYSTEM_PROMPT,
            prompt=prompt,
            response_model=ResumeAnalysisLLMOutput,
        )
        narrative = ResumeAnalysisNarrative.model_validate(structured_output.model_dump())
    except AIConnectionError as exc:
        raise AnalysisConfigurationError("Gemini is currently unreachable. Please retry shortly.") from exc
    except AIModelNotFoundError as exc:
        raise AnalysisConfigurationError(f'Gemini model "{exc.model}" is unavailable.') from exc
    except AnalysisConfigurationError:
        raise
    except AnalysisGenerationError:
        raise
    except (AIError, ValidationError, TypeError, ValueError) as exc:
        raise AnalysisGenerationError("The AI analysis could not be completed. Please retry in a moment.") from exc

    return GeneratedFeedback(narrative=narrative, response_id=None)


def _to_response(record: ResumeAnalysis, *, is_cached: bool) -> ResumeAnalysisResponse:
    return ResumeAnalysisResponse(
        id=record.id,
        resume_id=record.resume_id,
        overall_score=record.overall_score,
        category_scores=record.category_scores,
        analysis=record.analysis_result,
        created_at=record.created_at,
        provider=record.provider,
        model=record.model_name,
        rubric_version=record.rubric_version,
        is_cached=is_cached,
    )


def latest_analysis(database: Session, resume: Resume) -> ResumeAnalysis | None:
    return database.scalar(
        select(ResumeAnalysis)
        .where(
            ResumeAnalysis.resume_id == resume.id,
            ResumeAnalysis.resume_fingerprint == _fingerprint(resume),
        )
        .order_by(ResumeAnalysis.created_at.desc(), ResumeAnalysis.id.desc())
    )


def analyze_resume(
    database: Session,
    resume: Resume,
    user: User,
    *,
    refresh: bool,
) -> ResumeAnalysisResponse:
    fingerprint = _fingerprint(resume)
    if not refresh:
        cached = database.scalar(
            select(ResumeAnalysis)
            .where(
                ResumeAnalysis.resume_id == resume.id,
                ResumeAnalysis.resume_fingerprint == fingerprint,
                ResumeAnalysis.provider == PROVIDER,
                ResumeAnalysis.model_name == settings.gemini_model,
                ResumeAnalysis.rubric_version == RUBRIC_VERSION,
            )
            .order_by(ResumeAnalysis.created_at.desc(), ResumeAnalysis.id.desc())
        )
        if cached:
            return _to_response(cached, is_cached=True)

    scores = calculate_resume_scores(resume, user.target_role)
    generated = generate_resume_feedback(resume, user, scores)
    record = ResumeAnalysis(
        resume_id=resume.id,
        resume_fingerprint=fingerprint,
        overall_score=sum(category.score for category in scores),
        category_scores=[category.model_dump() for category in scores],
        analysis_result=generated.narrative.model_dump(),
        provider=PROVIDER,
        model_name=settings.gemini_model,
        provider_response_id=generated.response_id,
        rubric_version=RUBRIC_VERSION,
    )
    database.add(record)
    try:
        database.commit()
        database.refresh(record)
    except Exception:
        database.rollback()
        raise
    return _to_response(record, is_cached=False)


def get_latest_analysis(database: Session, resume: Resume) -> ResumeAnalysisResponse | None:
    record = latest_analysis(database, resume)
    return _to_response(record, is_cached=True) if record else None


def get_analysis_history(database: Session, resume: Resume, limit: int) -> list[ResumeAnalysisResponse]:
    records = database.scalars(
        select(ResumeAnalysis)
        .where(ResumeAnalysis.resume_id == resume.id)
        .order_by(ResumeAnalysis.created_at.desc(), ResumeAnalysis.id.desc())
        .limit(limit)
    ).all()
    return [_to_response(record, is_cached=True) for record in records]
