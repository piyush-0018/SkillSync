import { motion } from 'framer-motion'
import { AlertCircle, ArrowRight, CheckCircle2, Circle, MessageSquareText, RefreshCw, Sparkles } from 'lucide-react'
import { Link } from 'react-router-dom'
import AnalyticsMetricCard from '../components/dashboard/AnalyticsMetricCard'
import BackendStatus from '../components/dashboard/BackendStatus'
import NextActions from '../components/dashboard/NextActions'
import WorkspaceSummary from '../components/dashboard/WorkspaceSummary'
import { useAuth } from '../context/AuthContext'
import useCareerAnalytics from '../hooks/useCareerAnalytics'

const container = {
  hidden: { opacity: 0 },
  visible: { opacity: 1, transition: { staggerChildren: 0.06 } },
}

const section = {
  hidden: { opacity: 0, y: 10 },
  visible: { opacity: 1, y: 0, transition: { duration: 0.3 } },
}

function getGreeting() {
  const hour = new Date().getHours()
  if (hour < 12) return 'Good morning'
  if (hour < 18) return 'Good afternoon'
  return 'Good evening'
}

function DashboardSkeleton() {
  return <div className="mx-auto max-w-6xl animate-pulse"><div className="h-20 max-w-lg rounded-2xl bg-slate-200/70 dark:bg-slate-900" /><div className="mt-8 grid gap-4 sm:grid-cols-2 xl:grid-cols-4">{Array.from({ length: 4 }).map((_, index) => <div key={index} className="h-32 rounded-2xl bg-slate-200/70 dark:bg-slate-900" />)}</div><div className="mt-6 grid gap-4 lg:grid-cols-2"><div className="h-64 rounded-2xl bg-slate-200/70 dark:bg-slate-900" /><div className="h-64 rounded-2xl bg-slate-200/70 dark:bg-slate-900" /></div></div>
}

function EvidenceTimeline({ analytics }) {
  const evidence = [
    {
      complete: analytics.latest_resume_score.sample_size > 0,
      title: 'Resume evidence reviewed',
      detail: analytics.latest_resume_score.sample_size > 0 ? `${analytics.latest_resume_score.sample_size} saved analysis ${analytics.latest_resume_score.sample_size === 1 ? 'report' : 'reports'}` : 'Analyze your resume to establish a readiness baseline',
      to: '/resume/analysis',
    },
    {
      complete: analytics.job_analyses_completed > 0,
      title: 'Role requirements compared',
      detail: analytics.job_analyses_completed > 0 ? `${analytics.job_analyses_completed} job ${analytics.job_analyses_completed === 1 ? 'description' : 'descriptions'} compared with your resume` : 'Compare a real role to reveal the most useful skill gaps',
      to: '/job-match',
    },
    {
      complete: analytics.interviews_completed > 0,
      title: 'Interview evidence recorded',
      detail: analytics.interviews_completed > 0 ? `${analytics.interviews_completed} completed practice ${analytics.interviews_completed === 1 ? 'session' : 'sessions'}` : 'Run a focused mock interview for your target role',
      to: '/interviews',
    },
  ]

  return (
    <section className="surface-panel overflow-hidden">
      <div className="border-b px-5 py-4 sm:px-6"><h2 className="text-sm font-semibold">Evidence timeline</h2><p className="mt-1 text-xs text-slate-500">A clear record of what SkillSync can use to guide you.</p></div>
      <div className="divide-y">{evidence.map((item) => <Link key={item.title} to={item.to} className="evidence-row group grid grid-cols-[1.5rem_minmax(0,1fr)_auto] gap-3 px-5 py-4 sm:px-6">{item.complete ? <CheckCircle2 size={18} className="mt-0.5 text-emerald-600 dark:text-emerald-400" /> : <Circle size={18} className="mt-0.5 text-slate-300 dark:text-slate-600" />}<span><span className="block text-sm font-semibold">{item.title}</span><span className="mt-1 block text-xs leading-5 text-slate-500">{item.detail}</span></span><ArrowRight size={14} className="mt-1 text-slate-400 transition group-hover:translate-x-0.5 group-hover:text-[var(--primary)]" /></Link>)}</div>
    </section>
  )
}

