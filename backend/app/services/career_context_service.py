import hashlib
import json
import math
import re
from dataclasses import dataclass
from typing import Any, Literal

from sqlalchemy import Float, Text, bindparam, case, cast, func, select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session, selectinload
from sqlalchemy.types import UserDefinedType

from app.core.config import settings
from app.models.career_chunk import CareerChunk
from app.models.career_document import CareerDocument
from app.models.job_match import JobMatch
from app.models.resume import Resume
from app.models.user import User
from app.services.ai_client import AIClient
from app.services.resume_analysis_service import latest_analysis

SourceType = Literal["profile", "resume", "resume_analysis", "job_match"]
EMBEDDING_BATCH_SIZE = 16
RESUME_SECTIONS = (
    ("technical_skills", "Technical skills"),
    ("projects", "Projects"),
    ("education", "Education"),
    ("experience", "Experience"),
    ("certifications", "Certifications"),
    ("achievements", "Achievements"),
)


class ContextIndexError(Exception):
    pass


@dataclass(frozen=True)
class PreparedDocument:
    source_type: SourceType
    source_record_id: int | None
    source_key: str
    title: str
    content: str
    source_attributes: dict[str, Any]


@dataclass(frozen=True)
class RetrievedContext:
    context_id: str
    label: str
    source_type: SourceType
    source_record_id: int | None
    content: str
    similarity: float

    def source_reference(self) -> dict[str, Any]:
        return {
            "context_id": self.context_id,
            "label": self.label,
            "source_type": self.source_type,
            "source_record_id": self.source_record_id,
        }


def _list_values(data: dict[str, Any], key: str) -> list[str]:
    value = data.get(key, [])
    if not isinstance(value, list):
        return []
    return [str(item).strip() for item in value if str(item).strip()]


def _bullets(values: list[str]) -> str:
    return "\n".join(f"- {value}" for value in values)


def _add_document(
    documents: list[PreparedDocument],
    *,
    source_type: SourceType,
    source_record_id: int | None,
    source_key: str,
    title: str,
    content: str,
    source_attributes: dict[str, Any] | None = None,
) -> None:
    cleaned = content.strip()
    if not cleaned:
        return
    documents.append(
        PreparedDocument(
            source_type=source_type,
            source_record_id=source_record_id,
            source_key=source_key,
            title=title,
            content=cleaned,
            source_attributes=source_attributes or {},
        )
    )


def _resume_documents(resume: Resume) -> list[PreparedDocument]:
    documents: list[PreparedDocument] = []
    data = resume.structured_data or {}
    for key, label in RESUME_SECTIONS:
        values = _list_values(data, key)
        if values:
            _add_document(
                documents,
                source_type="resume",
                source_record_id=resume.id,
                source_key=f"resume:{resume.id}:{key}",
                title=f"Resume · {label}",
                content=f"{label}\n{_bullets(values)}",
                source_attributes={"section": key},
            )

    if resume.parsed_text.strip():
        _add_document(
            documents,
            source_type="resume",
            source_record_id=resume.id,
            source_key=f"resume:{resume.id}:text",
            title="Resume · Full text",
            content=resume.parsed_text,
            source_attributes={"section": "full_text"},
        )
    return documents


def prepare_user_documents(database: Session, user: User) -> list[PreparedDocument]:
    documents: list[PreparedDocument] = []
    profile_lines = []
    if user.target_role:
        profile_lines.append(f"Target role: {user.target_role}")
    if user.experience_level:
        profile_lines.append(f"Experience level: {user.experience_level}")
    if profile_lines:
        _add_document(
            documents,
            source_type="profile",
            source_record_id=user.id,
            source_key="profile",
            title="Profile · Career goal",
            content="\n".join(profile_lines),
        )

    resume = database.scalar(select(Resume).where(Resume.user_id == user.id))
    if resume:
        documents.extend(_resume_documents(resume))
        analysis = latest_analysis(database, resume)
        if analysis:
            analysis_content = {
                "overall_score": analysis.overall_score,
                "category_scores": analysis.category_scores,
                **(analysis.analysis_result or {}),
            }
            _add_document(
                documents,
                source_type="resume_analysis",
                source_record_id=analysis.id,
                source_key=f"resume-analysis:{analysis.id}",
                title="Resume analysis · Latest feedback",
                content=json.dumps(analysis_content, ensure_ascii=False, indent=2),
                source_attributes={"resume_id": resume.id},
            )

    job_matches = database.scalars(
        select(JobMatch)
        .where(JobMatch.user_id == user.id)
        .order_by(JobMatch.created_at.desc(), JobMatch.id.desc())
    ).all()
    for match in job_matches:
        title = match.job_title or "Saved job"
        match_content = {
            "job_title": match.job_title,
            "job_description": match.job_description,
            "parsed_requirements": match.parsed_job_requirements,
            "match_result": match.match_result,
        }
        _add_document(
            documents,
            source_type="job_match",
            source_record_id=match.id,
            source_key=f"job-match:{match.id}",
            title=f"Job match · {title}",
            content=json.dumps(match_content, ensure_ascii=False, indent=2),
        )
    return documents


