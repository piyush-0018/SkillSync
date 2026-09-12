import { AnimatePresence, motion } from 'framer-motion'
import { AlertCircle, ArrowLeft, ArrowRight, LoaderCircle, MessageSquareText, RefreshCw } from 'lucide-react'
import { useCallback, useEffect, useMemo, useRef, useState } from 'react'
import { Link, useNavigate, useParams } from 'react-router-dom'
import QuestionFeedback from '../components/interviews/QuestionFeedback'
import VideoInterviewAnswer from '../components/interviews/VideoInterviewAnswer'
import { getApiErrorMessage } from '../services/api'
import { finishInterview, getInterview, submitInterviewAnswer } from '../services/interviewService'

function readable(value) {
  return value.replace('_', ' ').replace(/\b\w/g, (letter) => letter.toUpperCase())
}

function TextAnswerForm({ question, answer, isSubmitting, onAnswerChange, onSubmit, answerRef }) {
  return (
    <motion.form
      key={question.id}
      onSubmit={onSubmit}
      initial={{ opacity: 0, x: 8 }}
      animate={{ opacity: 1, x: 0 }}
      exit={{ opacity: 0, x: -8 }}
      className="mt-7 rounded-3xl border bg-[#fdfdff] p-5 shadow-[0_22px_55px_-42px_rgba(15,23,42,.7)] dark:bg-slate-900 sm:p-8"
    >
      <div className="flex items-center justify-between gap-4">
        <span className="rounded-full bg-indigo-50 px-3 py-1 text-xs font-semibold text-indigo-700 dark:bg-indigo-950 dark:text-indigo-300">{question.focus_area}</span>
        <span className="text-xs text-slate-400">Question {question.sequence_number}</span>
      </div>
      <h2 className="mt-6 text-xl font-semibold leading-8 tracking-[-0.02em] sm:text-2xl">{question.question_text}</h2>
      <label htmlFor="interview-answer" className="mt-8 block text-sm font-semibold">Your answer</label>
      <textarea
        ref={answerRef}
        id="interview-answer"
        value={answer}
        onChange={onAnswerChange}
        disabled={isSubmitting}
        placeholder="Structure your response clearly. Explain your reasoning and use a concrete example where it helps…"
        className="mt-2 min-h-56 w-full resize-y rounded-xl border bg-[#fafaff] p-4 text-sm leading-6 outline-none transition placeholder:text-slate-400 focus:border-indigo-500 focus:ring-2 focus:ring-indigo-500/15 disabled:cursor-wait disabled:opacity-70 dark:bg-slate-950"
      />
      <div className="mt-3 flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
        <p className="text-xs text-slate-500">Evaluated on accuracy, relevance, clarity, completeness, and communication.</p>
        <button disabled={answer.trim().length < 2 || isSubmitting} className="button-primary min-w-40 gap-2 disabled:cursor-not-allowed disabled:opacity-50">
          {isSubmitting ? <><LoaderCircle size={16} className="animate-spin" />Evaluating…</> : 'Submit answer'}
        </button>
      </div>
      {isSubmitting && <p role="status" className="mt-4 rounded-lg bg-indigo-50 px-3 py-2 text-xs text-indigo-700 dark:bg-indigo-950/40 dark:text-indigo-300">Gemini is reviewing your answer and preparing a follow-up. This may take a moment.</p>}
    </motion.form>
  )
}

