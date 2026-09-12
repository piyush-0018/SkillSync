import logging
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from uuid import uuid4

import pymupdf
from fastapi import UploadFile, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.career_document import CareerDocument
from app.models.resume import Resume

logger = logging.getLogger(__name__)
CHUNK_SIZE = 1024 * 1024
ALLOWED_CONTENT_TYPES = {"application/pdf", "application/x-pdf"}
MAX_EXTRACTED_CHARACTERS = 500_000

SECTION_ALIASES = {
    "education": {"education", "academic background", "academic qualifications", "qualifications"},
    "technical_skills": {"skills", "technical skills", "technical expertise", "core competencies", "technologies"},
    "projects": {"projects", "academic projects", "personal projects", "project experience"},
    "experience": {"experience", "work experience", "professional experience", "employment", "internships"},
    "certifications": {"certifications", "certificates", "courses and certifications", "licenses and certifications"},
    "achievements": {"achievements", "awards", "honors", "honours", "awards and achievements"},
}


class ResumeUploadError(Exception):
    def __init__(self, detail: str, status_code: int = status.HTTP_422_UNPROCESSABLE_CONTENT):
        self.detail = detail
        self.status_code = status_code
        super().__init__(detail)


def _storage_root() -> Path:
    root = settings.resume_storage_dir.resolve()
    root.mkdir(parents=True, exist_ok=True)
    return root


def _safe_original_filename(filename: str | None) -> str:
    display_name = (filename or "resume.pdf").replace("\\", "/").rsplit("/", 1)[-1]
    display_name = re.sub(r"[\x00-\x1f\x7f]", "", display_name).strip()
    return (display_name or "resume.pdf")[:255]


def _stored_path(filename: str) -> Path:
    root = _storage_root()
    path = (root / filename).resolve()
    if path.parent != root:
        raise RuntimeError("Invalid stored resume filename")
    return path


def _remove_file(path: Path) -> None:
    try:
        path.unlink(missing_ok=True)
    except OSError:
        logger.warning("Could not remove stored resume file %s", path.name, exc_info=True)


def _heading_key(line: str) -> str | None:
    normalized = re.sub(r"[^a-z0-9+ ]", "", line.lower()).strip()
    for section, aliases in SECTION_ALIASES.items():
        if normalized in aliases:
            return section
    return None


def _extract_name(lines: list[str]) -> str | None:
    excluded = {alias for aliases in SECTION_ALIASES.values() for alias in aliases}
    excluded.update({"resume", "curriculum vitae", "cv"})
    for line in lines[:12]:
        candidate = line.strip(" |•-\t")
        normalized = candidate.lower().strip(":")
        if not candidate or normalized in excluded or "@" in candidate or len(candidate) > 80:
            continue
        words = candidate.split()
        if 2 <= len(words) <= 5 and all(re.fullmatch(r"[A-Za-z][A-Za-z.'-]*", word) for word in words):
            return candidate
    return None


def _first_match(pattern: str, text: str, flags: int = 0) -> str | None:
    match = re.search(pattern, text, flags)
    return match.group(0).strip() if match else None


def _clean_section_lines(lines: list[str]) -> list[str]:
    cleaned = []
    for line in lines:
        value = re.sub(r"^[•●▪◦*\-–—]+\s*", "", line).strip()
        if value and value not in cleaned:
            cleaned.append(value)
    return cleaned[:40]


def parse_resume_text(text: str) -> dict[str, Any]:
    lines = [re.sub(r"\s+", " ", line).strip() for line in text.splitlines()]
    lines = [line for line in lines if line]
    sections: dict[str, list[str]] = {key: [] for key in SECTION_ALIASES}
    active_section = None

    for line in lines:
        heading = _heading_key(line)
        if heading:
            active_section = heading
            continue
        if active_section:
            sections[active_section].append(line)

    email = _first_match(r"[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}", text, re.IGNORECASE)
    linkedin = _first_match(r"(?:https?://)?(?:www\.)?linkedin\.com/in/[A-Za-z0-9._%-]+/?", text, re.IGNORECASE)
    github = _first_match(r"(?:https?://)?(?:www\.)?github\.com/[A-Za-z0-9._-]+/?", text, re.IGNORECASE)
    phone_candidates = re.findall(r"(?:\+\d{1,3}[\s.-]?)?(?:\(?\d{2,5}\)?[\s.-]?)?\d{3,5}[\s.-]\d{4,6}", text)
    phone = next((value.strip() for value in phone_candidates if 10 <= len(re.sub(r"\D", "", value)) <= 15), None)

    skill_lines = _clean_section_lines(sections["technical_skills"])
    skills = []
    for line in skill_lines:
        for skill in re.split(r"[,|•]", line):
            cleaned = re.sub(r"^[A-Za-z ]{2,20}:\s*", "", skill).strip(" .-")
            if cleaned and len(cleaned) <= 80 and cleaned not in skills:
                skills.append(cleaned)

    return {
        "name": _extract_name(lines),
        "contact": {"email": email, "phone": phone, "linkedin": linkedin, "github": github},
        "education": _clean_section_lines(sections["education"]),
        "technical_skills": skills[:40],
        "projects": _clean_section_lines(sections["projects"]),
        "experience": _clean_section_lines(sections["experience"]),
        "certifications": _clean_section_lines(sections["certifications"]),
        "achievements": _clean_section_lines(sections["achievements"]),
    }