def _word_boundary(value: str, preferred_end: int, minimum_end: int) -> int:
    boundary = value.rfind(" ", minimum_end, preferred_end)
    return boundary if boundary > minimum_end else preferred_end


def chunk_text(text: str, chunk_size: int | None = None, overlap: int | None = None) -> list[str]:
    size = chunk_size or settings.rag_chunk_size
    shared = settings.rag_chunk_overlap if overlap is None else overlap
    if size < 100 or shared < 0 or shared >= size:
        raise ValueError("RAG chunk settings are invalid")

    normalized = re.sub(r"[ \t]+", " ", text.replace("\r\n", "\n").replace("\r", "\n"))
    normalized = re.sub(r"\n{3,}", "\n\n", normalized).strip()
    if not normalized:
        return []

    chunks: list[str] = []
    start = 0
    while start < len(normalized):
        proposed_end = min(len(normalized), start + size)
        end = proposed_end
        if proposed_end < len(normalized):
            paragraph_end = normalized.rfind("\n\n", start + size // 2, proposed_end)
            if paragraph_end > start:
                end = paragraph_end
            else:
                end = _word_boundary(normalized, proposed_end, start + size // 2)

        chunk = normalized[start:end].strip()
        if chunk and (not chunks or chunk != chunks[-1]):
            chunks.append(chunk)
        if end >= len(normalized):
            break
        start = max(start + 1, end - shared)
        while start < end and normalized[start].isspace():
            start += 1
    return chunks


def _fingerprint(document: PreparedDocument) -> str:
    payload = {
        "title": document.title,
        "content": document.content,
        "attributes": document.source_attributes,
        "embedding_model": settings.gemini_embedding_model,
        "embedding_dimensions": settings.rag_embedding_dimensions,
        "chunk_size": settings.rag_chunk_size,
        "chunk_overlap": settings.rag_chunk_overlap,
    }
    return hashlib.sha256(json.dumps(payload, sort_keys=True, ensure_ascii=False).encode("utf-8")).hexdigest()


def _embedding_batches(client: AIClient, inputs: list[str]) -> list[list[float]]:
    vectors: list[list[float]] = []
    for start in range(0, len(inputs), EMBEDDING_BATCH_SIZE):
        vectors.extend(
            client.embed(
                model=settings.gemini_embedding_model,
                inputs=inputs[start : start + EMBEDDING_BATCH_SIZE],
            )
        )
    for vector in vectors:
        if len(vector) != settings.rag_embedding_dimensions:
            raise ContextIndexError(
                f"Embedding model returned {len(vector)} dimensions; expected {settings.rag_embedding_dimensions}."
            )
        if not all(isinstance(value, (int, float)) and math.isfinite(value) for value in vector):
            raise ContextIndexError("Embedding model returned an invalid vector.")
    return vectors


def sync_user_documents(database: Session, user: User, client: AIClient) -> None:
    prepared = prepare_user_documents(database, user)
    existing = database.scalars(
        select(CareerDocument).options(selectinload(CareerDocument.chunks)).where(CareerDocument.user_id == user.id)
    ).all()
    existing_by_key = {document.source_key: document for document in existing}

    replacements: list[tuple[PreparedDocument, str, list[str], list[list[float]]]] = []
    for document in prepared:
        fingerprint = _fingerprint(document)
        stored = existing_by_key.get(document.source_key)
        current_chunks = stored.chunks if stored else []
        is_current = (
            stored is not None
            and stored.content_fingerprint == fingerprint
            and bool(current_chunks)
            and all(chunk.embedding_model == settings.gemini_embedding_model for chunk in current_chunks)
        )
        if is_current:
            continue

        chunks = chunk_text(document.content)
        if not chunks:
            continue
        embedding_inputs = [f"{document.title}\n{chunk}" for chunk in chunks]
        replacements.append((document, fingerprint, chunks, _embedding_batches(client, embedding_inputs)))

    expected_keys = {document.source_key for document in prepared}
    try:
        for stored in existing:
            if stored.source_key not in expected_keys:
                database.delete(stored)

        for prepared_document, fingerprint, chunks, vectors in replacements:
            stored = existing_by_key.get(prepared_document.source_key)
            if stored is None:
                stored = CareerDocument(user_id=user.id, source_key=prepared_document.source_key)
                database.add(stored)
            else:
                stored.chunks.clear()
                database.flush()

            stored.source_type = prepared_document.source_type
            stored.source_record_id = prepared_document.source_record_id
            stored.title = prepared_document.title
            stored.content = prepared_document.content
            stored.content_fingerprint = fingerprint
            stored.source_attributes = prepared_document.source_attributes
            for index, (content, vector) in enumerate(zip(chunks, vectors, strict=True)):
                stored.chunks.append(
                    CareerChunk(
                        user_id=user.id,
                        chunk_index=index,
                        content=content,
                        embedding=vector,
                        embedding_model=settings.gemini_embedding_model,
                    )
                )
        if replacements or any(document.source_key not in expected_keys for document in existing):
            database.commit()
    except Exception:
        database.rollback()
        raise


def _cosine_similarity(first: list[float], second: list[float]) -> float:
    if len(first) != len(second) or not first:
        return -1.0
    denominator = math.sqrt(sum(value * value for value in first)) * math.sqrt(
        sum(value * value for value in second)
    )
    if denominator == 0:
        return -1.0
    similarity = sum(a * b for a, b in zip(first, second, strict=True)) / denominator
    return max(-1.0, min(1.0, similarity))


class _Vector(UserDefinedType):
    cache_ok = True

    def get_col_spec(self, **kw):
        return "vector"


def _context_query(user_id):
    # Both owners must match, even if a chunk has inconsistent document metadata.
    return select(CareerChunk, CareerDocument).join(
        CareerDocument, CareerDocument.id == CareerChunk.document_id,
    ).where(
        CareerChunk.user_id == user_id,
        CareerDocument.user_id == user_id,
        CareerChunk.embedding_model == settings.gemini_embedding_model,
    )


def _pgvector_query(user_id, query_vector):
    vector = cast(cast(CareerChunk.embedding, Text), _Vector())
    question = cast(bindparam("query_vector", json.dumps(query_vector)), _Vector())
    distance = vector.op("<=>", return_type=Float)(question)
    similarity = case(
        (func.json_array_length(CareerChunk.embedding) == len(query_vector), 1.0 - distance),
        else_=-1.0,
    ).label("similarity")
    return _context_query(user_id).add_columns(similarity).order_by(similarity.desc(), CareerChunk.id)


def retrieve_context(
    database: Session,
    user_id: int,
    query: str,
    client: AIClient,
) -> list[RetrievedContext]:
    query_vector = _embedding_batches(client, [query])[0]
    if settings.rag_vector_backend == "pgvector":
        try:
            rows = database.execute(_pgvector_query(user_id, query_vector)).all()
        except SQLAlchemyError:
            raise ContextIndexError("Vector retrieval is unavailable. Check the PostgreSQL vector extension.") from None
        ranked = [(similarity, chunk, document) for chunk, document, similarity in rows]
    else:
        rows = database.execute(_context_query(user_id).order_by(CareerChunk.id)).all()
        ranked = sorted(
            (
                (_cosine_similarity(query_vector, [float(value) for value in chunk.embedding]), chunk, document)
                for chunk, document in rows
            ),
            key=lambda item: item[0],
            reverse=True,
        )

    selected: list[RetrievedContext] = []
    per_document: dict[int, int] = {}
    used_characters = 0
    for similarity, chunk, document in ranked:
        if not math.isfinite(similarity) or similarity < settings.rag_min_similarity:
            continue
        if per_document.get(document.id, 0) >= 2:
            continue
        if used_characters + len(chunk.content) > settings.rag_max_context_characters:
            continue
        selected.append(
            RetrievedContext(
                context_id=f"C{len(selected) + 1}",
                label=document.title,
                source_type=document.source_type,
                source_record_id=document.source_record_id,
                content=chunk.content,
                similarity=similarity,
            )
        )
        used_characters += len(chunk.content)
        per_document[document.id] = per_document.get(document.id, 0) + 1
        if len(selected) >= settings.rag_top_k:
            break
    return selected
