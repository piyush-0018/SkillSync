import hashlib
import json
import math

from pydantic import ValidationError
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.job_match import JobMatch
from app.models.resume import Resume
from app.models.user import User
from app.prompts.job_match import SYSTEM_PROMPT, build_job_interpretation_prompt
from app.schemas.job_match import (
    JobInterpretationLLMOutput,
    JobMatchNarrative,
    JobMatchResponse,
    JobMatchResult,
    JobRequirements,
)
from app.services.job_match_scoring import SCORING_VERSION, calculate_job_match
from app.services.ai_client import (
    AIClient,
    AIConfigurationError,
    AIConnectionError,
    AIError,
    AIModelNotFoundError,
    create_ai_client,
)

PROVIDER = "gemini"


class JobMatchConfigurationError(Exception):
    pass


class JobMatchGenerationError(Exception):
    pass


def _client() -> AIClient:
    try:
        return create_ai_client(settings)
    except AIConfigurationError as exc:
        raise JobMatchConfigurationError(str(exc)) from exc


def _fingerprint(job_description: str, resume: Resume, user: User) -> str:
    source = {
        "job_description": " ".join(job_description.lower().split()),
        "resume_text": resume.parsed_text,
        "resume_data": resume.structured_data,
        "target_role": user.target_role,
        "experience_level": user.experience_level,
        "provider": PROVIDER,
        "model": settings.gemini_model,
        "embedding_model": settings.gemini_embedding_model,
        "scoring_version": SCORING_VERSION,
    }
    return hashlib.sha256(json.dumps(source, sort_keys=True).encode("utf-8")).hexdigest()


def _interpret_job(client: AIClient, job_description: str, resume: Resume, user: User) -> tuple[JobRequirements, JobMatchNarrative, str | None]:
    prompt = build_job_interpretation_prompt(
        job_description=job_description,
        resume_text=resume.parsed_text[: settings.resume_analysis_max_characters],
        resume_data=resume.structured_data or {},
        target_role=user.target_role,
        experience_level=user.experience_level,
    )
    output = client.chat_structured(
        model=settings.gemini_model,
        system_prompt=SYSTEM_PROMPT,
        prompt=prompt,
        response_model=JobInterpretationLLMOutput,
    )
    output = output.model_dump()
    requirements = JobRequirements.model_validate(
        {key: output[key] for key in JobRequirements.model_fields}
    )
    narrative = JobMatchNarrative.model_validate(
        {key: output[key] for key in JobMatchNarrative.model_fields}
    )
    return requirements, narrative, None


def _cosine_similarity(first: list[float], second: list[float]) -> float:
    denominator = math.sqrt(sum(value * value for value in first)) * math.sqrt(sum(value * value for value in second))
    if denominator == 0:
        return 0.0
    return max(-1.0, min(1.0, sum(a * b for a, b in zip(first, second, strict=True)) / denominator))


def _semantic_similarity(client: AIClient, requirements: JobRequirements, resume: Resume) -> float:
    project_text = " ".join((resume.structured_data or {}).get("projects", []))
    if not project_text.strip():
        return 0.0

    job_context = " ".join(
        [requirements.job_title or ""]
        + requirements.required_skills
        + requirements.preferred_skills
        + requirements.tools_technologies
        + requirements.responsibilities
    )
    if not job_context.strip():
        return 0.0

    embeddings = client.embed(
        model=settings.gemini_embedding_model,
        inputs=[job_context[:8_000], project_text[:8_000]],
    )
    return _cosine_similarity(embeddings[0], embeddings[1])


def _to_response(record: JobMatch, *, is_cached: bool) -> JobMatchResponse:
    return JobMatchResponse(
        id=record.id,
        job_title=record.job_title,
        job_description=record.job_description,
        parsed_job=record.parsed_job_requirements,
        result=record.match_result,
        created_at=record.created_at,
        provider=record.provider,
        model=record.model_name,
        embedding_model=record.embedding_model,
        scoring_version=record.scoring_version,
        is_cached=is_cached,
    )