def _extract_pdf(path: Path) -> tuple[str, dict[str, Any], str, str | None]:
    try:
        document = pymupdf.open(path)
    except (pymupdf.FileDataError, RuntimeError) as exc:
        raise ResumeUploadError("The uploaded file is not a readable PDF") from exc

    try:
        if not document.is_pdf:
            raise ResumeUploadError("The uploaded file is not a valid PDF")
        if document.needs_pass:
            raise ResumeUploadError("Password-protected PDFs are not supported")
        if document.page_count == 0:
            raise ResumeUploadError("The PDF does not contain any pages")
        if document.page_count > settings.max_resume_pages:
            raise ResumeUploadError(f"The PDF cannot contain more than {settings.max_resume_pages} pages")

        try:
            parts = []
            remaining = MAX_EXTRACTED_CHARACTERS
            for page in document:
                page_text = page.get_text("text", sort=True)
                parts.append(page_text[:remaining])
                remaining -= len(parts[-1]) + 2
                if remaining <= 0:
                    break
            text = "\n\n".join(parts)
        except RuntimeError:
            return "", parse_resume_text(""), "failed", "Text extraction failed. Try exporting the resume as a new PDF."
    finally:
        document.close()

    text = text[:MAX_EXTRACTED_CHARACTERS].strip()
    if not text:
        return "", parse_resume_text(""), "failed", "No readable text was found. Upload a text-based PDF rather than a scanned image."
    return text, parse_resume_text(text), "parsed", None


def get_user_resume(database: Session, user_id: int) -> Resume | None:
    return database.scalar(select(Resume).where(Resume.user_id == user_id))


def _discard_resume_context(database: Session, user_id: int) -> None:
    # Remove derived copies in the same transaction as the source change.
    documents = database.scalars(select(CareerDocument).where(
        CareerDocument.user_id == user_id,
        CareerDocument.source_type.in_(["resume", "resume_analysis"]),
    ))
    for document in documents:
        database.delete(document)


def save_resume(database: Session, user_id: int, upload: UploadFile) -> Resume:
    original_filename = _safe_original_filename(upload.filename)
    if Path(original_filename).suffix.lower() != ".pdf":
        raise ResumeUploadError("Only PDF files are allowed", status.HTTP_400_BAD_REQUEST)

    content_type = (upload.content_type or "").lower().split(";", 1)[0]
    if content_type not in ALLOWED_CONTENT_TYPES:
        raise ResumeUploadError("The selected file must have a PDF content type", status.HTTP_400_BAD_REQUEST)

    root = _storage_root()
    temporary_path = root / f".{uuid4().hex}.upload"
    file_size = 0
    max_bytes = settings.max_resume_size_mb * 1024 * 1024

    try:
        with temporary_path.open("xb") as destination:
            while chunk := upload.file.read(CHUNK_SIZE):
                file_size += len(chunk)
                if file_size > max_bytes:
                    raise ResumeUploadError(
                        f"Resume must be {settings.max_resume_size_mb} MB or smaller",
                        status.HTTP_413_CONTENT_TOO_LARGE,
                    )
                destination.write(chunk)
    except Exception:
        _remove_file(temporary_path)
        raise
    finally:
        upload.file.close()

    final_path = None
    committed = False
    try:
        if file_size == 0:
            raise ResumeUploadError("The selected file is empty", status.HTTP_400_BAD_REQUEST)
        with temporary_path.open("rb") as source:
            if source.read(5) != b"%PDF-":
                raise ResumeUploadError("The uploaded file does not contain a valid PDF signature")

        parsed_text, structured_data, parsing_status, parsing_error = _extract_pdf(temporary_path)
        stored_filename = f"{uuid4().hex}.pdf"
        final_path = _stored_path(stored_filename)
        temporary_path.replace(final_path)

        existing_resume = get_user_resume(database, user_id)
        old_filename = existing_resume.stored_filename if existing_resume else None
        resume = existing_resume or Resume(user_id=user_id)
        resume.original_filename = original_filename
        resume.stored_filename = stored_filename
        resume.file_size = file_size
        resume.uploaded_at = datetime.now(timezone.utc)
        resume.parsed_text = parsed_text
        resume.structured_data = structured_data
        resume.parsing_status = parsing_status
        resume.parsing_error = parsing_error
        database.add(resume)
        _discard_resume_context(database, user_id)

        database.commit()
        committed = True

        if old_filename and old_filename != stored_filename:
            _remove_file(_stored_path(old_filename))
        return resume
    except Exception:
        if not committed:
            database.rollback()
            if final_path is not None:
                _remove_file(final_path)
        _remove_file(temporary_path)
        raise


def delete_user_resume(database: Session, resume: Resume) -> None:
    stored_path = _stored_path(resume.stored_filename)
    _discard_resume_context(database, resume.user_id)
    database.delete(resume)
    try:
        database.commit()
    except Exception:
        database.rollback()
        raise
    _remove_file(stored_path)
