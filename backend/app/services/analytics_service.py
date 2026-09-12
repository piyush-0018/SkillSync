from collections import Counter, defaultdict
from datetime import datetime, timezone
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.models.interview_session import InterviewSession
from app.models.job_match import JobMatch
from app.models.resume import Resume
from app.models.resume_analysis import ResumeAnalysis
from app.models.user import User
from app.schemas.analytics import (
    AnalyticsMetric,
    CareerAnalyticsDashboard,
    MissingSkillFrequency,
    NextAction,
    ScoreTrendPoint,
    SkillStrength,
)
from app.services.job_match_scoring import normalize_skill

TREND_LIMIT = 8
SKILL_LIMIT = 6


def _average(values: list[float | int]) -> float | None:
    return round(sum(values) / len(values), 1) if values else None


def _display_skill(value: str) -> str:
    cleaned = value.strip()
    return cleaned if cleaned else value


def _resume_skills(resume: Resume | None) -> list[str]:
    if not resume or resume.parsing_status != "parsed":
        return []
    value = (resume.structured_data or {}).get("technical_skills", [])
    return [str(item).strip() for item in value if str(item).strip()] if isinstance(value, list) else []


def _skill_insights(resume: Resume | None, job_matches: list[JobMatch]) -> list[SkillStrength]:
    resume_values = _resume_skills(resume)
    display_names: dict[str, str] = {}
    resume_keys = set()
    match_counts: Counter[str] = Counter()

    for skill in resume_values:
        key = normalize_skill(skill)
        if key:
            resume_keys.add(key)
            display_names.setdefault(key, _display_skill(skill))

    for match in job_matches:
        matched = match.match_result.get("matched_skills", []) if isinstance(match.match_result, dict) else []
        seen = set()
        for value in matched if isinstance(matched, list) else []:
            skill = str(value).strip()
            key = normalize_skill(skill)
            if key and key not in seen:
                seen.add(key)
                match_counts[key] += 1
                display_names.setdefault(key, _display_skill(skill))

    keys = resume_keys | set(match_counts)
    ranked = sorted(keys, key=lambda key: (-match_counts[key], display_names[key].lower()))[:SKILL_LIMIT]
    return [
        SkillStrength(name=display_names[key], match_count=match_counts[key], in_resume=key in resume_keys)
        for key in ranked
    ]


def _missing_skill_insights(job_matches: list[JobMatch]) -> list[MissingSkillFrequency]:
    totals: Counter[str] = Counter()
    required: Counter[str] = Counter()
    preferred: Counter[str] = Counter()
    display_names: dict[str, str] = {}

    for match in job_matches:
        result = match.match_result if isinstance(match.match_result, dict) else {}
        missing_in_job = set()
        for field, counter in (("missing_required_skills", required), ("missing_preferred_skills", preferred)):
            values = result.get(field, [])
            seen = set()
            for value in values if isinstance(values, list) else []:
                skill = str(value).strip()
                key = normalize_skill(skill)
                if key and key not in seen:
                    seen.add(key)
                    counter[key] += 1
                    missing_in_job.add(key)
                    display_names.setdefault(key, _display_skill(skill))
        totals.update(missing_in_job)

    ranked = sorted(totals, key=lambda key: (-required[key], -totals[key], display_names[key].lower()))[:SKILL_LIMIT]
    return [
        MissingSkillFrequency(
            name=display_names[key],
            count=totals[key],
            required_count=required[key],
            preferred_count=preferred[key],
        )
        for key in ranked
    ]


def _lowest_interview_criterion(sessions: list[InterviewSession]) -> tuple[str, float] | None:
    ratings: dict[str, list[int]] = defaultdict(list)
    labels: dict[str, str] = {}
    for session in sessions:
        for question in session.questions:
            evaluation = question.evaluation if isinstance(question.evaluation, dict) else {}
            rubric_scores = evaluation.get("rubric_scores", [])
            for item in rubric_scores if isinstance(rubric_scores, list) else []:
                if not isinstance(item, dict):
                    continue
                key = str(item.get("key", "")).strip()
                rating = item.get("rating")
                if key and isinstance(rating, int):
                    ratings[key].append(rating)
                    labels[key] = str(item.get("label") or key.replace("_", " ").title())
    if not ratings:
        return None
    key = min(ratings, key=lambda value: sum(ratings[value]) / len(ratings[value]))
    return labels[key], round(sum(ratings[key]) / len(ratings[key]), 1)


def _resume_category_action(latest: ResumeAnalysis | None) -> NextAction | None:
    if not latest or not latest.category_scores:
        return None
    valid = [item for item in latest.category_scores if isinstance(item, dict) and isinstance(item.get("score"), int)]
    if not valid:
        return None
    weakest = min(valid, key=lambda item: item["score"])
    label = str(weakest.get("label") or "resume section")
    return NextAction(
        key=f'resume-{weakest.get("key", "readiness")}',
        title=f"Improve {label.lower()}",
        description=f"This is the lowest category in your latest resume analysis at {weakest['score']}/20.",
        path="/resume/analysis",
        source="resume_analysis",
    )


