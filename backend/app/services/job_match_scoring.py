import re
from typing import Any

from app.models.resume import Resume
from app.schemas.job_match import JobRequirements, MatchCategoryScore

SCORING_VERSION = "1.1"
SKILL_ALIASES = {
    "amazon web services": "aws",
    "artificial intelligence": "ai",
    "c sharp": "c#",
    "c plus plus": "c++",
    "google cloud platform": "gcp",
    "javascript": "javascript",
    "js": "javascript",
    "k8s": "kubernetes",
    "machine learning": "machine learning",
    "ml": "machine learning",
    "node": "node.js",
    "nodejs": "node.js",
    "postgres": "postgresql",
    "reactjs": "react",
    "rest api": "rest",
    "restful api": "rest",
    "ts": "typescript",
}
STOP_WORDS = {
    "and", "are", "for", "from", "into", "our", "that", "the", "their", "this", "using", "will", "with",
    "work", "role", "team", "you", "your", "years", "experience", "responsible", "requirements",
}
EXPERIENCE_ESTIMATES = {"student": 0.0, "fresher": 0.25, "0-1 years": 0.5, "1-3 years": 2.0, "3+ years": 3.5}
DEGREE_TERMS = {
    "bachelor", "bachelors", "btech", "b.e", "be", "master", "masters", "mtech", "mca", "mba", "phd",
    "computer science", "information technology", "engineering",
}


def _clean(value: str) -> str:
    normalized = value.lower().replace("&", " and ")
    normalized = re.sub(r"[^a-z0-9+#. ]", " ", normalized)
    return " ".join(normalized.split())


def normalize_skill(value: str) -> str:
    cleaned = _clean(value)
    if cleaned in SKILL_ALIASES:
        return SKILL_ALIASES[cleaned]
    for alias, canonical in SKILL_ALIASES.items():
        if re.search(rf"(?<!\w){re.escape(alias)}(?!\w)", cleaned):
            return canonical
    return cleaned


def _normalized_skills(values: list[str]) -> dict[str, str]:
    normalized = {}
    for value in values:
        key = normalize_skill(value)
        if key:
            normalized.setdefault(key, value.strip())
    return normalized


def _items(data: dict[str, Any], key: str) -> list[str]:
    value = data.get(key, [])
    return [str(item).strip() for item in value if str(item).strip()] if isinstance(value, list) else []


def _percentage(matched: int, total: int) -> int:
    return 100 if total == 0 else round((matched / total) * 100)


def _category(key: str, label: str, score: int, maximum: int, method: str, explanation: str) -> MatchCategoryScore:
    return MatchCategoryScore(
        key=key,
        label=label,
        score=min(maximum, max(0, score)),
        max_score=maximum,
        method=method,
        explanation=explanation,
    )


def _candidate_years(resume: Resume, experience_level: str | None) -> float:
    experience_text = " ".join(_items(resume.structured_data or {}, "experience"))
    explicit = [float(value) for value in re.findall(r"(\d+(?:\.\d+)?)\+?\s+years?", experience_text.lower())]
    return max(explicit, default=EXPERIENCE_ESTIMATES.get(experience_level or "", 0.0))


def _keyword_overlap(requirements: JobRequirements, text: str) -> tuple[int, int]:
    source = " ".join(
        requirements.required_skills
        + requirements.preferred_skills
        + requirements.tools_technologies
        + requirements.responsibilities
    )
    terms = {word for word in re.findall(r"[a-z][a-z0-9+#.-]{2,}", source.lower()) if word not in STOP_WORDS}
    text_terms = set(re.findall(r"[a-z][a-z0-9+#.-]{2,}", text.lower()))
    return len(terms & text_terms), len(terms)


