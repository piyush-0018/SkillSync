import { motion } from 'framer-motion'
import {
  ArrowRight,
  BarChart3,
  Bot,
  BriefcaseBusiness,
  Check,
  FileSearch,
  Gauge,
  MessageSquareText,
  Target,
} from 'lucide-react'
import { Link } from 'react-router-dom'
import Reveal from '../components/ui/Reveal'

const workflow = [
  ['01', 'Upload resume'],
  ['02', 'Analyze profile'],
  ['03', 'Match roles'],
  ['04', 'Identify gaps'],
  ['05', 'Practise'],
  ['06', 'Improve'],
]

const capabilities = [
  {
    icon: FileSearch,
    eyebrow: 'Resume intelligence',
    title: 'See what your resume proves—and what it leaves unclear.',
    text: 'A structured readiness review turns projects, skills, and experience into practical priorities for your target role.',
    className: 'lg:col-span-7',
  },
  {
    icon: Target,
    eyebrow: 'Role comparison',
    title: 'Compare evidence with a real job description.',
    text: 'Separate matched skills from required and preferred gaps before you apply.',
    className: 'lg:col-span-5',
  },
  {
    icon: Bot,
    eyebrow: 'Contextual guidance',
    title: 'Ask questions grounded in your own preparation.',
    text: 'The career assistant can use your resume, saved analyses, and target role instead of returning generic advice.',
    className: 'lg:col-span-5',
  },
  {
    icon: MessageSquareText,
    eyebrow: 'Interview practice',
    title: 'Practise deliberately, then review the evidence.',
    text: 'Run role-focused sessions, revisit question-level feedback, and compare saved performance over time.',
    className: 'lg:col-span-7',
  },
]

function WorkspacePreview() {
  return (
    <div className="relative overflow-hidden rounded-2xl border bg-[var(--surface-elevated)] shadow-[var(--shadow-elevated)]">
      <div className="flex h-11 items-center justify-between border-b px-4">
        <div className="flex items-center gap-2 text-[11px] font-semibold"><span className="h-2 w-2 rounded-full bg-blue-600" />SkillSync workspace</div>
        <span className="text-[10px] font-medium uppercase tracking-[.12em] text-slate-500">Illustrative preview</span>
      </div>
      <div className="grid sm:grid-cols-[136px_1fr]">
        <aside className="hidden border-r bg-[var(--surface-subtle)] p-3 sm:block">
          {['Overview', 'Resume', 'Job match', 'Interviews'].map((item, index) => <div key={item} className={`mb-1 rounded-md px-3 py-2 text-[10px] font-medium ${index === 0 ? 'bg-blue-600 text-white' : 'text-slate-500'}`}>{item}</div>)}
        </aside>
        <div className="p-5 sm:p-6">
          <div className="flex items-end justify-between gap-4"><div><p className="text-[10px] font-semibold uppercase tracking-[.14em] text-blue-700 dark:text-blue-300">Preparation overview</p><h2 className="mt-1 text-lg font-semibold">Backend developer</h2></div><span className="text-xs text-slate-500">Preview data</span></div>
          <div className="mt-6 grid grid-cols-2 gap-3">
            <div className="rounded-xl border bg-[var(--surface-subtle)] p-4"><p className="text-[10px] text-slate-500">Resume readiness</p><p className="data-value mt-2 text-2xl font-semibold">74<span className="text-xs text-slate-500">/100</span></p><div className="mt-3 h-1.5 overflow-hidden rounded-full bg-[var(--border)]"><div className="h-full w-[74%] rounded-full bg-blue-600" /></div></div>
            <div className="rounded-xl border bg-[var(--surface-subtle)] p-4"><p className="text-[10px] text-slate-500">Role compatibility</p><p className="data-value mt-2 text-2xl font-semibold">68<span className="text-xs text-slate-500">/100</span></p><div className="mt-3 h-1.5 overflow-hidden rounded-full bg-[var(--border)]"><div className="h-full w-[68%] rounded-full bg-blue-600" /></div></div>
          </div>
          <div className="mt-3 rounded-xl border p-4"><p className="text-[10px] font-semibold uppercase tracking-[.12em] text-slate-500">Recommended next step</p><div className="mt-3 flex items-start gap-3"><span className="mt-0.5 grid h-6 w-6 shrink-0 place-items-center rounded-md bg-blue-600 text-white"><ArrowRight size={13} /></span><div><p className="text-xs font-semibold">Strengthen project evidence</p><p className="mt-1 text-[11px] leading-5 text-slate-500">Add measurable outcomes to your most relevant backend project.</p></div></div></div>
          <div className="mt-3 grid gap-3 sm:grid-cols-2"><div className="rounded-xl border p-4"><p className="text-[10px] text-slate-500">Strong signals</p><div className="mt-3 flex flex-wrap gap-1.5">{['Python', 'FastAPI', 'REST'].map((skill) => <span key={skill} className="rounded-md border px-2 py-1 text-[10px] font-medium">{skill}</span>)}</div></div><div className="rounded-xl border p-4"><p className="text-[10px] text-slate-500">Priority gap</p><p className="mt-3 text-xs font-semibold">Deployment evidence</p><p className="mt-1 text-[10px] text-slate-500">Docker · CI/CD</p></div></div>
        </div>
      </div>
    </div>
  )
}