def _grounded_guidance(
    categories,
    missing_required: list[str],
    missing_preferred: list[str],
) -> tuple[str, str, str, list[str]]:
    by_key = {category.key: category for category in categories}
    recommendations: list[str] = []
    if missing_required:
        recommendations.append(
            "Build and document verifiable evidence for the missing required skills: "
            + ", ".join(missing_required[:5])
            + "."
        )
    if missing_preferred:
        recommendations.append(
            "After the required gaps, consider adding evidence for these preferred skills: "
            + ", ".join(missing_preferred[:5])
            + "."
        )
    if by_key["experience"].score < by_key["experience"].max_score:
        recommendations.append(
            "Add concise, verifiable experience bullets that connect your work to this role's responsibilities."
        )
    if by_key["projects"].score < by_key["projects"].max_score:
        recommendations.append(
            "Strengthen project bullets with your contribution, relevant technologies, and measurable outcomes."
        )
    if not recommendations:
        recommendations.append("Keep the strongest matching evidence specific, recent, and easy to verify.")
    return (
        by_key["experience"].explanation,
        by_key["education"].explanation,
        by_key["projects"].explanation,
        recommendations[:6],
    )


def analyze_job_match(
    database: Session,
    user: User,
    resume: Resume,
    job_description: str,
    *,
    refresh: bool,
) -> JobMatchResponse:
    fingerprint = _fingerprint(job_description, resume, user)
    if not refresh:
        cached = database.scalar(
            select(JobMatch)
            .where(JobMatch.user_id == user.id, JobMatch.input_fingerprint == fingerprint)
            .order_by(JobMatch.created_at.desc(), JobMatch.id.desc())
        )
        if cached:
            return _to_response(cached, is_cached=True)

    try:
        client = _client()
        requirements, _narrative, response_id = _interpret_job(client, job_description, resume, user)
        similarity = _semantic_similarity(client, requirements, resume)
        categories, matched, missing_required, missing_preferred, required_percent, preferred_percent = (
            calculate_job_match(
                resume=resume,
                requirements=requirements,
                experience_level=user.experience_level,
                semantic_similarity=similarity,
            )
        )
    except AIConnectionError as exc:
        raise JobMatchConfigurationError("Gemini is currently unreachable. Please retry shortly.") from exc
    except AIModelNotFoundError as exc:
        raise JobMatchConfigurationError(f'Gemini model "{exc.model}" is unavailable.') from exc
    except JobMatchConfigurationError:
        raise
    except JobMatchGenerationError:
        raise
    except (AIError, ValidationError, TypeError, ValueError) as exc:
        raise JobMatchGenerationError("The AI job match could not be completed. Please retry in a moment.") from exc

    experience_alignment, education_alignment, project_relevance, recommendations = _grounded_guidance(
        categories,
        missing_required,
        missing_preferred,
    )
    result = JobMatchResult(
        overall_score=sum(category.score for category in categories),
        required_skill_match=required_percent,
        preferred_skill_match=preferred_percent,
        matched_skills=matched,
        missing_required_skills=missing_required,
        missing_preferred_skills=missing_preferred,
        category_scores=categories,
        experience_alignment=experience_alignment,
        education_alignment=education_alignment,
        project_relevance=project_relevance,
        recommendations=recommendations,
        semantic_similarity=similarity,
    )
    record = JobMatch(
        user_id=user.id,
        resume_id=resume.id,
        input_fingerprint=fingerprint,
        job_title=requirements.job_title,
        job_description=job_description,
        parsed_job_requirements=requirements.model_dump(),
        match_result=result.model_dump(),
        overall_score=result.overall_score,
        provider=PROVIDER,
        model_name=settings.gemini_model,
        embedding_model=settings.gemini_embedding_model,
        provider_response_id=response_id,
        scoring_version=SCORING_VERSION,
    )
    database.add(record)
    try:
        database.commit()
        database.refresh(record)
    except Exception:
        database.rollback()
        raise
    return _to_response(record, is_cached=False)


def get_job_match_history(database: Session, user_id: int, limit: int) -> list[JobMatchResponse]:
    records = database.scalars(
        select(JobMatch)
        .where(JobMatch.user_id == user_id)
        .order_by(JobMatch.created_at.desc(), JobMatch.id.desc())
        .limit(limit)
    ).all()
    return [_to_response(record, is_cached=True) for record in records]


def get_job_match(database: Session, user_id: int, match_id: int) -> JobMatchResponse | None:
    record = database.scalar(select(JobMatch).where(JobMatch.id == match_id, JobMatch.user_id == user_id))
    return _to_response(record, is_cached=True) if record else None
