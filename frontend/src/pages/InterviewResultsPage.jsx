import { motion } from 'framer-motion'
import { AlertCircle, ArrowLeft, BookOpen, CheckCircle2, MessageCircle, RotateCcw, Target, TrendingUp } from 'lucide-react'
import { useCallback, useEffect, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import QuestionFeedback from '../components/interviews/QuestionFeedback'
import { getApiErrorMessage } from '../services/api'
import { getInterview } from '../services/interviewService'

function FeedbackList({ title, icon: Icon, items, tone = 'indigo' }) {
  const colors = {
    indigo: 'bg-indigo-50 text-indigo-600 dark:bg-indigo-950 dark:text-indigo-300',
    emerald: 'bg-emerald-50 text-emerald-600 dark:bg-emerald-950 dark:text-emerald-300',
    amber: 'bg-amber-50 text-amber-700 dark:bg-amber-950 dark:text-amber-300',
  }
  return (
    <section className="rounded-2xl border bg-[#fdfdff] p-5 dark:bg-slate-900"><div className="flex items-center gap-3"><span className={`grid h-9 w-9 place-items-center rounded-lg ${colors[tone]}`}><Icon size={17} /></span><h2 className="font-semibold">{title}</h2></div>{items.length ? <ul className="mt-4 space-y-2 text-sm leading-6 text-slate-600 dark:text-slate-300">{items.map((item) => <li key={item} className="flex gap-2"><span className="mt-2.5 h-1 w-1 shrink-0 rounded-full bg-current opacity-60" />{item}</li>)}</ul> : <p className="mt-4 text-sm text-slate-400">No specific items were identified.</p>}</section>
  )
}

export default function InterviewResultsPage() {
  const { sessionId } = useParams()
  const [session, setSession] = useState(null)
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState('')

  const load = useCallback(async () => {
    setIsLoading(true)
    setError('')
    try {
      setSession(await getInterview(sessionId))
    } catch (requestError) {
      setError(getApiErrorMessage(requestError, 'Could not load interview results.'))
    } finally {
      setIsLoading(false)
    }
  }, [sessionId])

  useEffect(() => { load() }, [load])

  if (isLoading) return <div className="mx-auto max-w-5xl animate-pulse"><div className="h-36 rounded-3xl bg-slate-200 dark:bg-slate-900" /><div className="mt-5 grid gap-4 md:grid-cols-2"><div className="h-44 rounded-2xl bg-slate-200 dark:bg-slate-900" /><div className="h-44 rounded-2xl bg-slate-200 dark:bg-slate-900" /></div></div>
  if (error || !session) return <div className="mx-auto max-w-3xl rounded-2xl border bg-[#fdfdff] p-8 text-center dark:bg-slate-900"><AlertCircle className="mx-auto text-rose-500" /><h1 className="mt-4 font-semibold">Results unavailable</h1><p className="mt-2 text-sm text-slate-500">{error}</p><button type="button" onClick={load} className="button-secondary mt-5">Retry</button></div>
  if (session.status !== 'completed' || !session.final_feedback) return <div className="mx-auto max-w-3xl rounded-2xl border bg-[#fdfdff] p-8 text-center dark:bg-slate-900"><Target className="mx-auto text-indigo-500" /><h1 className="mt-4 font-semibold">This interview is still active</h1><p className="mt-2 text-sm text-slate-500">Finish the session before opening the final coaching report.</p><Link to={`/interviews/${session.id}`} className="button-primary mt-5">Continue interview</Link></div>

  const feedback = session.final_feedback
  return (
    <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} className="mx-auto max-w-5xl">
      <Link to="/interviews" className="inline-flex items-center gap-1 text-xs font-semibold text-slate-500 transition hover:text-slate-900 dark:hover:text-white"><ArrowLeft size={14} />All interviews</Link>
      <section className="relative mt-5 overflow-hidden rounded-3xl bg-slate-950 p-6 text-white dark:bg-indigo-600 sm:p-8"><div className="absolute -right-16 -top-20 h-56 w-56 rounded-full border-[38px] border-white/5" /><div className="relative flex flex-col gap-7 sm:flex-row sm:items-center sm:justify-between"><div><p className="text-xs font-semibold uppercase tracking-[0.18em] text-indigo-300 dark:text-indigo-100">Interview complete</p><h1 className="mt-2 text-2xl font-bold tracking-tight">{session.target_role}</h1><p className="mt-2 text-sm capitalize text-slate-400 dark:text-indigo-100">{session.difficulty} · {session.interview_type.replace('_', ' ')} · {session.response_mode || 'text'} responses · {session.answered_count} questions answered</p><p className="mt-5 max-w-2xl text-sm leading-6 text-slate-300 dark:text-white/90">{feedback.summary}</p></div><div className="shrink-0 rounded-2xl bg-white/10 px-7 py-5 text-center backdrop-blur-sm"><strong className="block text-4xl tracking-tight">{Math.round(session.overall_score)}</strong><span className="mt-1 block text-xs text-slate-300 dark:text-indigo-100">out of 100</span></div></div></section>
      <div className="mt-5 grid gap-4 md:grid-cols-2"><FeedbackList title="Technical strengths" icon={CheckCircle2} items={feedback.technical_strengths} tone="emerald" /><FeedbackList title="Weak areas" icon={TrendingUp} items={feedback.weak_areas} tone="amber" /><FeedbackList title="Topics to revise" icon={BookOpen} items={feedback.topics_to_revise} /><FeedbackList title="Suggested next steps" icon={RotateCcw} items={feedback.suggested_next_steps} /></div>
      <section className="mt-4 rounded-2xl border bg-[#fdfdff] p-5 dark:bg-slate-900 sm:p-6"><h2 className="flex items-center gap-2 font-semibold"><MessageCircle size={17} className="text-indigo-500" />Communication feedback</h2><p className="mt-3 text-sm leading-6 text-slate-600 dark:text-slate-300">{feedback.communication_feedback}</p></section>
      <section className="mt-8"><div><h2 className="font-semibold">Question-level feedback</h2><p className="mt-1 text-xs text-slate-500">Review the evidence behind your final score.</p></div><div className="mt-4 space-y-4">{session.questions.filter((question) => question.evaluation).map((question) => <article key={question.id} className="rounded-3xl border bg-[#f8f8fc] p-4 dark:bg-slate-950/40 sm:p-5"><div className="px-1 pb-4"><p className="text-xs font-semibold text-indigo-600 dark:text-indigo-400">Question {question.sequence_number} · {question.focus_area}</p><h3 className="mt-2 text-sm font-semibold leading-6">{question.question_text}</h3><details className="mt-3 text-xs text-slate-500"><summary className="cursor-pointer font-medium">Review your answer</summary><p className="mt-2 whitespace-pre-wrap rounded-lg bg-white p-3 leading-5 dark:bg-slate-900">{question.answer_text}</p></details></div><QuestionFeedback question={question} compact /></article>)}</div></section>
      <div className="mt-7 flex flex-col gap-3 border-t pt-6 sm:flex-row sm:items-center sm:justify-between"><p className="text-xs text-slate-400">AI-assisted coaching only — this report is not a hiring decision.</p><Link to="/interviews" className="button-primary">Practice another interview</Link></div>
    </motion.div>
  )
}
