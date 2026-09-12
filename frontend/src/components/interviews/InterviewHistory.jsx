import { ArrowRight, Clock3, History, Keyboard, Video } from 'lucide-react'
import { Link } from 'react-router-dom'

function readable(value) {
  return value.replace('_', ' ').replace(/\b\w/g, (letter) => letter.toUpperCase())
}

export default function InterviewHistory({ sessions, isLoading }) {
  return (
    <section className="rounded-3xl border bg-[#fdfdff] p-5 dark:bg-slate-900 sm:p-6">
      <div className="flex items-center gap-2"><History size={17} className="text-slate-400" /><h2 className="font-semibold">Interview history</h2></div>
      {isLoading ? <div className="mt-5 space-y-3"><div className="h-20 animate-pulse rounded-xl bg-slate-100 dark:bg-slate-800" /><div className="h-20 animate-pulse rounded-xl bg-slate-100 dark:bg-slate-800" /></div> : sessions.length ? <div className="mt-5 divide-y">{sessions.map((session) => {
        const destination = session.status === 'completed' ? `/interviews/${session.id}/results` : `/interviews/${session.id}`
        const ModeIcon = session.response_mode === 'video' ? Video : Keyboard
        return <article key={session.id} className="flex flex-col gap-3 py-4 first:pt-0 last:pb-0 sm:flex-row sm:items-center sm:justify-between"><div className="min-w-0"><div className="flex flex-wrap items-center gap-2"><h3 className="truncate text-sm font-semibold">{session.target_role}</h3><span className={`rounded-full px-2 py-0.5 text-[10px] font-semibold uppercase tracking-wide ${session.status === 'completed' ? 'bg-emerald-50 text-emerald-700 dark:bg-emerald-950 dark:text-emerald-300' : 'bg-amber-50 text-amber-700 dark:bg-amber-950 dark:text-amber-300'}`}>{session.status}</span></div><p className="mt-1 flex flex-wrap items-center gap-x-3 gap-y-1 text-xs text-slate-500"><span>{readable(session.difficulty)} · {readable(session.interview_type)}</span><span className="inline-flex items-center gap-1"><ModeIcon size={12} />{readable(session.response_mode || 'text')}</span><span className="inline-flex items-center gap-1"><Clock3 size={12} />{new Date(session.started_at).toLocaleDateString()}</span><span>{session.answered_count}/{session.question_limit} answered</span>{session.overall_score != null && <strong className="text-slate-700 dark:text-slate-200">{Math.round(session.overall_score)}/100</strong>}</p></div><Link to={destination} className="inline-flex shrink-0 items-center gap-1 text-xs font-semibold text-indigo-600 dark:text-indigo-400">{session.status === 'completed' ? 'View results' : 'Resume session'} <ArrowRight size={13} /></Link></article>
      })}</div> : <div className="mt-6 rounded-2xl border border-dashed bg-[#fafaff] px-5 py-8 text-center dark:bg-slate-950/40"><p className="text-sm font-medium">No interview sessions yet</p><p className="mt-1 text-xs leading-5 text-slate-500">Your active and completed practice sessions will appear here.</p></div>}
    </section>
  )
}
