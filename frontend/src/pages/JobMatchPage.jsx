import { AnimatePresence, motion } from 'framer-motion'
import { AlertCircle, ArrowRight, BriefcaseBusiness, Clock3, FileText, RefreshCw, Search, Sparkles } from 'lucide-react'
import { useCallback, useEffect, useRef, useState } from 'react'
import { Link } from 'react-router-dom'
import JobMatchResult from '../components/jobs/JobMatchResult'
import JobMatchSkeleton from '../components/jobs/JobMatchSkeleton'
import PageHeader from '../components/ui/PageHeader'
import { getApiErrorMessage } from '../services/api'
import { analyzeJobDescription, getJobMatches } from '../services/jobMatchService'

const MIN_LENGTH = 200
const MAX_LENGTH = 20_000

function MatchHistory({ items, selectedId, isLoading, onSelect, disabled }) {
  return (
    <fieldset disabled={disabled} aria-label="Previous job analyses" className="min-w-0 rounded-2xl border bg-[#fdfdff] p-4 disabled:opacity-60 dark:bg-slate-900 lg:sticky lg:top-20">
      <div className="flex items-center gap-2 px-1"><Clock3 size={15} className="text-slate-400" /><h2 className="text-sm font-semibold">Previous analyses</h2></div>
      {isLoading ? <div className="mt-4 space-y-2"><div className="h-16 animate-pulse rounded-xl bg-slate-100 dark:bg-slate-800" /><div className="h-16 animate-pulse rounded-xl bg-slate-100 dark:bg-slate-800" /></div> : items.length ? <div className="mt-3 space-y-2">{items.map((item) => <button key={item.id} type="button" onClick={() => onSelect(item)} className={`w-full rounded-xl border px-3 py-3 text-left transition ${selectedId === item.id ? 'border-indigo-300 bg-indigo-50 dark:border-indigo-800 dark:bg-indigo-950/40' : 'hover:bg-slate-50 dark:hover:bg-slate-800'}`}><span className="block truncate text-sm font-semibold">{item.job_title || 'Untitled role'}</span><span className="mt-1 flex items-center justify-between gap-2 text-xs text-slate-500"><span>{new Date(item.created_at).toLocaleDateString()}</span><strong className="text-slate-700 dark:text-slate-200">{item.result.overall_score}/100</strong></span></button>)}</div> : <p className="mt-4 px-1 text-sm leading-6 text-slate-400">Your saved job comparisons will appear here.</p>}
    </fieldset>
  )
}

