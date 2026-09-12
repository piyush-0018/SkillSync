import re
from datetime import datetime, timezone
from typing import Any

from pydantic import ValidationError
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.core.config import settings
from app.models.interview_question import InterviewQuestion
from app.models.interview_session import InterviewSession
from app.models.user import User
from app.prompts.mock_interview import (
    SYSTEM_PROMPT,
    build_answer_evaluation_prompt,
    build_final_feedback_prompt,
    build_question_prompt,
)
from app.schemas.interview import (
    AnswerEvaluationLLMOutput,
    FinalInterviewLLMOutput,
    InterviewAnswerResponse,
    InterviewQuestionLLMOutput,
    InterviewQuestionResponse,
    InterviewSessionDetail,
    InterviewSessionSummary,
    QuestionEvaluation,
    RubricScore,
)
from app.services.ai_client import (
    AIClient,
    AIConfigurationError,
    AIConnectionError,
    AIError,
    AIModelNotFoundError,
    create_ai_client,
)
from app.services.resume_service import get_user_resume

PROVIDER = "gemini"
RUBRIC_FIELDS = (
    ("accuracy", "Accuracy"),
    ("relevance", "Relevance"),
    ("clarity", "Clarity"),
    ("completeness", "Completeness"),
    ("communication", "Communication"),
)


class InterviewConfigurationError(Exception):
    pass


class InterviewGenerationError(Exception):
    pass


class InterviewStateError(Exception):
    pass


def _client() -> AIClient:
    try:
        return create_ai_client(settings)
    except AIConfigurationError as exc:
        raise InterviewConfigurationError(str(exc)) from exc


def _candidate_context(database: Session, user: User) -> dict[str, Any]:
    context: dict[str, Any] = {
        "target_role": user.target_role,
        "experience_level": user.experience_level,
    }
    resume = get_user_resume(database, user.id)
    if resume and resume.parsing_status == "parsed":
        data = resume.structured_data or {}
        context["resume"] = {
            "technical_skills": data.get("technical_skills", []),
            "projects": data.get("projects", []),
            "experience": data.get("experience", []),
            "education": data.get("education", []),
            "certifications": data.get("certifications", []),
        }
    return context


