import { AnimatePresence, motion } from 'framer-motion'
import { Bot, Menu, MessageSquarePlus, RefreshCw, Sparkles, Trash2, X } from 'lucide-react'
import { useCallback, useEffect, useRef, useState } from 'react'
import ChatMessage from '../components/assistant/ChatMessage'
import ConversationList from '../components/assistant/ConversationList'
import MessageComposer from '../components/assistant/MessageComposer'
import { getApiErrorMessage } from '../services/api'
import {
  deleteAssistantConversation,
  getAssistantConversation,
  getAssistantConversations,
  sendAssistantMessage,
} from '../services/careerAssistantService'

const suggestedQuestions = [
  'What skills am I missing for backend roles?',
  'Which of my projects should I highlight?',
  'How can I improve my resume?',
  'Am I ready for an AI engineer role?',
  'What should I learn next?',
]

function EmptyConversation({ onQuestion, disabled }) {
  return (
    <div className="mx-auto flex min-h-full max-w-2xl flex-col items-center justify-center px-5 py-12 text-center">
      <span className="grid h-12 w-12 place-items-center rounded-2xl bg-[#ebeafe] text-indigo-600 dark:bg-indigo-950 dark:text-indigo-300"><Sparkles size={21} /></span>
      <h2 className="mt-5 text-xl font-semibold tracking-tight">Guidance grounded in your progress</h2>
      <p className="mt-2 max-w-lg text-sm leading-6 text-slate-500">SkillSync retrieves relevant details from your resume, analyses, saved job matches, and career goal before answering.</p>
      <div className="mt-7 flex flex-wrap justify-center gap-2.5">
        {suggestedQuestions.map((question) => (
          <button key={question} type="button" disabled={disabled} onClick={() => onQuestion(question)} className="rounded-xl border bg-[#fdfdff] px-3.5 py-2.5 text-left text-xs font-medium text-slate-600 transition hover:-translate-y-0.5 hover:border-indigo-300 hover:text-indigo-700 disabled:opacity-50 dark:bg-slate-900 dark:text-slate-300 dark:hover:border-indigo-800 dark:hover:text-indigo-300">
            {question}
          </button>
        ))}
      </div>
    </div>
  )
}

function LoadingConversation() {
  return (
    <div className="mx-auto max-w-3xl space-y-8 px-5 py-8" aria-label="Loading conversation">
      <div className="ml-auto h-14 w-2/3 animate-pulse rounded-2xl bg-slate-100 dark:bg-slate-800" />
      <div className="flex gap-3"><div className="h-8 w-8 animate-pulse rounded-lg bg-indigo-100 dark:bg-indigo-950" /><div className="h-28 w-4/5 animate-pulse rounded-2xl bg-slate-100 dark:bg-slate-800" /></div>
    </div>
  )
}

function ProcessingMessage() {
  return (
    <motion.div initial={{ opacity: 0, y: 6 }} animate={{ opacity: 1, y: 0 }} className="flex items-start gap-3" role="status" aria-live="polite">
      <span className="grid h-8 w-8 shrink-0 place-items-center rounded-lg bg-[#ebeafe] text-indigo-600 dark:bg-indigo-950 dark:text-indigo-300"><Bot size={16} /></span>
      <div className="rounded-2xl border bg-[#fafaff] px-4 py-3 dark:bg-slate-950">
        <div className="flex items-center gap-2 text-sm font-medium"><span className="h-2 w-2 animate-pulse rounded-full bg-indigo-500" />Retrieving your SkillSync context</div>
        <p className="mt-1 text-xs text-slate-500">Local AI can take a few minutes on the first response.</p>
      </div>
    </motion.div>
  )
}