function AnalysisPreview() {
  return (
    <div className="grid gap-3 rounded-2xl border bg-[var(--surface)] p-4 sm:grid-cols-[.65fr_1.35fr] sm:p-5">
      <div className="rounded-xl bg-slate-950 p-5 text-white dark:bg-blue-600"><Gauge size={18} className="text-blue-300 dark:text-blue-100" /><p className="mt-8 text-xs text-slate-400 dark:text-blue-100">Readiness score</p><p className="data-value mt-1 text-3xl font-semibold">74<span className="text-sm text-slate-400 dark:text-blue-100">/100</span></p><p className="mt-5 text-[10px] leading-4 text-slate-400 dark:text-blue-100">A preparation signal, not a hiring decision.</p></div>
      <div className="space-y-2">{[['Skills', 82], ['Projects', 69], ['Experience', 58], ['Structure', 88]].map(([label, value]) => <div key={label} className="rounded-lg border bg-[var(--surface-elevated)] p-3"><div className="flex justify-between text-[10px] font-medium"><span>{label}</span><span>{value}</span></div><div className="mt-2 h-1 rounded-full bg-[var(--border)]"><div className="h-full rounded-full bg-blue-600" style={{ width: `${value}%` }} /></div></div>)}</div>
    </div>
  )
}

function MatchPreview() {
  return (
    <div className="rounded-2xl border bg-[var(--surface)] p-5"><div className="flex items-start justify-between"><div><p className="text-[10px] text-slate-500">Role comparison</p><p className="mt-1 text-sm font-semibold">Junior backend engineer</p></div><span className="data-value text-xl font-semibold">68%</span></div><div className="mt-5 grid gap-3 sm:grid-cols-2"><div><p className="text-[10px] font-semibold uppercase tracking-[.12em] text-emerald-700 dark:text-emerald-300">Matched</p><div className="mt-2 space-y-2">{['Python', 'REST APIs', 'PostgreSQL'].map((skill) => <p key={skill} className="flex items-center gap-2 text-xs"><Check size={12} className="text-emerald-600" />{skill}</p>)}</div></div><div><p className="text-[10px] font-semibold uppercase tracking-[.12em] text-amber-700 dark:text-amber-300">Missing required</p><div className="mt-2 space-y-2">{['Docker', 'Testing'].map((skill) => <p key={skill} className="text-xs">{skill}</p>)}</div></div></div></div>
  )
}

