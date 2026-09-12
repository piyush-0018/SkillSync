import { motion } from 'framer-motion'
import { AlertTriangle, BookOpen, BriefcaseBusiness, Check, ClipboardList, Code2, GraduationCap, Lightbulb, Wrench } from 'lucide-react'

const reveal = {
  hidden: { opacity: 0, y: 10 },
  visible: { opacity: 1, y: 0, transition: { duration: 0.28 } },
}

function matchLabel(score) {
  if (score >= 75) return 'Strong compatibility'
  if (score >= 55) return 'Potential compatibility'
  return 'Several gaps to address'
}

function SkillGroup({ title, items, tone, emptyText }) {
  const styles = tone === 'rose'
    ? 'border-rose-200 bg-rose-50 text-rose-800 dark:border-rose-900 dark:bg-rose-950/30 dark:text-rose-200'
    : tone === 'amber'
      ? 'border-amber-200 bg-amber-50 text-amber-800 dark:border-amber-900 dark:bg-amber-950/30 dark:text-amber-200'
      : 'border-emerald-200 bg-emerald-50 text-emerald-800 dark:border-emerald-900 dark:bg-emerald-950/30 dark:text-emerald-200'
  return (
    <section className="rounded-2xl border bg-[#fdfdff] p-5 dark:bg-slate-900">
      <h3 className="text-sm font-semibold">{title}</h3>
      {items.length ? <div className="mt-4 flex flex-wrap gap-2">{items.map((item) => <span key={item} className={`rounded-full border px-2.5 py-1 text-xs font-medium ${styles}`}>{item}</span>)}</div> : <p className="mt-4 text-sm text-slate-400">{emptyText}</p>}
    </section>
  )
}

function AlignmentCard({ icon: Icon, title, text }) {
  return (
    <motion.section variants={reveal} className="rounded-2xl border bg-[#fdfdff] p-5 dark:bg-slate-900">
      <div className="flex items-center gap-2.5"><Icon size={17} className="text-indigo-600 dark:text-indigo-400" /><h3 className="text-sm font-semibold">{title}</h3></div>
      <p className="mt-4 text-sm leading-6 text-slate-600 dark:text-slate-300">{text}</p>
    </motion.section>
  )
}

function RequirementList({ title, items }) {
  return (
    <div><p className="text-xs font-semibold uppercase tracking-wide text-slate-400">{title}</p>{items.length ? <ul className="mt-3 space-y-2">{items.map((item, index) => <li key={`${item}-${index}`} className="text-sm leading-6 text-slate-600 dark:text-slate-300">{item}</li>)}</ul> : <p className="mt-3 text-sm text-slate-400">Not specified.</p>}</div>
  )
}