def _next_actions(
    *,
    resume: Resume | None,
    latest_analysis: ResumeAnalysis | None,
    job_matches: list[JobMatch],
    missing_skills: list[MissingSkillFrequency],
    completed_interviews: list[InterviewSession],
) -> list[NextAction]:
    actions: list[NextAction] = []
    if not resume:
        actions.append(NextAction(
            key="upload-resume",
            title="Upload your resume",
            description="Resume analytics and personalized comparisons need a parsed resume.",
            path="/resume",
            source="resume",
        ))
    elif resume.parsing_status != "parsed":
        actions.append(NextAction(
            key="replace-resume",
            title="Replace the unreadable resume",
            description="The current PDF could not be parsed, so resume-based insights are unavailable.",
            path="/resume",
            source="resume",
        ))
    elif not latest_analysis:
        actions.append(NextAction(
            key="analyze-resume",
            title="Analyze your resume",
            description="Your resume is parsed, but it does not have a readiness analysis yet.",
            path="/resume/analysis",
            source="resume_analysis",
        ))
    else:
        category_action = _resume_category_action(latest_analysis)
        if category_action:
            actions.append(category_action)

    if not job_matches:
        if resume and resume.parsing_status == "parsed":
            actions.append(NextAction(
                key="analyze-job",
                title="Analyze a target job",
                description="No saved job comparison is available to identify role-specific gaps.",
                path="/job-match",
                source="job_matches",
            ))
    elif missing_skills:
        skill = missing_skills[0]
        qualifier = "required" if skill.required_count else "preferred"
        actions.append(NextAction(
            key=f"skill-{normalize_skill(skill.name)}",
            title=f"Build evidence for {skill.name}",
            description=(
                f"It is missing as a {qualifier} skill in {skill.required_count or skill.preferred_count} "
                f"saved job {'analysis' if (skill.required_count or skill.preferred_count) == 1 else 'analyses'}."
            ),
            path="/job-match",
            source="job_matches",
        ))

    if not completed_interviews:
        actions.append(NextAction(
            key="start-interview",
            title="Complete a mock interview",
            description="There is no completed interview yet to measure answer performance.",
            path="/interviews",
            source="interviews",
        ))
    else:
        weakest = _lowest_interview_criterion(completed_interviews)
        if weakest:
            label, rating = weakest
            actions.append(NextAction(
                key=f"interview-{label.lower().replace(' ', '-')}",
                title=f"Practice interview {label.lower()}",
                description=f"{label} is your lowest interview rubric average at {rating}/4.",
                path="/interviews",
                source="interviews",
            ))
    return actions[:4]


def build_dashboard(database: Session, user: User) -> CareerAnalyticsDashboard:
    resume = database.scalar(select(Resume).where(Resume.user_id == user.id))
    analyses = database.scalars(
        select(ResumeAnalysis)
        .join(Resume, ResumeAnalysis.resume_id == Resume.id)
        .where(Resume.user_id == user.id)
        .order_by(ResumeAnalysis.created_at.asc(), ResumeAnalysis.id.asc())
    ).all()
    job_matches = database.scalars(
        select(JobMatch)
        .where(JobMatch.user_id == user.id)
        .order_by(JobMatch.created_at.asc(), JobMatch.id.asc())
    ).all()
    completed_interviews = database.scalars(
        select(InterviewSession)
        .options(selectinload(InterviewSession.questions))
        .where(InterviewSession.user_id == user.id, InterviewSession.status == "completed")
        .order_by(InterviewSession.completed_at.asc(), InterviewSession.id.asc())
    ).all()

    latest_analysis = analyses[-1] if analyses else None
    resume_trend = [
        ScoreTrendPoint(id=item.id, score=item.overall_score, recorded_at=item.created_at, label="Resume analysis")
        for item in analyses[-TREND_LIMIT:]
    ]
    interview_trend = [
        ScoreTrendPoint(
            id=item.id,
            score=item.overall_score or 0,
            recorded_at=item.completed_at or item.created_at,
            label=item.target_role,
        )
        for item in completed_interviews[-TREND_LIMIT:]
        if item.overall_score is not None
    ]
    missing_skills = _missing_skill_insights(job_matches)
    job_scores = [item.overall_score for item in job_matches]
    interview_scores = [item.overall_score for item in completed_interviews if item.overall_score is not None]

    return CareerAnalyticsDashboard(
        latest_resume_score=AnalyticsMetric(
            value=latest_analysis.overall_score if latest_analysis else None,
            sample_size=len(analyses),
        ),
        resume_score_trend=resume_trend,
        job_analyses_completed=len(job_matches),
        average_job_match=AnalyticsMetric(value=_average(job_scores), sample_size=len(job_scores)),
        strongest_skills=_skill_insights(resume, job_matches),
        common_missing_skills=missing_skills,
        interviews_completed=len(completed_interviews),
        interview_average_score=AnalyticsMetric(
            value=_average(interview_scores), sample_size=len(interview_scores)
        ),
        interview_performance_trend=interview_trend,
        next_actions=_next_actions(
            resume=resume,
            latest_analysis=latest_analysis,
            job_matches=job_matches,
            missing_skills=missing_skills,
            completed_interviews=completed_interviews,
        ),
        has_resume=resume is not None,
        resume_status=resume.parsing_status if resume else None,
        generated_at=datetime.now(timezone.utc),
    )
