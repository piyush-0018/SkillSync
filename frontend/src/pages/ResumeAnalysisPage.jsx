import { AnimatePresence, motion } from 'framer-motion'
import { AlertCircle, ArrowRight, Clock3, RefreshCw, ScanSearch, Sparkles } from 'lucide-react'
import { useCallback, useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import AnalysisSkeleton from '../components/analysis/AnalysisSkeleton'
import ResumeAnalysisResult from '../components/analysis/ResumeAnalysisResult'
import PageHeader from '../components/ui/PageHeader'
import { getApiErrorMessage } from '../services/api'
import { getLatestResumeAnalysis, getResumeAnalysisHistory, runResumeAnalysis } from '../services/resumeAnalysisService'

function EmptyAnalysis({ needsResume, onAnalyze }) {
  return (
    <section className="rounded-3xl border border-dashed bg-[#f8f7fc] p-8 text-center dark:bg-slate-900/40 sm:p-12">
      <span className="mx-auto grid h-12 w-12 place-items-center rounded-xl bg-[#ebeafe] text-indigo-600 dark:bg-indigo-950 dark:text-indigo-300"><ScanSearch size={21} /></span>
      <h2 className="mt-5 text-lg font-semibold">{needsResume ? 'A parsed resume is required' : 'Your resume is ready to analyze'}</h2>
      <p className="mx-auto mt-2 max-w-lg text-sm leading-6 text-slate-500">{needsResume ? 'Upload a text-based PDF first. SkillSync needs readable resume content before it can generate feedback.' : 'SkillSync will apply its fixed 100-point rubric, then use AI to prepare practical feedback for your target role.'}</p>
      {needsResume ? <Link to="/resume" className="button-primary mt-6 gap-2">Open resume workspace <ArrowRight size={16} /></Link> : <button type="button" onClick={() => onAnalyze(false)} className="button-primary mt-6 gap-2"><Sparkles size={16} />Analyze resume</button>}
      <p className="mx-auto mt-4 max-w-md text-xs leading-5 text-slate-400">AI-generated guidance only. This does not reproduce or represent a proprietary ATS system.</p>
    </section>
  )
}

function History({ items, selectedId, onSelect }) {
  if (!items.length) return null
  return (
    <aside className="rounded-2xl border bg-[#fdfdff] p-4 dark:bg-slate-900">
      <div className="flex items-center gap-2 px-1"><Clock3 size={15} className="text-slate-400" /><h2 className="text-sm font-semibold">Previous analyses</h2></div>
      <div className="mt-3 flex gap-2 overflow-x-auto pb-1">
        {items.map((item, index) => <button key={item.id} type="button" onClick={() => onSelect(item)} className={`min-w-40 rounded-xl border px-3 py-2.5 text-left transition ${selectedId === item.id ? 'border-indigo-300 bg-indigo-50 dark:border-indigo-800 dark:bg-indigo-950/40' : 'hover:bg-slate-50 dark:hover:bg-slate-800'}`}><span className="block text-xs font-semibold">{index === 0 ? 'Latest' : new Date(item.created_at).toLocaleDateString()}</span><span className="mt-1 block text-xs text-slate-500">Score {item.overall_score}/100 · {new Date(item.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}</span></button>)}
      </div>
    </aside>
  )
}

export default function ResumeAnalysisPage() {
  const [analysis, setAnalysis] = useState(null)
  const [history, setHistory] = useState([])
  const [isLoading, setIsLoading] = useState(true)
  const [isProcessing, setIsProcessing] = useState(false)
  const [needsResume, setNeedsResume] = useState(false)
  const [error, setError] = useState('')
  const [cacheNotice, setCacheNotice] = useState('')
  const [retryAction, setRetryAction] = useState('')

  const loadAnalysis = useCallback(async () => {
    setIsLoading(true)
    setError('')
    setRetryAction('')
    setNeedsResume(false)
    try {
      const [latest, previous] = await Promise.all([getLatestResumeAnalysis(), getResumeAnalysisHistory()])
      setAnalysis(latest)
      setHistory(previous)
    } catch (requestError) {
      if (requestError.response?.status === 409) setNeedsResume(true)
      else {
        setError(getApiErrorMessage(requestError, 'Could not load resume analysis.'))
        setRetryAction('load')
      }
    } finally {
      setIsLoading(false)
    }
  }, [])

  useEffect(() => { loadAnalysis() }, [loadAnalysis])

  async function handleAnalyze(refresh) {
    if (isProcessing || isLoading) return
    setIsProcessing(true)
    setError('')
    setCacheNotice('')
    setRetryAction('')
    try {
      const result = await runResumeAnalysis(refresh)
      setAnalysis(result)
      setNeedsResume(false)
      setCacheNotice(result.is_cached ? 'Your resume has not changed, so the saved analysis was reused.' : '')
      setHistory((current) => [result, ...current.filter((item) => item.id !== result.id)].slice(0, 10))
    } catch (requestError) {
      if (requestError.response?.status === 409) {
        setNeedsResume(true)
        setAnalysis(null)
        setHistory([])
      }
      setError(getApiErrorMessage(requestError, 'The analysis could not be completed.'))
      setRetryAction(refresh ? 'refresh' : 'analyze')
    } finally {
      setIsProcessing(false)
    }
  }

  return (
    <motion.div initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: .24 }} className="mx-auto max-w-6xl">
      <PageHeader icon={Sparkles} kicker="AI resume analysis" title="Resume readiness" description="A transparent rubric scores your resume while AI turns the evidence into focused career feedback." action={analysis && !isProcessing ? <button type="button" onClick={() => handleAnalyze(true)} className="button-secondary gap-2"><RefreshCw size={15} />Run new analysis</button> : null} />

      {error && <div role="alert" className="mt-6 flex items-start gap-3 rounded-xl border border-rose-200 bg-rose-50 p-4 text-sm text-rose-700 dark:border-rose-900 dark:bg-rose-950/40 dark:text-rose-300"><AlertCircle size={18} className="mt-0.5 shrink-0" /><div className="flex-1"><p>{error}</p>{!needsResume && retryAction && <button type="button" onClick={() => retryAction === 'load' ? loadAnalysis() : handleAnalyze(retryAction === 'refresh')} className="mt-2 inline-flex items-center gap-1 font-semibold"><RefreshCw size={14} />Retry</button>}</div></div>}
      {cacheNotice && <div role="status" className="mt-6 rounded-xl border border-indigo-200 bg-indigo-50 px-4 py-3 text-sm text-indigo-700 dark:border-indigo-900 dark:bg-indigo-950/40 dark:text-indigo-300">{cacheNotice}</div>}

      <div className="mt-8">
        <AnimatePresence mode="wait">
          {isLoading || isProcessing ? <motion.div key="loading" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}><AnalysisSkeleton processing={isProcessing} /></motion.div> : analysis ? <motion.div key={analysis.id} initial={{ opacity: 0 }} animate={{ opacity: 1 }}><ResumeAnalysisResult result={analysis} /></motion.div> : <motion.div key="empty" initial={{ opacity: 0 }} animate={{ opacity: 1 }}><EmptyAnalysis needsResume={needsResume} onAnalyze={handleAnalyze} /></motion.div>}
        </AnimatePresence>
      </div>

      {!isLoading && !isProcessing && <div className="mt-6"><History items={history} selectedId={analysis?.id} onSelect={setAnalysis} /></div>}
      {analysis && <p className="mt-4 text-right text-xs text-slate-400">Generated {new Date(analysis.created_at).toLocaleString()} · {analysis.provider} / {analysis.model} · Rubric {analysis.rubric_version}</p>}
    </motion.div>
  )
}
