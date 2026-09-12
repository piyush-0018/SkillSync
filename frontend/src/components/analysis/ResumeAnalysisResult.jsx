import { motion } from 'framer-motion'
import { AlertTriangle, Check, CircleDashed, GraduationCap, Lightbulb, ListChecks, ScanSearch, Sparkles, Wrench } from 'lucide-react'

const sectionAnimation = {
  hidden: { opacity: 0, y: 10 },
  visible: { opacity: 1, y: 0, transition: { duration: 0.3 } },
}

function ScoreRing({ score }) {
  const tone = score >= 75 ? 'text-emerald-600 dark:text-emerald-400' : score >= 50 ? 'text-amber-600 dark:text-amber-400' : 'text-rose-600 dark:text-rose-400'
  return (
    <div className="relative grid h-36 w-36 place-items-center" aria-label={`Overall score ${score} out of 100`}>
      <svg viewBox="0 0 44 44" className="absolute inset-0 -rotate-90" aria-hidden="true">
        <circle cx="22" cy="22" r="18" fill="none" stroke="currentColor" strokeWidth="3" className="text-slate-200 dark:text-slate-800" />
        <motion.circle cx="22" cy="22" r="18" fill="none" stroke="currentColor" strokeWidth="3" strokeLinecap="round" pathLength="100" strokeDasharray="100" initial={{ strokeDashoffset: 100 }} animate={{ strokeDashoffset: 100 - score }} transition={{ duration: 0.7, ease: 'easeOut' }} className={tone} />
      </svg>
      <div className="text-center"><span className="text-4xl font-bold tracking-tight">{score}</span><span className="block text-xs font-medium text-slate-400">out of 100</span></div>
    </div>
  )
}

function CategoryBreakdown({ categories }) {
  return (
    <section className="rounded-3xl border bg-[#fdfdff] p-6 dark:bg-slate-900 sm:p-7">
      <div className="flex items-center gap-2"><ListChecks size={18} className="text-indigo-600 dark:text-indigo-400" /><h2 className="font-semibold">Category breakdown</h2></div>
      <div className="mt-6 space-y-5">
        {categories.map((category) => (
          <div key={category.key}>
            <div className="flex items-center justify-between gap-4 text-sm"><span className="font-medium">{category.label}</span><span className="font-semibold tabular-nums">{category.score}<span className="font-normal text-slate-400">/{category.max_score}</span></span></div>
            <div className="mt-2 h-1.5 overflow-hidden rounded-full bg-slate-100 dark:bg-slate-800"><motion.div initial={{ width: 0 }} animate={{ width: `${(category.score / category.max_score) * 100}%` }} transition={{ duration: 0.55, ease: 'easeOut' }} className="h-full rounded-full bg-indigo-600 dark:bg-indigo-400" /></div>
            <p className="mt-2 text-xs leading-5 text-slate-500">{category.explanation}</p>
            <details className="mt-1 text-xs text-slate-400"><summary className="cursor-pointer select-none hover:text-indigo-600 dark:hover:text-indigo-400">View scoring criteria</summary><p className="mt-1.5 leading-5">{category.rubric}</p></details>
          </div>
        ))}
      </div>
    </section>
  )
}

function EvaluationCard({ icon: Icon, title, children }) {
  return (
    <motion.section variants={sectionAnimation} className="rounded-2xl border bg-[#fdfdff] p-5 dark:bg-slate-900">
      <div className="flex items-center gap-2.5"><Icon size={17} className="text-indigo-600 dark:text-indigo-400" /><h3 className="text-sm font-semibold">{title}</h3></div>
      <p className="mt-4 text-sm leading-6 text-slate-600 dark:text-slate-300">{children}</p>
    </motion.section>
  )
}

