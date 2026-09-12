import { motion } from 'framer-motion'
import { AlertCircle, MessageSquareText, RefreshCw, ShieldCheck } from 'lucide-react'
import { useCallback, useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import InterviewHistory from '../components/interviews/InterviewHistory'
import InterviewSetupForm from '../components/interviews/InterviewSetupForm'
import PageHeader from '../components/ui/PageHeader'
import { useAuth } from '../context/AuthContext'
import { getApiErrorMessage } from '../services/api'
import { getInterviews, startInterview } from '../services/interviewService'

export default function InterviewSetupPage() {
  const { user } = useAuth()
  const navigate = useNavigate()
  const [form, setForm] = useState({
    target_role: user.target_role || '',
    difficulty: 'intermediate',
    interview_type: 'mixed',
    response_mode: 'video',
  })
  const [sessions, setSessions] = useState([])
  const [isLoading, setIsLoading] = useState(true)
  const [isStarting, setIsStarting] = useState(false)
  const [error, setError] = useState('')
  const [historyFailed, setHistoryFailed] = useState(false)

  const loadHistory = useCallback(async () => {
    setIsLoading(true)
    setHistoryFailed(false)
    try {
      setSessions(await getInterviews())
    } catch (requestError) {
      setError(getApiErrorMessage(requestError, 'Could not load interview history.'))
      setHistoryFailed(true)
    } finally {
      setIsLoading(false)
    }
  }, [])

  useEffect(() => { loadHistory() }, [loadHistory])

  function handleChange(event) {
    const { name, value } = event.target
    setForm((current) => ({ ...current, [name]: value }))
  }

  async function handleSubmit(event) {
    event.preventDefault()
    setIsStarting(true)
    setError('')
    setHistoryFailed(false)
    try {
      if (form.response_mode === 'video') {
        if (!navigator.mediaDevices?.getUserMedia || typeof MediaRecorder === 'undefined') {
          throw new Error('Video interviews are not supported in this browser. Try the latest Chrome or Edge, or choose text mode.')
        }
        const stream = await navigator.mediaDevices.getUserMedia({ video: true, audio: true })
        stream.getTracks().forEach((track) => track.stop())
      }
      const interview = await startInterview({ ...form, target_role: form.target_role.trim() })
      navigate(`/interviews/${interview.id}`)
    } catch (requestError) {
      const permissionMessage = requestError?.name === 'NotAllowedError'
        ? 'Camera and microphone access is required for a video interview. Allow access and try again, or choose text mode.'
        : ''
      const browserMessage = requestError?.isAxiosError ? '' : requestError?.message
      setError(permissionMessage || browserMessage || getApiErrorMessage(requestError, 'The interview could not be prepared.'))
    } finally {
      setIsStarting(false)
    }
  }

  return (
    <motion.div initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: .24 }} className="mx-auto max-w-6xl">
      <PageHeader icon={MessageSquareText} kicker="AI mock interview" title="Practice a realistic interview" description="Answer on camera or by text. SkillSync evaluates the substance of every response with the same visible five-part rubric." action={<div className="inline-flex w-fit items-center gap-2 rounded-lg border bg-[var(--surface-elevated)] px-3 py-2 text-xs font-medium text-slate-500"><ShieldCheck size={14} className="text-emerald-500" />Practice feedback only</div>} />
      {error && <div role="alert" className="mt-6 flex items-start gap-3 rounded-xl border border-rose-200 bg-rose-50 p-4 text-sm text-rose-700 dark:border-rose-900 dark:bg-rose-950/40 dark:text-rose-300"><AlertCircle size={18} className="mt-0.5 shrink-0" /><div className="flex-1"><p>{error}</p>{historyFailed && <button type="button" onClick={loadHistory} className="mt-2 inline-flex items-center gap-1 font-semibold"><RefreshCw size={14} />Retry history</button>}</div></div>}
      {isStarting && <div role="status" className="mt-6 rounded-xl border border-indigo-200 bg-indigo-50 px-4 py-3 text-sm text-indigo-700 dark:border-indigo-900 dark:bg-indigo-950/40 dark:text-indigo-300">Your local AI is preparing a role-specific opening question. This can take a moment on the first run.</div>}
      <div className="mt-8 grid items-start gap-6 xl:grid-cols-[minmax(0,1.35fr)_minmax(320px,.65fr)]"><InterviewSetupForm form={form} onChange={handleChange} onSubmit={handleSubmit} isStarting={isStarting} /><InterviewHistory sessions={sessions} isLoading={isLoading} /></div>
    </motion.div>
  )
}