def _normalize_question(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", value.lower()).strip()


def _ensure_new_question(question: str, previous_questions: list[str]) -> None:
    normalized = _normalize_question(question)
    if normalized in {_normalize_question(item) for item in previous_questions}:
        raise InterviewGenerationError("The interview generated a repeated question. Please retry.")


def _translate_ai_error(exc: Exception) -> Exception:
    if isinstance(exc, AIConnectionError):
        return InterviewConfigurationError("Gemini is currently unreachable. Please retry shortly.")
    if isinstance(exc, AIModelNotFoundError):
        return InterviewConfigurationError(f'Gemini model "{exc.model}" is unavailable.')
    return InterviewGenerationError("The AI provider could not complete this interview step. Please retry.")


def _generate_question(
    database: Session,
    user: User,
    *,
    target_role: str,
    difficulty: str,
    interview_type: str,
    previous_questions: list[str],
) -> InterviewQuestionLLMOutput:
    try:
        output = _client().chat_structured(
            model=settings.gemini_model,
            system_prompt=SYSTEM_PROMPT,
            prompt=build_question_prompt(
                target_role=target_role,
                difficulty=difficulty,
                interview_type=interview_type,
                candidate_context=_candidate_context(database, user),
                previous_questions=previous_questions,
            ),
            response_model=InterviewQuestionLLMOutput,
        )
        _ensure_new_question(output.question, previous_questions)
        return output
    except (AIError, ValidationError, TypeError, ValueError) as exc:
        raise _translate_ai_error(exc) from exc


def _build_evaluation(output: AnswerEvaluationLLMOutput) -> QuestionEvaluation:
    rubric_scores = []
    for key, label in RUBRIC_FIELDS:
        assessment = getattr(output, key)
        rubric_scores.append(
            RubricScore(
                key=key,
                label=label,
                rating=assessment.rating,
                score=assessment.rating * 5,
                feedback=assessment.feedback,
            )
        )
    return QuestionEvaluation(
        overall_score=sum(item.score for item in rubric_scores),
        rubric_scores=rubric_scores,
        strengths=output.strengths,
        improvements=output.improvements,
        coaching_feedback=output.coaching_feedback,
    )


def _question_response(question: InterviewQuestion) -> InterviewQuestionResponse:
    return InterviewQuestionResponse(
        id=question.id,
        sequence_number=question.sequence_number,
        question_text=question.question_text,
        focus_area=question.focus_area,
        answer_text=question.answer_text,
        evaluation=QuestionEvaluation.model_validate(question.evaluation) if question.evaluation else None,
        score=question.score,
        asked_at=question.asked_at,
        answered_at=question.answered_at,
    )


def _summary(session: InterviewSession) -> InterviewSessionSummary:
    return InterviewSessionSummary(
        id=session.id,
        target_role=session.target_role,
        difficulty=session.difficulty,
        interview_type=session.interview_type,
        response_mode=session.response_mode,
        status=session.status,
        question_limit=session.question_limit,
        answered_count=sum(question.answer_text is not None for question in session.questions),
        overall_score=session.overall_score,
        started_at=session.started_at,
        completed_at=session.completed_at,
    )


def _detail(session: InterviewSession) -> InterviewSessionDetail:
    summary = _summary(session)
    return InterviewSessionDetail(
        **summary.model_dump(),
        questions=[_question_response(question) for question in session.questions],
        final_feedback=session.final_feedback,
        provider=session.provider,
        model=session.model_name,
    )


def _session_query(user_id: int, session_id: int):
    return (
        select(InterviewSession)
        .options(selectinload(InterviewSession.questions))
        .where(InterviewSession.id == session_id, InterviewSession.user_id == user_id)
    )


def start_interview(
    database: Session,
    user: User,
    *,
    target_role: str,
    difficulty: str,
    interview_type: str,
    response_mode: str,
) -> InterviewSessionDetail:
    generated = _generate_question(
        database,
        user,
        target_role=target_role,
        difficulty=difficulty,
        interview_type=interview_type,
        previous_questions=[],
    )
    session = InterviewSession(
        user_id=user.id,
        target_role=target_role,
        difficulty=difficulty,
        interview_type=interview_type,
        response_mode=response_mode,
        status="active",
        question_limit=settings.interview_question_limit,
        provider=PROVIDER,
        model_name=settings.gemini_model,
    )
    session.questions.append(
        InterviewQuestion(sequence_number=1, question_text=generated.question, focus_area=generated.focus_area)
    )
    database.add(session)
    try:
        database.commit()
        database.refresh(session)
    except Exception:
        database.rollback()
        raise
    return _detail(session)


def get_interview(database: Session, user_id: int, session_id: int) -> InterviewSessionDetail | None:
    session = database.scalar(_session_query(user_id, session_id))
    return _detail(session) if session else None


def list_interviews(database: Session, user_id: int, limit: int) -> list[InterviewSessionSummary]:
    sessions = database.scalars(
        select(InterviewSession)
        .options(selectinload(InterviewSession.questions))
        .where(InterviewSession.user_id == user_id)
        .order_by(InterviewSession.created_at.desc(), InterviewSession.id.desc())
        .limit(limit)
    ).all()
    return [_summary(session) for session in sessions]


def submit_answer(
    database: Session,
    user: User,
    session_id: int,
    answer: str,
) -> InterviewAnswerResponse | None:
    session = database.scalar(_session_query(user.id, session_id))
    if not session:
        return None
    if session.status != "active":
        raise InterviewStateError("This interview is already complete.")

    current = next((question for question in session.questions if question.answer_text is None), None)
    if not current:
        raise InterviewStateError("All generated questions have been answered. Finish the interview to view results.")

    previous_questions = [question.question_text for question in session.questions]
    needs_next = current.sequence_number < session.question_limit
    try:
        output = _client().chat_structured(
            model=settings.gemini_model,
            system_prompt=SYSTEM_PROMPT,
            prompt=build_answer_evaluation_prompt(
                target_role=session.target_role,
                difficulty=session.difficulty,
                interview_type=session.interview_type,
                candidate_context=_candidate_context(database, user),
                question=current.question_text,
                answer=answer,
                previous_questions=previous_questions,
                include_next_question=needs_next,
            ),
            response_model=AnswerEvaluationLLMOutput,
        )
        next_question = output.next_question if needs_next else None
        if needs_next and next_question is None:
            next_question = _generate_question(
                database,
                user,
                target_role=session.target_role,
                difficulty=session.difficulty,
                interview_type=session.interview_type,
                previous_questions=previous_questions,
            )
        if next_question:
            _ensure_new_question(next_question.question, previous_questions)
        evaluation = _build_evaluation(output)
    except InterviewGenerationError:
        raise
    except (AIError, ValidationError, TypeError, ValueError) as exc:
        raise _translate_ai_error(exc) from exc

    current.answer_text = answer
    current.evaluation = evaluation.model_dump()
    current.score = evaluation.overall_score
    current.answered_at = datetime.now(timezone.utc)
    next_record = None
    if next_question:
        next_record = InterviewQuestion(
            sequence_number=current.sequence_number + 1,
            question_text=next_question.question,
            focus_area=next_question.focus_area,
        )
        session.questions.append(next_record)
    try:
        database.commit()
        database.refresh(session)
    except Exception:
        database.rollback()
        raise

    return InterviewAnswerResponse(
        session=_detail(session),
        evaluated_question=_question_response(current),
        next_question=_question_response(next_record) if next_record else None,
    )


def finish_interview(database: Session, user: User, session_id: int) -> InterviewSessionDetail | None:
    session = database.scalar(_session_query(user.id, session_id))
    if not session:
        return None
    if session.status == "completed":
        return _detail(session)

    answered = [question for question in session.questions if question.answer_text is not None]
    if not answered:
        raise InterviewStateError("Answer at least one question before finishing the interview.")
    overall_score = round(sum(question.score or 0 for question in answered) / len(answered))
    question_results = [
        {
            "question": question.question_text,
            "answer": question.answer_text,
            "score": question.score,
            "evaluation": question.evaluation,
        }
        for question in answered
    ]
    try:
        feedback = _client().chat_structured(
            model=settings.gemini_model,
            system_prompt=SYSTEM_PROMPT,
            prompt=build_final_feedback_prompt(
                target_role=session.target_role,
                difficulty=session.difficulty,
                interview_type=session.interview_type,
                overall_score=overall_score,
                question_results=question_results,
            ),
            response_model=FinalInterviewLLMOutput,
        )
    except (AIError, ValidationError, TypeError, ValueError) as exc:
        raise _translate_ai_error(exc) from exc

    session.status = "completed"
    session.overall_score = overall_score
    session.final_feedback = feedback.model_dump()
    session.completed_at = datetime.now(timezone.utc)
    try:
        database.commit()
        database.refresh(session)
    except Exception:
        database.rollback()
        raise
    return _detail(session)
