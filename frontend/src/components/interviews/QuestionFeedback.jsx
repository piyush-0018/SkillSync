import { CheckCircle2, Lightbulb, TrendingUp } from 'lucide-react'

export default function QuestionFeedback({ question, compact = false }) {
  const evaluation = question?.evaluation
  if (!evaluation) return null

  return (
    <section className="rounded-2xl border bg-[#fdfdff] p-5 dark:bg-slate-900 sm:p-6" aria-live="polite">
      <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between"><div><p className="text-xs font-semibold uppercase tracking-[0.16em] text-indigo-600 dark:text-indigo-400">Coaching feedback</p><h2 className="mt-1 font-semibold">Your answer review</h2></div><div className="flex items-baseline gap-1"><strong className="text-2xl tracking-tight">{evaluation.overall_score}</strong><span className="text-xs text-slate-500">/100</span></div></div>
      <div className="mt-5 grid gap-2 sm:grid-cols-5">{evaluation.rubric_scores.map((item) => <div key={item.key} className="rounded-xl bg-[#f5f5fa] p-3 dark:bg-slate-950"><div className="flex items-center justify-between gap-2"><span className="text-xs font-medium text-slate-500">{item.label}</span><strong className="text-sm">{item.rating}/4</strong></div>{!compact && <p className="mt-2 text-[11px] leading-4 text-slate-500">{item.feedback}</p>}</div>)}</div>
      <p className="mt-5 text-sm leading-6 text-slate-600 dark:text-slate-300">{evaluation.coaching_feedback}</p>
      {!compact && <div className="mt-5 grid gap-4 border-t pt-5 md:grid-cols-2"><div><h3 className="flex items-center gap-2 text-xs font-semibold uppercase tracking-wide text-emerald-700 dark:text-emerald-400"><CheckCircle2 size={14} />What worked</h3><ul className="mt-3 space-y-2 text-sm text-slate-600 dark:text-slate-300">{evaluation.strengths.map((item) => <li key={item} className="flex gap-2"><span className="mt-2 h-1 w-1 shrink-0 rounded-full bg-emerald-500" />{item}</li>)}</ul></div><div><h3 className="flex items-center gap-2 text-xs font-semibold uppercase tracking-wide text-amber-700 dark:text-amber-400"><Lightbulb size={14} />Improve next</h3><ul className="mt-3 space-y-2 text-sm text-slate-600 dark:text-slate-300">{evaluation.improvements.map((item) => <li key={item} className="flex gap-2"><TrendingUp size={13} className="mt-1 shrink-0 text-amber-500" />{item}</li>)}</ul></div></div>}
    </section>
  )
}
