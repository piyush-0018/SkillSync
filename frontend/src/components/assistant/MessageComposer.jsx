import { LoaderCircle, Send } from 'lucide-react'
import { useEffect, useRef, useState } from 'react'

const MAX_LENGTH = 2_000

export default function MessageComposer({ onSend, disabled, focusSignal }) {
  const [content, setContent] = useState('')
  const textareaRef = useRef(null)
  const trimmedContent = content.trim()
  const canSend = trimmedContent.length >= 2 && !disabled

  useEffect(() => {
    textareaRef.current?.focus()
  }, [focusSignal])

  function resizeTextarea(element) {
    element.style.height = 'auto'
    element.style.height = `${Math.min(element.scrollHeight, 144)}px`
  }

  function handleChange(event) {
    setContent(event.target.value.slice(0, MAX_LENGTH))
    resizeTextarea(event.target)
  }

  function submitMessage(event) {
    event?.preventDefault()
    if (!canSend) return
    onSend(trimmedContent)
    setContent('')
    if (textareaRef.current) textareaRef.current.style.height = 'auto'
  }

  function handleKeyDown(event) {
    if (event.key === 'Enter' && !event.shiftKey && !event.nativeEvent.isComposing) {
      event.preventDefault()
      submitMessage()
    }
  }

  return (
    <form onSubmit={submitMessage} className="border-t bg-[#fdfdff] p-3 dark:bg-slate-900 sm:p-4">
      <div className="mx-auto max-w-3xl rounded-2xl border bg-[#fafaff] p-2 shadow-sm transition focus-within:border-indigo-400 focus-within:ring-2 focus-within:ring-indigo-500/10 dark:bg-slate-950">
        <label htmlFor="career-question" className="sr-only">Ask the career assistant</label>
        <textarea ref={textareaRef} id="career-question" rows={1} maxLength={MAX_LENGTH} value={content} onChange={handleChange} onKeyDown={handleKeyDown} disabled={disabled} placeholder={disabled ? 'Waiting for SkillSync to respond…' : 'Ask about your resume, skills, projects, or target role…'} className="max-h-36 min-h-12 w-full resize-none bg-transparent px-2 py-2 text-sm leading-6 outline-none placeholder:text-slate-400 disabled:cursor-wait disabled:opacity-70" />
        <div className="flex items-center justify-between gap-3 px-1 pb-1">
          <p className="text-[11px] text-slate-400">Enter to send · Shift + Enter for a new line</p>
          <div className="flex items-center gap-3">
            {content.length >= 1_600 && <span className="text-[11px] tabular-nums text-slate-400">{content.length.toLocaleString()} / {MAX_LENGTH.toLocaleString()}</span>}
            <button type="submit" disabled={!canSend} className="button-primary h-9 gap-2 px-3 disabled:cursor-not-allowed disabled:opacity-50" aria-label={disabled ? 'Waiting for response' : 'Send message'}>{disabled ? <LoaderCircle size={15} className="animate-spin" /> : <Send size={15} />}<span className="hidden sm:inline">Send</span></button>
          </div>
        </div>
      </div>
    </form>
  )
}