export default function CareerAssistantPage() {
  const [conversations, setConversations] = useState([])
  const [activeConversation, setActiveConversation] = useState(null)
  const [messages, setMessages] = useState([])
  const [isLoading, setIsLoading] = useState(true)
  const [isConversationLoading, setIsConversationLoading] = useState(false)
  const [isSending, setIsSending] = useState(false)
  const [isClearing, setIsClearing] = useState(false)
  const [confirmClear, setConfirmClear] = useState(false)
  const [mobileOpen, setMobileOpen] = useState(false)
  const [error, setError] = useState('')
  const [failedQuestion, setFailedQuestion] = useState('')
  const [focusSignal, setFocusSignal] = useState(0)
  const endRef = useRef(null)
  const latestResponseRef = useRef(null)
  const conversationRequest = useRef(0)
  const closeConversations = useCallback(() => setMobileOpen(false), [])
  const busy = isLoading || isSending || isConversationLoading || isClearing

  useEffect(() => {
    let cancelled = false
    async function loadWorkspace() {
      try {
        const items = await getAssistantConversations()
        if (cancelled) return
        setConversations(items)
        if (items.length) {
          const detail = await getAssistantConversation(items[0].id)
          if (!cancelled) {
            setActiveConversation(detail.conversation)
            setMessages(detail.messages)
          }
        }
      } catch (requestError) {
        if (!cancelled) setError(getApiErrorMessage(requestError, 'Could not load the Career Assistant.'))
      } finally {
        if (!cancelled) setIsLoading(false)
      }
    }
    loadWorkspace()
    return () => { cancelled = true }
  }, [])

  useEffect(() => {
    const latestMessage = messages[messages.length - 1]
    if (!isSending && latestMessage?.role === 'assistant') {
      latestResponseRef.current?.scrollIntoView({ behavior: 'smooth', block: 'start' })
      return
    }
    endRef.current?.scrollIntoView({ behavior: isSending ? 'smooth' : 'auto', block: 'end' })
  }, [messages, isSending])

  async function selectConversation(conversationId) {
    if (isSending || isClearing || conversationId === activeConversation?.id) {
      setMobileOpen(false)
      return
    }
    setIsConversationLoading(true)
    setError('')
    setFailedQuestion('')
    setConfirmClear(false)
    setMobileOpen(false)
    const requestId = ++conversationRequest.current
    try {
      const detail = await getAssistantConversation(conversationId)
      if (requestId !== conversationRequest.current) return
      setActiveConversation(detail.conversation)
      setMessages(detail.messages)
    } catch (requestError) {
      if (requestId === conversationRequest.current) setError(getApiErrorMessage(requestError, 'Could not open that conversation.'))
    } finally {
      if (requestId === conversationRequest.current) setIsConversationLoading(false)
    }
  }

  function startConversation() {
    if (busy) return
    conversationRequest.current += 1
    setActiveConversation(null)
    setMessages([])
    setError('')
    setFailedQuestion('')
    setConfirmClear(false)
    setMobileOpen(false)
    setFocusSignal((value) => value + 1)
  }

  async function sendMessage(content) {
    if (busy) return
    const previousMessages = messages
    const pendingMessage = { id: `pending-${Date.now()}`, role: 'user', content }
    setMessages([...previousMessages, pendingMessage])
    setIsSending(true)
    setError('')
    setFailedQuestion('')
    setConfirmClear(false)
    try {
      const turn = await sendAssistantMessage(activeConversation?.id || null, content)
      setActiveConversation(turn.conversation)
      setMessages([...previousMessages, turn.user_message, turn.assistant_message])
      setConversations((items) => [turn.conversation, ...items.filter((item) => item.id !== turn.conversation.id)])
      setFocusSignal((value) => value + 1)
    } catch (requestError) {
      setMessages(previousMessages)
      setFailedQuestion(content)
      setError(getApiErrorMessage(requestError, 'The Career Assistant could not answer that question.'))
    } finally {
      setIsSending(false)
    }
  }

  async function clearConversation() {
    if (!activeConversation || isSending || isClearing) return
    if (!confirmClear) {
      setConfirmClear(true)
      return
    }
    setIsClearing(true)
    setError('')
    try {
      await deleteAssistantConversation(activeConversation.id)
      const remaining = conversations.filter((item) => item.id !== activeConversation.id)
      setConversations(remaining)
      setActiveConversation(null)
      setMessages([])
      setConfirmClear(false)
      setFocusSignal((value) => value + 1)
    } catch (requestError) {
      setError(getApiErrorMessage(requestError, 'Could not clear the conversation.'))
    } finally {
      setIsClearing(false)
    }
  }

  return (
    <div className="mx-auto max-w-7xl">
      <div className="mb-5 flex flex-col justify-between gap-3 sm:flex-row sm:items-end">
        <div><div className="flex items-center gap-2 text-sm font-semibold text-indigo-600 dark:text-indigo-400"><Sparkles size={15} />Career Assistant</div><h1 className="mt-2 text-2xl font-bold tracking-[-0.03em] sm:text-3xl">Ask with context</h1><p className="mt-2 max-w-2xl text-sm leading-6 text-slate-500">Personalized answers from your SkillSync workspace, with general guidance clearly identified.</p></div>
        <p className="text-xs text-slate-400">Powered by Gemini</p>
      </div>

      <section className="relative grid h-[calc(100vh-14rem)] min-h-[31rem] overflow-hidden rounded-3xl border bg-[#fdfdff] shadow-[0_24px_60px_-44px_rgba(15,23,42,.45)] dark:bg-slate-900 lg:grid-cols-[17rem_minmax(0,1fr)]">
        <ConversationList conversations={conversations} activeId={activeConversation?.id} isLoading={isLoading} disabled={busy} onSelect={selectConversation} onNew={startConversation} mobileOpen={mobileOpen} onClose={closeConversations} />

        <div className="flex min-h-0 min-w-0 flex-col">
          <header className="flex min-h-16 items-center justify-between gap-3 border-b px-4 sm:px-5">
            <div className="flex min-w-0 items-center gap-3">
              <button type="button" onClick={() => setMobileOpen(true)} className="grid h-9 w-9 shrink-0 place-items-center rounded-lg text-slate-500 transition hover:bg-slate-100 dark:hover:bg-slate-800 lg:hidden" aria-label="Open conversations"><Menu size={18} /></button>
              <div className="min-w-0"><p className="truncate text-sm font-semibold">{activeConversation?.title || 'New conversation'}</p><p className="mt-0.5 hidden text-xs text-slate-400 sm:block">Resume, analysis, job-match, and profile context</p></div>
            </div>
            <div className="flex items-center gap-2">
              {activeConversation && (confirmClear ? <><button type="button" onClick={() => setConfirmClear(false)} className="grid h-9 w-9 place-items-center rounded-lg text-slate-500 transition hover:bg-slate-100 dark:hover:bg-slate-800" aria-label="Cancel clearing conversation"><X size={16} /></button><button type="button" onClick={clearConversation} disabled={busy} className="inline-flex h-9 items-center gap-2 rounded-lg bg-rose-600 px-3 text-xs font-semibold text-white transition hover:bg-rose-700 disabled:opacity-50"><Trash2 size={14} />Confirm clear</button></> : <button type="button" onClick={clearConversation} disabled={busy} className="inline-flex h-9 items-center gap-2 rounded-lg px-3 text-xs font-semibold text-slate-500 transition hover:bg-rose-50 hover:text-rose-700 disabled:opacity-40 dark:hover:bg-rose-950/30 dark:hover:text-rose-300"><Trash2 size={14} /><span className="hidden sm:inline">Clear</span></button>)}
              <button type="button" onClick={startConversation} disabled={busy} className="grid h-9 w-9 place-items-center rounded-lg text-indigo-600 transition hover:bg-indigo-50 disabled:opacity-40 dark:text-indigo-300 dark:hover:bg-indigo-950/50" aria-label="Start new conversation"><MessageSquarePlus size={17} /></button>
            </div>
          </header>

          <div className="min-h-0 flex-1 overflow-y-auto bg-[#fcfcff] dark:bg-slate-900">
            {isLoading || isConversationLoading ? <LoadingConversation /> : messages.length === 0 && !isSending ? <EmptyConversation onQuestion={sendMessage} disabled={isSending} /> : <div className="mx-auto max-w-3xl space-y-7 px-5 py-7 sm:px-7">{messages.map((message, index) => <div key={message.id} ref={index === messages.length - 1 && message.role === 'assistant' ? latestResponseRef : null}><ChatMessage message={message} /></div>)}<AnimatePresence>{isSending && <ProcessingMessage />}</AnimatePresence><div ref={endRef} /></div>}
          </div>

          {error && <div className="border-t border-rose-200 bg-rose-50 px-4 py-3 text-sm text-rose-700 dark:border-rose-900 dark:bg-rose-950/30 dark:text-rose-300" role="alert"><div className="mx-auto flex max-w-3xl items-center justify-between gap-4"><span>{error}</span>{failedQuestion && <button type="button" onClick={() => sendMessage(failedQuestion)} disabled={isSending} className="inline-flex shrink-0 items-center gap-1.5 text-xs font-semibold"><RefreshCw size={13} />Retry</button>}</div></div>}
          <MessageComposer onSend={sendMessage} disabled={busy} focusSignal={focusSignal} />
        </div>
      </section>
      <p className="mt-3 text-center text-[11px] leading-5 text-slate-400">Personalized claims use retrieved SkillSync data. Review AI guidance before acting on it.</p>
    </div>
  )
}