function FeedbackList({ icon: Icon, title, items, emptyText, tone = 'indigo' }) {
  const iconTone = tone === 'rose' ? 'text-rose-600 dark:text-rose-400' : tone === 'emerald' ? 'text-emerald-600 dark:text-emerald-400' : 'text-indigo-600 dark:text-indigo-400'
  return (
    <motion.section variants={sectionAnimation} className="rounded-2xl border bg-[#fdfdff] p-5 dark:bg-slate-900 sm:p-6">
      <div className="flex items-center gap-2.5"><Icon size={17} className={iconTone} /><h3 className="font-semibold">{title}</h3></div>
      {items.length ? <ul className="mt-4 space-y-3">{items.map((item, index) => <li key={`${item}-${index}`} className="flex gap-3 text-sm leading-6 text-slate-600 dark:text-slate-300"><span className="mt-2 h-1.5 w-1.5 shrink-0 rounded-full bg-slate-300 dark:bg-slate-600" />{item}</li>)}</ul> : <p className="mt-4 text-sm text-slate-400">{emptyText}</p>}
    </motion.section>
  )
}

export default function ResumeAnalysisResult({ result }) {
  const feedback = result.analysis
  return (
    <motion.div initial="hidden" animate="visible" className="space-y-6">
      <div className="grid gap-5 lg:grid-cols-[.72fr_1.28fr]">
        <motion.section variants={sectionAnimation} className="flex flex-col items-center justify-center rounded-3xl border bg-[#fdfdff] p-7 text-center dark:bg-slate-900">
          <ScoreRing score={result.overall_score} />
          <h2 className="mt-4 text-lg font-semibold">Resume-readiness score</h2>
          <p className="mt-2 max-w-xs text-xs leading-5 text-slate-500">{result.disclaimer}</p>
        </motion.section>
        <motion.div variants={sectionAnimation}><CategoryBreakdown categories={result.category_scores} /></motion.div>
      </div>

      <motion.section variants={sectionAnimation} className="rounded-2xl border border-indigo-200 bg-indigo-50/70 p-5 dark:border-indigo-900 dark:bg-indigo-950/30 sm:p-6">
        <div className="flex items-center gap-2.5 text-indigo-700 dark:text-indigo-300"><Sparkles size={17} /><h2 className="font-semibold">Profile summary</h2></div>
        <p className="mt-3 text-sm leading-7 text-slate-700 dark:text-slate-200">{feedback.profile_summary}</p>
      </motion.section>

      <motion.div variants={{ visible: { transition: { staggerChildren: 0.05 } } }} className="grid gap-4 md:grid-cols-2">
        <EvaluationCard icon={Wrench} title="Technical skills">{feedback.technical_skills_evaluation}</EvaluationCard>
        <EvaluationCard icon={CircleDashed} title="Projects">{feedback.projects_evaluation}</EvaluationCard>
        <EvaluationCard icon={ScanSearch} title="Experience">{feedback.experience_evaluation}</EvaluationCard>
        <EvaluationCard icon={GraduationCap} title="Education">{feedback.education_evaluation}</EvaluationCard>
      </motion.div>

      <motion.div variants={{ visible: { transition: { staggerChildren: 0.05 } } }} className="grid gap-4 lg:grid-cols-2">
        <FeedbackList icon={Check} title="Strengths" items={feedback.strengths} emptyText="No clear strengths were identified." tone="emerald" />
        <FeedbackList icon={AlertTriangle} title="Weaknesses" items={feedback.weaknesses} emptyText="No material weaknesses were identified." tone="rose" />
        <FeedbackList icon={CircleDashed} title="Missing information" items={feedback.missing_information} emptyText="No essential missing information was identified." />
        <FeedbackList icon={Lightbulb} title="Improvement recommendations" items={feedback.improvement_recommendations} emptyText="No recommendations were returned." />
      </motion.div>

      <motion.section variants={sectionAnimation} className="rounded-2xl border bg-[#fdfdff] p-5 dark:bg-slate-900 sm:p-6">
        <h3 className="font-semibold">Suggested skills</h3>
        {feedback.suggested_skills.length ? <div className="mt-4 flex flex-wrap gap-2">{feedback.suggested_skills.map((skill) => <span key={skill} className="rounded-full bg-[#efeff8] px-3 py-1.5 text-xs font-medium text-slate-700 dark:bg-slate-800 dark:text-slate-200">{skill}</span>)}</div> : <p className="mt-3 text-sm text-slate-400">No additional skills were suggested.</p>}
      </motion.section>

      <FeedbackList icon={ScanSearch} title="ATS-oriented observations" items={feedback.ats_observations} emptyText="No general ATS observations were returned." />
    </motion.div>
  )
}