export default function JobMatchResult({ match }) {
  const { result, parsed_job: job } = match
  return (
    <motion.div initial="hidden" animate="visible" className="space-y-6">
      <motion.section variants={reveal} className="rounded-3xl border bg-[#fdfdff] p-6 dark:bg-slate-900 sm:p-8">
        <div className="flex flex-col gap-6 md:flex-row md:items-center md:justify-between">
          <div><div className="flex items-center gap-2 text-xs font-semibold uppercase tracking-wide text-indigo-600 dark:text-indigo-400"><BriefcaseBusiness size={14} /> Match summary</div><h2 className="mt-3 text-xl font-semibold">{match.job_title || 'Job title not specified'}</h2><p className="mt-2 text-sm text-slate-500">{matchLabel(result.overall_score)}</p></div>
          <div className="flex items-end gap-2"><span className="text-5xl font-bold tracking-[-0.05em] tabular-nums">{result.overall_score}</span><span className="pb-1.5 text-sm font-medium text-slate-400">/ 100</span></div>
        </div>
        <div className="mt-7 grid gap-3 border-t pt-5 sm:grid-cols-2"><div><div className="flex justify-between text-xs"><span className="font-medium text-slate-500">Required skill match</span><strong>{result.required_skill_match}%</strong></div><div className="mt-2 h-1.5 overflow-hidden rounded-full bg-slate-100 dark:bg-slate-800"><motion.div initial={{ width: 0 }} animate={{ width: `${result.required_skill_match}%` }} className="h-full rounded-full bg-indigo-600 dark:bg-indigo-400" /></div></div><div><div className="flex justify-between text-xs"><span className="font-medium text-slate-500">Preferred skill match</span><strong>{result.preferred_skill_match}%</strong></div><div className="mt-2 h-1.5 overflow-hidden rounded-full bg-slate-100 dark:bg-slate-800"><motion.div initial={{ width: 0 }} animate={{ width: `${result.preferred_skill_match}%` }} className="h-full rounded-full bg-slate-500 dark:bg-slate-400" /></div></div></div>
      </motion.section>

      {result.missing_required_skills.length > 0 && <motion.section variants={reveal} className="rounded-2xl border border-rose-200 bg-rose-50 p-5 dark:border-rose-900 dark:bg-rose-950/30 sm:p-6"><div className="flex items-start gap-3"><AlertTriangle size={19} className="mt-0.5 shrink-0 text-rose-600 dark:text-rose-400" /><div><h2 className="font-semibold text-rose-900 dark:text-rose-100">Priority required-skill gaps</h2><p className="mt-1 text-xs leading-5 text-rose-700 dark:text-rose-300">These gaps have the largest effect on this match.</p><div className="mt-4 flex flex-wrap gap-2">{result.missing_required_skills.map((skill) => <span key={skill} className="rounded-lg border border-rose-200 bg-white/70 px-3 py-1.5 text-xs font-semibold text-rose-800 dark:border-rose-800 dark:bg-rose-950/50 dark:text-rose-200">{skill}</span>)}</div></div></div></motion.section>}

      <motion.section variants={reveal} className="rounded-2xl border bg-[#fdfdff] p-5 dark:bg-slate-900 sm:p-6">
        <div className="flex items-center gap-2.5"><ClipboardList size={17} className="text-indigo-600 dark:text-indigo-400" /><h2 className="font-semibold">How the score was calculated</h2></div>
        <div className="mt-6 space-y-5">{result.category_scores.map((category) => <div key={category.key}><div className="flex items-center justify-between gap-4 text-sm"><span className="font-medium">{category.label}</span><span className="font-semibold tabular-nums">{category.score}<span className="font-normal text-slate-400">/{category.max_score}</span></span></div><div className="mt-2 h-1.5 overflow-hidden rounded-full bg-slate-100 dark:bg-slate-800"><motion.div initial={{ width: 0 }} animate={{ width: `${(category.score / category.max_score) * 100}%` }} transition={{ duration: 0.5 }} className="h-full rounded-full bg-indigo-600 dark:bg-indigo-400" /></div><p className="mt-2 text-xs leading-5 text-slate-500">{category.explanation}</p><details className="mt-1 text-xs text-slate-400"><summary className="cursor-pointer hover:text-indigo-600 dark:hover:text-indigo-400">View method</summary><p className="mt-1.5 leading-5">{category.method}</p></details></div>)}</div>
      </motion.section>

      <motion.div variants={reveal} className="grid gap-4 md:grid-cols-3">
        <SkillGroup title="Matched skills" items={result.matched_skills} tone="emerald" emptyText="No direct skill matches were identified." />
        <SkillGroup title="Missing required" items={result.missing_required_skills} tone="rose" emptyText="No required skill gaps were identified." />
        <SkillGroup title="Missing preferred" items={result.missing_preferred_skills} tone="amber" emptyText="No preferred skill gaps were identified." />
      </motion.div>

      <motion.div variants={{ visible: { transition: { staggerChildren: 0.05 } } }} className="grid gap-4 lg:grid-cols-3">
        <AlignmentCard icon={BriefcaseBusiness} title="Experience alignment" text={result.experience_alignment} />
        <AlignmentCard icon={GraduationCap} title="Education alignment" text={result.education_alignment} />
        <AlignmentCard icon={Code2} title="Project relevance" text={result.project_relevance} />
      </motion.div>

      <div className="grid gap-5 lg:grid-cols-[1.1fr_.9fr]">
        <motion.section variants={reveal} className="rounded-2xl border bg-[#fdfdff] p-5 dark:bg-slate-900 sm:p-6"><div className="flex items-center gap-2.5"><Lightbulb size={17} className="text-indigo-600 dark:text-indigo-400" /><h2 className="font-semibold">Recommendations</h2></div><ol className="mt-5 space-y-4">{result.recommendations.map((item, index) => <li key={`${item}-${index}`} className="flex gap-3 text-sm leading-6 text-slate-600 dark:text-slate-300"><span className="grid h-6 w-6 shrink-0 place-items-center rounded-md bg-indigo-50 text-xs font-semibold text-indigo-700 dark:bg-indigo-950 dark:text-indigo-300">{index + 1}</span>{item}</li>)}</ol></motion.section>
        <motion.section variants={reveal} className="rounded-2xl border bg-[#fdfdff] p-5 dark:bg-slate-900 sm:p-6"><div className="flex items-center gap-2.5"><BookOpen size={17} className="text-indigo-600 dark:text-indigo-400" /><h2 className="font-semibold">Extracted requirements</h2></div><div className="mt-5 space-y-5"><RequirementList title="Experience" items={job.experience_requirement ? [job.experience_requirement] : []} /><RequirementList title="Education" items={job.education_requirements} /><RequirementList title="Responsibilities" items={job.responsibilities.slice(0, 6)} /><RequirementList title="Tools and technologies" items={job.tools_technologies} /></div></motion.section>
      </div>

      <motion.div variants={reveal} className="flex items-center gap-2 text-xs text-slate-400"><Check size={14} className="text-emerald-500" />Saved automatically · {match.disclaimer}</motion.div>
    </motion.div>
  )
}
