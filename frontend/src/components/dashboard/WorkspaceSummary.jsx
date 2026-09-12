import { AlertCircle, ArrowRight, BriefcaseBusiness, FileText, MessageSquareText, RefreshCw } from 'lucide-react'
import { useCallback, useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { getApiErrorMessage } from '../../services/api'
import { getInterviews } from '../../services/interviewService'
import { getJobMatches } from '../../services/jobMatchService'
import { getResume } from '../../services/resumeService'

function SummarySkeleton() {
  return <div className="grid gap-4 lg:grid-cols-3">{Array.from({ length: 3 }).map((_, index) => <div key={index} className="h-52 animate-pulse rounded-xl bg-[var(--surface-subtle)]" />)}</div>
}

function SummaryCard({ icon: Icon, title, action, children }) {
  return <article className="surface-panel flex min-h-52 flex-col p-5"><div className="flex items-center gap-2"><Icon size={17} className="text-blue-700 dark:text-blue-300" /><h3 className="text-sm font-semibold">{title}</h3></div><div className="flex-1 py-5">{children}</div><Link to={action.to} className="inline-flex items-center gap-1.5 text-xs font-semibold text-blue-700 dark:text-blue-300">{action.label}<ArrowRight size={13} /></Link></article>
}

function EmptySummary({ children }) {
  return <p className="text-sm leading-6 text-slate-500">{children}</p>
}

export default function WorkspaceSummary() {
  const [data, setData] = useState(null)
  const [error, setError] = useState('')
  const [isLoading, setIsLoading] = useState(true)

  const load = useCallback(async () => {
    setIsLoading(true)
    setError('')
    try {
      const [resume, jobMatches, interviews] = await Promise.all([getResume(), getJobMatches(), getInterviews()])
      setData({ resume, latestJob: jobMatches[0] || null, latestInterview: interviews[0] || null })
    } catch (requestError) {
      setError(getApiErrorMessage(requestError, 'Could not load your recent workspace activity.'))
    } finally {
      setIsLoading(false)
    }
  }, [])

  useEffect(() => { load() }, [load])

  if (isLoading) return <SummarySkeleton />
  if (!data) return <div className="surface-subtle flex flex-col items-start gap-4 p-5 sm:flex-row sm:items-center sm:justify-between"><div className="flex gap-3"><AlertCircle size={18} className="mt-0.5 shrink-0 text-rose-600" /><div><h3 className="text-sm font-semibold">Recent activity unavailable</h3><p className="mt-1 text-xs text-slate-500">{error}</p></div></div><button type="button" onClick={load} className="button-secondary shrink-0 gap-2"><RefreshCw size={14} />Retry</button></div>

  const { resume, latestJob, latestInterview } = data
  return (
    <div className="grid gap-4 lg:grid-cols-3">
      <SummaryCard icon={FileText} title="Resume" action={{ to: resume ? '/resume/analysis' : '/resume', label: resume ? 'Review analysis' : 'Upload resume' }}>
        {resume ? <><p className="truncate text-sm font-semibold">{resume.original_filename}</p><p className="mt-2 text-xs capitalize text-slate-500">{resume.parsing_status} · Uploaded {new Date(resume.uploaded_at).toLocaleDateString()}</p><p className="mt-4 text-xs leading-5 text-slate-500">{resume.parsing_status === 'parsed' ? `${resume.structured_data.technical_skills.length} technical skills extracted from the current file.` : 'Parsing did not complete. Replace the file to try again.'}</p></> : <EmptySummary>Upload your resume to start analyzing your career profile.</EmptySummary>}
      </SummaryCard>
      <SummaryCard icon={BriefcaseBusiness} title="Latest job match" action={{ to: '/job-match', label: latestJob ? 'Analyze another role' : 'Compare a job' }}>
        {latestJob ? <><p className="truncate text-sm font-semibold">{latestJob.job_title || 'Saved role comparison'}</p><p className="data-value mt-2 text-2xl font-semibold">{latestJob.result.overall_score}<span className="text-xs font-medium text-slate-500">/100 compatibility</span></p><p className="mt-4 text-xs leading-5 text-slate-500">{latestJob.result.missing_required_skills.length ? `${latestJob.result.missing_required_skills.length} required skill ${latestJob.result.missing_required_skills.length === 1 ? 'gap' : 'gaps'} identified.` : 'No missing required skills were identified.'}</p></> : <EmptySummary>Compare your resume with a job description to see where you stand.</EmptySummary>}
      </SummaryCard>
      <SummaryCard icon={MessageSquareText} title="Interview practice" action={{ to: '/interviews', label: latestInterview ? 'View interview history' : 'Start practising' }}>
        {latestInterview ? <><p className="truncate text-sm font-semibold">{latestInterview.target_role}</p><p className="mt-2 text-xs capitalize text-slate-500">{latestInterview.difficulty} · {latestInterview.interview_type.replace('_', ' ')}</p><p className="data-value mt-4 text-2xl font-semibold">{latestInterview.overall_score == null ? `${latestInterview.answered_count}/${latestInterview.question_limit}` : Math.round(latestInterview.overall_score)}<span className="text-xs font-medium text-slate-500">{latestInterview.overall_score == null ? ' answered' : '/100 practice score'}</span></p></> : <EmptySummary>Practice a mock interview and track your progress here.</EmptySummary>}
      </SummaryCard>
    </div>
  )
}
