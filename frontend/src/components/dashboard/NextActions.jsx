import { ArrowRight, Compass, Sparkles } from 'lucide-react'
import { Link } from 'react-router-dom'

export default function NextActions({ actions }) {
  const [primaryAction, ...otherActions] = actions

  if (!primaryAction) return null

  return (
    <div className="grid gap-4 xl:grid-cols-[minmax(0,1.55fr)_minmax(300px,.8fr)]">
      <section className="focus-card overflow-hidden p-5 sm:p-6">
        <div className="flex items-center gap-2 text-[11px] font-bold uppercase tracking-[.14em] text-blue-700 dark:text-blue-300"><Compass size={15} />Next best action</div>
        <div className="mt-6 flex flex-col justify-between gap-6 sm:flex-row sm:items-end">
          <div className="max-w-xl"><h2 className="text-xl font-semibold tracking-[-.025em] sm:text-2xl">{primaryAction.title}</h2><p className="mt-2 text-sm leading-6 text-[var(--text-secondary)]">{primaryAction.description}</p></div>
          <Link to={primaryAction.path} className="button-primary shrink-0 gap-2">Open task<ArrowRight size={15} /></Link>
        </div>
      </section>
      <section className="surface-panel p-5">
        <div className="flex items-center gap-2"><Sparkles size={16} className="text-[var(--primary)]" /><h2 className="text-sm font-semibold">After that</h2></div>
        <div className="mt-3 divide-y">{otherActions.slice(0, 2).map((action) => <Link key={action.key} to={action.path} className="group flex items-center justify-between gap-3 py-3 text-sm font-medium"><span>{action.title}</span><ArrowRight size={14} className="shrink-0 text-slate-400 transition group-hover:translate-x-0.5 group-hover:text-[var(--primary)]" /></Link>)}</div>
      </section>
    </div>
  )
}