export default function InterviewSessionPage() {
  const { sessionId } = useParams()
  const navigate = useNavigate()
  const answerRef = useRef(null)
  const [session, setSession] = useState(null)
  const [answer, setAnswer] = useState('')
  const [reviewedQuestion, setReviewedQuestion] = useState(null)
  const [isLoading, setIsLoading] = useState(true)
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [isFinishing, setIsFinishing] = useState(false)
  const [error, setError] = useState('')
  const [retryAction, setRetryAction] = useState('load')

  const loadSession = useCallback(async () => {
    setIsLoading(true)
    setError('')
    setRetryAction('load')
    try {
      const result = await getInterview(sessionId)
      if (result.status === 'completed') {
        navigate(`/interviews/${sessionId}/results`, { replace: true })
        return
      }
      setSession(result)
    } catch (requestError) {
      setError(getApiErrorMessage(requestError, 'Could not load this interview.'))
    } finally {
      setIsLoading(false)
    }
  }, [navigate, sessionId])

  useEffect(() => { loadSession() }, [loadSession])

  const currentQuestion = useMemo(
    () => session?.questions.find((question) => question.answer_text == null),
    [session],
  )
  const answeredCount = session?.answered_count || 0
  const progressStep = reviewedQuestion?.sequence_number || currentQuestion?.sequence_number || answeredCount
  const progress = session ? Math.min(100, (progressStep / session.question_limit) * 100) : 0

  async function submitAnswer(answerText) {
    if (!currentQuestion || answerText.trim().length < 2) return
    setIsSubmitting(true)
    setError('')
    setRetryAction('answer')
    try {
      const result = await submitInterviewAnswer(sessionId, answerText.trim())
      setSession(result.session)
      setReviewedQuestion(result.evaluated_question)
      setAnswer('')
    } catch (requestError) {
      setError(getApiErrorMessage(requestError, 'Your answer could not be evaluated.'))
    } finally {
      setIsSubmitting(false)
    }
  }

  function handleTextAnswer(event) {
    event.preventDefault()
    submitAnswer(answer)
  }

  async function handleFinish() {
    setIsFinishing(true)
    setError('')
    setRetryAction('finish')
    try {
      await finishInterview(sessionId)
      navigate(`/interviews/${sessionId}/results`, { replace: true })
    } catch (requestError) {
      setError(getApiErrorMessage(requestError, 'The final interview review could not be created.'))
    } finally {
      setIsFinishing(false)
    }
  }

  function showNextQuestion() {
    setReviewedQuestion(null)
    requestAnimationFrame(() => answerRef.current?.focus())
  }

  function retry() {
    if (retryAction === 'load') loadSession()
    else if (retryAction === 'finish') handleFinish()
  }

  if (isLoading) {
    return <div className="mx-auto max-w-5xl animate-pulse"><div className="h-5 w-40 rounded bg-slate-200 dark:bg-slate-800" /><div className="mt-8 h-96 rounded-3xl bg-slate-200 dark:bg-slate-900" /></div>
  }

  if (!session) {
    return <div className="mx-auto max-w-3xl rounded-2xl border bg-[#fdfdff] p-8 text-center dark:bg-slate-900"><AlertCircle className="mx-auto text-rose-500" /><h1 className="mt-4 font-semibold">Interview unavailable</h1><p className="mt-2 text-sm text-slate-500">{error || 'This interview could not be found.'}</p><Link to="/interviews" className="button-secondary mt-5">Back to interviews</Link></div>
  }

  return (
    <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className={session.response_mode === 'video' ? 'mx-auto max-w-6xl' : 'mx-auto max-w-4xl'}>
      <header>
        <Link to="/interviews" className="inline-flex items-center gap-1 text-xs font-semibold text-slate-500 transition hover:text-slate-900 dark:hover:text-white"><ArrowLeft size={14} />Interview setup</Link>
        <div className="mt-5 flex flex-col gap-4 sm:flex-row sm:items-end sm:justify-between">
          <div>
            <div className="flex items-center gap-2 text-sm font-semibold text-indigo-600 dark:text-indigo-400"><MessageSquareText size={15} />{session.target_role}</div>
            <h1 className="mt-2 text-2xl font-bold tracking-tight">{readable(session.difficulty)} {readable(session.interview_type)} interview</h1>
            <p className="mt-1 text-xs text-slate-500">{session.response_mode === 'video' ? 'Timed video responses' : 'Written responses'} · AI-assisted practice</p>
          </div>
          {answeredCount > 0 && <button type="button" onClick={handleFinish} disabled={isFinishing || isSubmitting} className="button-secondary shrink-0 disabled:opacity-50">{isFinishing ? 'Preparing results…' : 'Finish interview'}</button>}
        </div>
        <div className="mt-6">
          <div className="flex items-center justify-between text-xs text-slate-500"><span>Question {Math.max(progressStep, 1)} of {session.question_limit}</span><span>{answeredCount} answered</span></div>
          <div className="mt-2 h-1.5 overflow-hidden rounded-full bg-slate-200 dark:bg-slate-800"><motion.div className="h-full rounded-full bg-indigo-600" animate={{ width: `${progress}%` }} transition={{ duration: 0.3 }} /></div>
        </div>
      </header>

      {error && <div role="alert" className="mt-6 flex items-start gap-3 rounded-xl border border-rose-200 bg-rose-50 p-4 text-sm text-rose-700 dark:border-rose-900 dark:bg-rose-950/40 dark:text-rose-300"><AlertCircle size={18} className="mt-0.5 shrink-0" /><div className="flex-1"><p>{error}</p>{retryAction !== 'answer' && <button type="button" onClick={retry} className="mt-2 inline-flex items-center gap-1 font-semibold"><RefreshCw size={14} />Retry</button>}</div></div>}

      <AnimatePresence mode="wait">
        {reviewedQuestion ? (
          <motion.div key={`review-${reviewedQuestion.id}`} initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0, y: -8 }} className="mt-7">
            <QuestionFeedback question={reviewedQuestion} />
            <div className="mt-4 flex flex-col-reverse gap-3 sm:flex-row sm:justify-end">
              {currentQuestion && <button type="button" onClick={showNextQuestion} className="button-primary gap-2">Next question <ArrowRight size={16} /></button>}
              <button type="button" onClick={handleFinish} disabled={isFinishing} className="button-secondary disabled:opacity-50">{isFinishing ? 'Preparing results…' : 'Finish and view results'}</button>
            </div>
          </motion.div>
        ) : currentQuestion ? (
          session.response_mode === 'video' ? (
            <VideoInterviewAnswer key={currentQuestion.id} question={currentQuestion} isSubmitting={isSubmitting} onSubmit={submitAnswer} />
          ) : (
            <TextAnswerForm
              question={currentQuestion}
              answer={answer}
              isSubmitting={isSubmitting}
              onAnswerChange={(event) => setAnswer(event.target.value.slice(0, 10000))}
              onSubmit={handleTextAnswer}
              answerRef={answerRef}
            />
          )
        ) : (
          <motion.section key="ready-finish" initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="mt-7 rounded-3xl border bg-[#fdfdff] p-8 text-center dark:bg-slate-900">
            <h2 className="font-semibold">All questions answered</h2>
            <p className="mx-auto mt-2 max-w-md text-sm leading-6 text-slate-500">Finish the session to generate your complete coaching report.</p>
            <button type="button" onClick={handleFinish} disabled={isFinishing} className="button-primary mt-5 disabled:opacity-50">{isFinishing ? 'Preparing results…' : 'Generate final results'}</button>
          </motion.section>
        )}
      </AnimatePresence>
      <p className="mt-5 text-center text-xs text-slate-400">This is practice coaching and should not be treated as a real hiring outcome.</p>
    </motion.div>
  )
}