export default function JobMatchPage() {
  const textareaRef = useRef(null)
  const [description, setDescription] = useState('')
  const [match, setMatch] = useState(null)
  const [history, setHistory] = useState([])
  const [isLoadingHistory, setIsLoadingHistory] = useState(true)
  const [isProcessing, setIsProcessing] = useState(false)
  const [error, setError] = useState('')
  const [needsResume, setNeedsResume] = useState(false)
  const [retryRefresh, setRetryRefresh] = useState(false)
  const [retryAction, setRetryAction] = useState('')
  const [cacheNotice, setCacheNotice] = useState('')

  const loadHistory = useCallback(async () => {
    setIsLoadingHistory(true)
    setError('')
    try {
      setHistory(await getJobMatches())
      setRetryAction('')
    } catch (requestError) {
      setError(getApiErrorMessage(requestError, 'Could not load previous job analyses.'))
      setRetryAction('history')
    } finally {
      setIsLoadingHistory(false)
    }
  }, [])

  useEffect(() => { loadHistory() }, [loadHistory])

  async function handleAnalyze(refresh = false) {
    if (isProcessing || description.trim().length < MIN_LENGTH || description.length > MAX_LENGTH) return
    setIsProcessing(true)
    setError('')
    setNeedsResume(false)
    setCacheNotice('')
    setRetryRefresh(refresh)
    setRetryAction('analysis')
    try {
      const result = await analyzeJobDescription(description.trim(), refresh)
      setMatch(result)
      setRetryAction('')
      setCacheNotice(result.is_cached ? 'This job description and resume are unchanged, so the saved analysis was reused.' : '')
      setHistory((current) => [result, ...current.filter((item) => item.id !== result.id)].slice(0, 10))
    } catch (requestError) {
      if (requestError.response?.status === 409) setNeedsResume(true)
      setError(getApiErrorMessage(requestError, 'The job match could not be completed.'))
    } finally {
      setIsProcessing(false)
    }
  }

  function selectHistory(item) {
    if (isProcessing) return
    setMatch(item)
    setDescription(item.job_description)
    setError('')
    setCacheNotice('')
    setRetryAction('')
  }

  function startNewComparison() {
    setMatch(null)
    setDescription('')
    setError('')
    setCacheNotice('')
    setRetryAction('')
    requestAnimationFrame(() => textareaRef.current?.focus())
  }

  const characterCount = description.length
  const canAnalyze = description.trim().length >= MIN_LENGTH && characterCount <= MAX_LENGTH && !isProcessing

  return (
    <motion.div initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: .24 }} className="mx-auto max-w-6xl">
      <PageHeader icon={BriefcaseBusiness} kicker="Job matching" title="Compare a role with your resume" description="Paste the complete job description to identify requirements, evidence, and the gaps that matter most." action={match && !isProcessing ? <button type="button" onClick={startNewComparison} className="button-secondary">New comparison</button> : null} />

      {error && <div role="alert" className="mt-6 flex items-start gap-3 rounded-xl border border-rose-200 bg-rose-50 p-4 text-sm text-rose-700 dark:border-rose-900 dark:bg-rose-950/40 dark:text-rose-300"><AlertCircle size={18} className="mt-0.5 shrink-0" /><div className="flex-1"><p>{error}</p>{needsResume ? <Link to="/resume" className="mt-2 inline-flex items-center gap-1 font-semibold">Open resume workspace <ArrowRight size={14} /></Link> : <button type="button" onClick={() => retryAction === 'history' ? loadHistory() : handleAnalyze(retryRefresh)} className="mt-2 inline-flex items-center gap-1 font-semibold"><RefreshCw size={14} />Retry</button>}</div></div>}
      {cacheNotice && <div role="status" className="mt-6 rounded-xl border border-indigo-200 bg-indigo-50 px-4 py-3 text-sm text-indigo-700 dark:border-indigo-900 dark:bg-indigo-950/40 dark:text-indigo-300">{cacheNotice}</div>}

      <div className="mt-8 grid items-start gap-5 lg:grid-cols-[minmax(0,1fr)_280px]">
        <section className="surface-panel p-5 sm:p-6">
          <div className="flex items-center gap-2.5"><FileText size={17} className="text-indigo-600 dark:text-indigo-400" /><h2 className="font-semibold">Job description</h2></div>
          <label htmlFor="job-description" className="sr-only">Job description</label>
          <textarea ref={textareaRef} id="job-description" value={description} onChange={(event) => setDescription(event.target.value.slice(0, MAX_LENGTH))} disabled={isProcessing} placeholder="Paste the complete job description, including responsibilities, required skills, qualifications, and preferred experience…" className="mt-4 min-h-72 w-full resize-y rounded-xl border bg-[#fafaff] p-4 text-sm leading-6 outline-none transition placeholder:text-slate-400 focus:border-indigo-500 focus:ring-2 focus:ring-indigo-500/15 disabled:cursor-wait disabled:opacity-70 dark:bg-slate-950" />
          <div className="mt-2 flex flex-col gap-2 text-xs sm:flex-row sm:items-center sm:justify-between"><p className={characterCount > 0 && characterCount < MIN_LENGTH ? 'text-amber-600 dark:text-amber-400' : 'text-slate-400'}>{characterCount < MIN_LENGTH ? `${MIN_LENGTH - characterCount} more characters needed` : 'Ready to analyze'}</p><span className="tabular-nums text-slate-400">{characterCount.toLocaleString()} / {MAX_LENGTH.toLocaleString()}</span></div>
          <div className="mt-5 flex flex-col gap-3 border-t pt-5 sm:flex-row sm:items-center sm:justify-between"><p className="max-w-md text-xs leading-5 text-slate-500">Analysis is saved automatically. An unchanged job and resume reuse the saved result.</p><button type="button" disabled={!canAnalyze} onClick={() => handleAnalyze(false)} className="button-primary shrink-0 gap-2 disabled:cursor-not-allowed disabled:opacity-50"><Search size={16} />{isProcessing ? 'Analyzing…' : 'Analyze and save'}</button></div>
        </section>
        <MatchHistory items={history} selectedId={match?.id} isLoading={isLoadingHistory} onSelect={selectHistory} disabled={isProcessing} />
      </div>

      <div className="mt-7">
        <AnimatePresence mode="wait">{isProcessing ? <motion.div key="loading" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}><JobMatchSkeleton /></motion.div> : match ? <motion.div key={match.id} initial={{ opacity: 0 }} animate={{ opacity: 1 }}><JobMatchResult match={match} /></motion.div> : <motion.section key="empty" initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="rounded-2xl border border-dashed bg-[#f8f7fc] p-8 text-center dark:bg-slate-900/40"><span className="mx-auto grid h-11 w-11 place-items-center rounded-xl bg-[#ebeafe] text-indigo-600 dark:bg-indigo-950 dark:text-indigo-300"><Sparkles size={19} /></span><h2 className="mt-4 font-semibold">Your comparison will appear here</h2><p className="mx-auto mt-2 max-w-lg text-sm leading-6 text-slate-500">The result will prioritize required-skill gaps, then show the complete scoring evidence and recommendations.</p></motion.section>}</AnimatePresence>
      </div>
      {match && <p className="mt-4 text-right text-xs text-slate-400">Saved {new Date(match.created_at).toLocaleString()} · {match.model} + {match.embedding_model} · Scoring {match.scoring_version}</p>}
    </motion.div>
  )
}