def calculate_job_match(
    *,
    resume: Resume,
    requirements: JobRequirements,
    experience_level: str | None,
    semantic_similarity: float,
) -> tuple[list[MatchCategoryScore], list[str], list[str], list[str], int, int]:
    data = resume.structured_data or {}
    resume_skills = _normalized_skills(_items(data, "technical_skills"))
    required = _normalized_skills(requirements.required_skills)
    preferred = _normalized_skills(requirements.preferred_skills)
    tool_skills = _normalized_skills(requirements.tools_technologies)

    resume_text = (resume.parsed_text or "").lower()
    resume_keys = set(resume_skills)
    cleaned_resume_text = _clean(resume_text)
    for key in set(required) | set(preferred) | set(tool_skills):
        if key and re.search(rf"(?<![a-z0-9]){re.escape(key)}(?![a-z0-9])", cleaned_resume_text):
            resume_keys.add(key)

    matched_required = [required[key] for key in required if key in resume_keys]
    missing_required = [required[key] for key in required if key not in resume_keys]
    matched_preferred = [preferred[key] for key in preferred if key in resume_keys]
    missing_preferred = [preferred[key] for key in preferred if key not in resume_keys]
    matched_skills = list(dict.fromkeys(matched_required + matched_preferred))

    required_percent = _percentage(len(matched_required), len(required))
    preferred_percent = _percentage(len(matched_preferred), len(preferred))
    required_points = round(required_percent * 0.4)
    preferred_points = round(preferred_percent * 0.15)

    candidate_years = _candidate_years(resume, experience_level)
    required_years = requirements.minimum_years_experience
    experience_text = " ".join(_items(data, "experience"))
    experience_hits, experience_terms = _keyword_overlap(requirements, experience_text)
    relevance_points = round((experience_hits / experience_terms) * 5) if experience_terms else 5
    if required_years is None:
        experience_points = 10 + relevance_points
        experience_explanation = "No numeric minimum was extracted; points reflect available experience evidence and role keywords."
    else:
        years_points = 10 if required_years == 0 else round(min(1, candidate_years / required_years) * 10)
        experience_points = years_points + relevance_points
        experience_explanation = f"Candidate evidence indicates about {candidate_years:g} years against a {required_years:g}-year minimum."

    education_text = _clean(" ".join(_items(data, "education")))
    requirement_text = _clean(" ".join(requirements.education_requirements))
    if not requirements.education_requirements:
        education_points = 10
        education_explanation = "No explicit education requirement was extracted, so no education penalty was applied."
    else:
        resume_degrees = {term for term in DEGREE_TERMS if term in education_text}
        required_degrees = {term for term in DEGREE_TERMS if term in requirement_text}
        if resume_degrees & required_degrees:
            education_points = 10
            education_explanation = "The resume contains degree or field terms that match the stated education requirement."
        elif education_text:
            education_points = 5
            education_explanation = "Education is present, but an exact degree or field match was not identified."
        else:
            education_points = 0
            education_explanation = "No education evidence was identified in the parsed resume."

    project_text = " ".join(_items(data, "projects"))
    project_hits, project_terms = _keyword_overlap(requirements, project_text)
    project_keyword_points = round((project_hits / project_terms) * 8) if project_terms else 0
    semantic_ratio = min(1.0, max(0.0, (semantic_similarity - 0.25) / 0.55)) if project_text else 0.0
    semantic_points = round(semantic_ratio * 12)
    project_points = project_keyword_points + semantic_points

    categories = [
        _category(
            "required_skills", "Required skills", required_points, 40,
            "Normalized exact and alias-aware matching against resume skills and resume text.",
            f"Matched {len(matched_required)} of {len(required)} required skills.",
        ),
        _category(
            "preferred_skills", "Preferred skills", preferred_points, 15,
            "Normalized exact and alias-aware matching; no penalty when none are listed.",
            f"Matched {len(matched_preferred)} of {len(preferred)} preferred skills.",
        ),
        _category(
            "experience", "Experience alignment", experience_points, 15,
            "Numeric experience coverage (10) plus relevant keyword evidence (5).",
            experience_explanation,
        ),
        _category(
            "education", "Education alignment", education_points, 10,
            "Degree and field-term matching against the parsed education section.",
            education_explanation,
        ),
        _category(
            "projects", "Project relevance", project_points, 20,
            "Keyword overlap (8) plus embedding-based semantic relatedness (12).",
            f"Project evidence matched {project_hits} job terms; semantic similarity was {semantic_similarity:.2f}.",
        ),
    ]
    return categories, matched_skills, missing_required, missing_preferred, required_percent, preferred_percent