function AssistantPanel() {
  return (
    <aside className="assistant-panel flex flex-col p-5 sm:p-6">
      <div className="flex items-center gap-2 text-[11px] font-bold uppercase tracking-[.14em] text-blue-700 dark:text-blue-300"><Sparkles size={15} />Contextual assistant</div>
      <h2 className="mt-4 text-xl font-semibold tracking-[-.025em]">Ask from anywhere</h2>
      <p className="mt-2 text-sm leading-6 text-[var(--text-secondary)]">Get guidance grounded in the resume, matches, and interview evidence saved in your private workspace.</p>
      <div className="mt-5 space-y-2"><p className="assistant-prompt">Which project best proves my readiness?</p><p className="assistant-prompt">What should I practise before applying?</p></div>
      <Link to="/career-assistant" className="button-primary mt-6 gap-2 self-start"><MessageSquareText size={15} />Start a conversation</Link>
    </aside>
  )
}

export default function DashboardPage() {
  const { user } = useAuth()
  const { analytics, error, isLoading, refresh } = useCareerAnalytics()

  if (isLoading) return <DashboardSkeleton />
  if (!analytics) return <div className="surface-panel mx-auto max-w-3xl p-8 text-center"><AlertCircle className="mx-auto text-rose-500" /><h1 className="mt-4 font-semibold">Overview unavailable</h1><p className="mt-2 text-sm text-slate-500">{error}</p><button type="button" onClick={refresh} className="button-secondary mt-5 gap-2"><RefreshCw size={15} />Retry</button></div>

  const firstName = user.full_name.split(' ')[0]
  const resumeSamples = analytics.latest_resume_score.sample_size
  const jobSamples = analytics.average_job_match.sample_size
  const interviewSamples = analytics.interview_average_score.sample_size

  return (
    <motion.div className="mx-auto max-w-[1180px]" variants={container} initial="hidden" animate="visible">
      <motion.header variants={section} className="flex flex-col justify-between gap-5 sm:flex-row sm:items-end"><div><div className="page-kicker">{new Date().toLocaleDateString(undefined, { weekday: 'long', day: 'numeric', month: 'long' })}</div><h1 className="page-title">{getGreeting()}, {firstName}</h1><p className="page-copy">Your workspace is organized around the career evidence you have created.</p></div><BackendStatus /></motion.header>

      <motion.div variants={section} className="mt-7"><NextActions actions={analytics.next_actions} /></motion.div>

      <motion.section variants={section} className="mt-4 grid gap-4 sm:grid-cols-2 xl:grid-cols-4" aria-label="Career summary metrics">
        <AnalyticsMetricCard label="Resume readiness" value={analytics.latest_resume_score.value} suffix="/100" description={resumeSamples ? `Latest of ${resumeSamples} saved ${resumeSamples === 1 ? 'analysis' : 'analyses'}` : 'No resume analysis completed yet'} accent />
        <AnalyticsMetricCard label="Job analyses" value={analytics.job_analyses_completed} description={analytics.job_analyses_completed ? 'Saved job-to-resume comparisons' : 'No job descriptions analyzed yet'} />
        <AnalyticsMetricCard label="Average job match" value={analytics.average_job_match.value} suffix="/100" description={jobSamples ? `Across ${jobSamples} saved ${jobSamples === 1 ? 'comparison' : 'comparisons'}` : 'Available after your first job analysis'} />
        <AnalyticsMetricCard label="Interview performance" value={analytics.interview_average_score.value} suffix="/100" description={interviewSamples ? `${analytics.interviews_completed} completed ${analytics.interviews_completed === 1 ? 'interview' : 'interviews'}` : 'No completed interview sessions yet'} />
      </motion.section>

      <motion.section variants={section} className="mt-4 grid items-stretch gap-4 xl:grid-cols-[minmax(0,1.45fr)_minmax(320px,.75fr)]"><EvidenceTimeline analytics={analytics} /><AssistantPanel /></motion.section>

      <motion.section variants={section} className="mt-9"><div className="mb-4 flex items-end justify-between gap-4"><div><h2 className="text-base font-semibold">Recent workspace activity</h2><p className="mt-1 text-xs text-slate-500">Details from your saved resume, matches, and interview sessions.</p></div><Link to="/analytics" className="hidden items-center gap-1.5 text-xs font-semibold text-[var(--primary)] sm:flex">View progress<ArrowRight size={13} /></Link></div><WorkspaceSummary /></motion.section>

      <motion.p variants={section} className="mt-4 text-right text-[11px] text-slate-500">Updated from stored SkillSync data at {new Date(analytics.generated_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}</motion.p>
    </motion.div>
  )
}
