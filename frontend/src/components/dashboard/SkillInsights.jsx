import { AlertTriangle, BadgeCheck } from 'lucide-react'

function EmptyInsight({ children }) {
  return <div className="mt-5 rounded-xl border border-dashed bg-[#fafaff] px-4 py-7 text-center text-xs leading-5 text-slate-500 dark:bg-slate-950/40">{children}</div>
}

export default function SkillInsights({ strengths, missing }) {
  const maxMatches = Math.max(1, ...strengths.map((skill) => skill.match_count))
  const maxMissing = Math.max(1, ...missing.map((skill) => skill.count))
  return (
    <div className="grid gap-4 lg:grid-cols-2">
      <section className="rounded-2xl border bg-[#fdfdff] p-5 dark:bg-slate-900"><div className="flex items-center gap-2"><BadgeCheck size={17} className="text-emerald-600 dark:text-emerald-400" /><h3 className="text-sm font-semibold">Strongest skill signals</h3></div><p className="mt-1 text-xs text-slate-500">Resume skills ranked by saved job-match evidence.</p>{strengths.length ? <div className="mt-5 space-y-4">{strengths.map((skill) => <div key={skill.name}><div className="flex items-center justify-between gap-3 text-xs"><span className="font-medium">{skill.name}</span><span className="text-slate-500">{skill.match_count ? `${skill.match_count} job match${skill.match_count === 1 ? '' : 'es'}` : 'Resume only'}</span></div><div className="mt-2 h-1.5 overflow-hidden rounded-full bg-slate-100 dark:bg-slate-800"><div className="h-full rounded-full bg-emerald-500" style={{ width: `${skill.match_count ? Math.max(14, (skill.match_count / maxMatches) * 100) : 8}%` }} /></div></div>)}</div> : <EmptyInsight>Upload a parsed resume and complete job comparisons to build skill evidence.</EmptyInsight>}</section>
      <section className="rounded-2xl border bg-[#fdfdff] p-5 dark:bg-slate-900"><div className="flex items-center gap-2"><AlertTriangle size={17} className="text-amber-600 dark:text-amber-400" /><h3 className="text-sm font-semibold">Most common missing skills</h3></div><p className="mt-1 text-xs text-slate-500">Repeated gaps found across saved job analyses.</p>{missing.length ? <div className="mt-5 space-y-4">{missing.map((skill) => <div key={skill.name}><div className="flex items-center justify-between gap-3 text-xs"><span className="font-medium">{skill.name}</span><span className="text-slate-500">{skill.required_count ? `${skill.required_count} required` : `${skill.preferred_count} preferred`}</span></div><div className="mt-2 h-1.5 overflow-hidden rounded-full bg-slate-100 dark:bg-slate-800"><div className="h-full rounded-full bg-amber-500" style={{ width: `${Math.max(14, (skill.count / maxMissing) * 100)}%` }} /></div></div>)}</div> : <EmptyInsight>No missing-skill evidence is available yet. Analyze job descriptions to identify recurring gaps.</EmptyInsight>}</section>
    </div>
  )
}
