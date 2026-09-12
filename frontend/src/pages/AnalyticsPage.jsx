import { motion } from 'framer-motion'
import { AlertCircle, BarChart3, RefreshCw } from 'lucide-react'
import AnalyticsMetricCard from '../components/dashboard/AnalyticsMetricCard'
import ScoreTrendChart from '../components/dashboard/ScoreTrendChart'
import SkillInsights from '../components/dashboard/SkillInsights'
import PageHeader from '../components/ui/PageHeader'
import useCareerAnalytics from '../hooks/useCareerAnalytics'

function AnalyticsSkeleton() {
  return <div className="page-shell animate-pulse"><div className="h-24 max-w-xl rounded-xl bg-[var(--surface-subtle)]" /><div className="mt-8 grid gap-4 sm:grid-cols-2 xl:grid-cols-4">{Array.from({ length: 4 }).map((_, index) => <div key={index} className="h-28 rounded-xl bg-[var(--surface-subtle)]" />)}</div><div className="mt-7 grid gap-4 lg:grid-cols-2"><div className="h-64 rounded-xl bg-[var(--surface-subtle)]" /><div className="h-64 rounded-xl bg-[var(--surface-subtle)]" /></div></div>
}

export default function AnalyticsPage() {
  const { analytics, error, isLoading, refresh } = useCareerAnalytics()

  if (isLoading) return <AnalyticsSkeleton />
  if (!analytics) return <div className="surface-panel mx-auto max-w-3xl p-8 text-center"><AlertCircle className="mx-auto text-rose-500" /><h1 className="mt-4 font-semibold">Analytics unavailable</h1><p className="mt-2 text-sm text-slate-500">{error}</p><button type="button" onClick={refresh} className="button-secondary mt-5 gap-2"><RefreshCw size={15} />Retry</button></div>

  const resumeSamples = analytics.latest_resume_score.sample_size
  const jobSamples = analytics.average_job_match.sample_size
  const interviewSamples = analytics.interview_average_score.sample_size

  return (
    <motion.div className="page-shell" initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.24 }}>
      <PageHeader icon={BarChart3} kicker="Stored evidence" title="Career analytics" description="Track trends created by your saved resume analyses, job comparisons, and completed practice interviews." action={<button type="button" onClick={refresh} className="button-secondary gap-2"><RefreshCw size={15} />Refresh</button>} />

      <section className="mt-8 grid gap-4 sm:grid-cols-2 xl:grid-cols-4" aria-label="Career analytics summary">
        <AnalyticsMetricCard label="Resume readiness" value={analytics.latest_resume_score.value} suffix="/100" description={resumeSamples ? `Latest of ${resumeSamples} saved ${resumeSamples === 1 ? 'analysis' : 'analyses'}` : 'No resume analysis completed yet'} accent />
        <AnalyticsMetricCard label="Job analyses" value={analytics.job_analyses_completed} description={analytics.job_analyses_completed ? 'Saved resume-to-role comparisons' : 'No job comparisons completed yet'} />
        <AnalyticsMetricCard label="Average job match" value={analytics.average_job_match.value} suffix="/100" description={jobSamples ? `Across ${jobSamples} saved ${jobSamples === 1 ? 'comparison' : 'comparisons'}` : 'Available after your first comparison'} />
        <AnalyticsMetricCard label="Interview performance" value={analytics.interview_average_score.value} suffix="/100" description={interviewSamples ? `${analytics.interviews_completed} completed ${analytics.interviews_completed === 1 ? 'interview' : 'interviews'}` : 'No completed interviews yet'} />
      </section>

      <section className="mt-8"><h2 className="font-semibold">Progress over time</h2><p className="mt-1 text-xs text-slate-500">Only saved scores are plotted; two results are required to show a trend.</p><div className="mt-4 grid gap-4 lg:grid-cols-2"><ScoreTrendChart title="Resume-readiness trend" points={analytics.resume_score_trend} emptyText="Run another resume analysis after meaningful changes to compare readiness." /><ScoreTrendChart title="Interview performance trend" points={analytics.interview_performance_trend} emptyText="Complete at least two mock interviews to compare performance." /></div></section>
      <section className="mt-8"><h2 className="font-semibold">Skill signals</h2><p className="mt-1 text-xs text-slate-500">Evidence comes from your parsed resume and saved job-match results.</p><SkillInsights strengths={analytics.strongest_skills} missing={analytics.common_missing_skills} /></section>
      <p className="mt-4 text-right text-[11px] text-slate-500">Generated from stored SkillSync data at {new Date(analytics.generated_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}</p>
    </motion.div>
  )
}