export default function LandingPage() {
  return (
    <main>
      <section className="hero-surface relative overflow-hidden border-b">
        <div className="hero-grid absolute inset-0 opacity-60" />
        <div className="container-page relative grid items-center gap-12 py-16 lg:grid-cols-[.84fr_1.16fr] lg:py-24">
          <motion.div initial={{ opacity: 0, y: 14 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.42 }}>
            <div className="flex items-center gap-3 text-xs font-semibold uppercase tracking-[.14em] text-blue-700 dark:text-blue-300"><span className="h-px w-7 bg-blue-600" />Career intelligence for students</div>
            <h1 className="text-balance mt-6 max-w-2xl text-4xl font-semibold leading-[1.05] tracking-[-0.05em] sm:text-5xl">Build the skills. Match the role. Prepare smarter.</h1>
            <p className="mt-6 max-w-xl text-base leading-7 text-slate-600 dark:text-slate-300">Analyze your resume, understand skill gaps, compare real job requirements, and practise interviews from one connected preparation workspace.</p>
            <div className="mt-8 flex flex-col gap-3 sm:flex-row"><Link to="/register" className="button-primary group gap-2 px-5 py-3">Create your workspace <ArrowRight size={16} className="transition-transform group-hover:translate-x-0.5" /></Link><a href="#how-it-works" className="button-secondary px-5 py-3">See how it works</a></div>
            <p className="mt-5 text-xs text-slate-500">Built around your saved evidence. No permanent demo metrics.</p>
          </motion.div>
          <motion.div initial={{ opacity: 0, x: 18 }} animate={{ opacity: 1, x: 0 }} transition={{ duration: 0.5, delay: 0.08 }}><WorkspacePreview /></motion.div>
        </div>
      </section>

      <section aria-label="SkillSync outcomes" className="border-b bg-[var(--surface-elevated)]"><div className="container-page grid divide-y sm:grid-cols-2 sm:divide-x sm:divide-y-0 lg:grid-cols-4">{[[FileSearch, 'Resume clarity', 'Find the evidence recruiters can verify.'], [BriefcaseBusiness, 'Role alignment', 'Compare your profile with a real opportunity.'], [MessageSquareText, 'Interview practice', 'Turn feedback into deliberate preparation.'], [BarChart3, 'Stored progress', 'Track only results you have actually created.']].map(([Icon, title, text]) => <div key={title} className="flex gap-3 px-1 py-6 sm:px-5"><Icon size={17} className="mt-0.5 shrink-0 text-blue-700 dark:text-blue-300" /><div><h2 className="text-sm font-semibold">{title}</h2><p className="mt-1 text-xs leading-5 text-slate-500">{text}</p></div></div>)}</div></section>

      <section id="features" className="container-page py-20 lg:py-28">
        <Reveal className="grid gap-6 lg:grid-cols-[.72fr_1.28fr]"><div><p className="page-kicker">Connected preparation</p><h2 className="text-balance mt-3 max-w-lg text-3xl font-semibold tracking-[-0.04em] sm:text-4xl">One workspace for the work between learning and applying.</h2></div><p className="max-w-2xl text-sm leading-7 text-slate-600 dark:text-slate-300 lg:pt-8">SkillSync organizes career preparation around evidence: what your resume demonstrates, what a role expects, and what your saved practice results suggest doing next.</p></Reveal>
        <div className="mt-12 grid gap-4 lg:grid-cols-12">{capabilities.map(({ icon: Icon, eyebrow, title, text, className }, index) => <Reveal key={title} delay={index * 0.04} className={className}><article className="flex h-full min-h-60 flex-col border-t border-[var(--text-primary)] bg-[var(--surface-elevated)] p-6"><div className="flex items-center justify-between"><Icon size={19} className="text-blue-700 dark:text-blue-300" /><span className="text-xs text-slate-500">0{index + 1}</span></div><div className="mt-auto pt-12"><p className="text-xs font-semibold uppercase tracking-[.12em] text-slate-500">{eyebrow}</p><h3 className="mt-2 max-w-xl text-xl font-semibold tracking-[-0.02em]">{title}</h3><p className="mt-3 max-w-xl text-sm leading-6 text-slate-500">{text}</p></div></article></Reveal>)}</div>
      </section>

      <section id="how-it-works" className="border-y bg-slate-950 text-white"><div className="container-page py-20"><Reveal><p className="text-sm font-semibold text-blue-300">A clear preparation loop</p><h2 className="mt-3 text-3xl font-semibold tracking-[-0.035em]">From resume to focused improvement.</h2></Reveal><div className="mt-10 grid gap-px overflow-hidden rounded-xl border border-white/10 bg-white/10 sm:grid-cols-2 lg:grid-cols-6">{workflow.map(([number, label], index) => <Reveal key={number} delay={index * 0.03}><div className="h-full bg-slate-950 p-4"><span className="text-[10px] font-semibold text-blue-300">{number}</span><p className="mt-8 text-sm font-medium">{label}</p></div></Reveal>)}</div></div></section>

      <section id="platform" className="container-page space-y-20 py-20 lg:space-y-28 lg:py-28">
        <Reveal><article className="grid items-center gap-10 lg:grid-cols-2 lg:gap-20"><div><p className="page-kicker">Resume analysis</p><h2 className="mt-3 text-3xl font-semibold tracking-[-0.035em]">Priorities you can act on before the next application.</h2><p className="mt-5 max-w-xl text-sm leading-7 text-slate-600 dark:text-slate-300">Review skills, projects, experience, completeness, and structure without turning one score into an official hiring prediction.</p><Link to="/register" className="mt-6 inline-flex items-center gap-2 text-sm font-semibold text-blue-700 dark:text-blue-300">Analyze your resume <ArrowRight size={15} /></Link></div><AnalysisPreview /></article></Reveal>
        <Reveal><article className="grid items-center gap-10 lg:grid-cols-2 lg:gap-20"><div className="lg:order-2"><p className="page-kicker">Job matching</p><h2 className="mt-3 text-3xl font-semibold tracking-[-0.035em]">Understand the gap for a specific opportunity.</h2><p className="mt-5 max-w-xl text-sm leading-7 text-slate-600 dark:text-slate-300">Matched skills, missing requirements, project relevance, and alignment guidance stay tied to the description you provide.</p><Link to="/register" className="mt-6 inline-flex items-center gap-2 text-sm font-semibold text-blue-700 dark:text-blue-300">Compare a role <ArrowRight size={15} /></Link></div><div className="lg:order-1"><MatchPreview /></div></article></Reveal>
        <Reveal><article className="grid gap-6 border-y py-10 lg:grid-cols-[.7fr_1.3fr] lg:items-center"><div><p className="page-kicker">Guidance and practice</p><h2 className="mt-3 text-3xl font-semibold tracking-[-0.035em]">Ask with context. Practise with purpose.</h2></div><div className="grid gap-4 sm:grid-cols-2"><div className="border-l-2 border-blue-600 pl-5"><Bot size={18} className="text-blue-700 dark:text-blue-300" /><h3 className="mt-5 font-semibold">Career assistant</h3><p className="mt-2 text-sm leading-6 text-slate-500">Guidance can reference your saved resume, analyses, job comparisons, and career goal.</p></div><div className="border-l-2 border-blue-600 pl-5"><MessageSquareText size={18} className="text-blue-700 dark:text-blue-300" /><h3 className="mt-5 font-semibold">Mock interviews</h3><p className="mt-2 text-sm leading-6 text-slate-500">Role-focused sessions provide question-level feedback and stored performance history.</p></div></div></article></Reveal>
      </section>

      <section className="container-page pb-20 lg:pb-28"><Reveal><div className="grid gap-8 border-t-2 border-slate-950 bg-[var(--surface-elevated)] px-6 py-10 dark:border-blue-400 sm:px-10 lg:grid-cols-[1fr_auto] lg:items-center"><div><p className="text-sm font-semibold text-blue-700 dark:text-blue-300">Start with your own evidence</p><h2 className="mt-2 max-w-2xl text-2xl font-semibold tracking-[-0.03em] sm:text-3xl">Build a clearer path from preparation to application.</h2></div><Link to="/register" className="button-primary gap-2 px-5 py-3">Get started <ArrowRight size={16} /></Link></div></Reveal></section>
    </main>
  )
}
