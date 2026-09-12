import { AnimatePresence, motion } from 'framer-motion'
import { BarChart3, Bot, FileSearch, FileText, LayoutDashboard, MessageSquareText, Search, Settings, Target, UserRound } from 'lucide-react'
import { useEffect, useMemo, useRef, useState } from 'react'
import { useNavigate } from 'react-router-dom'

const destinations = [
  ['Overview', 'Career analytics and next actions', '/dashboard', LayoutDashboard],
  ['Profile', 'Skills, education, and target role', '/profile', UserRound],
  ['Resume', 'Upload and manage your resume', '/resume', FileText],
  ['Resume analysis', 'Review readiness and recommendations', '/resume/analysis', FileSearch],
  ['Job match', 'Compare your profile to a role', '/job-match', Target],
  ['Career assistant', 'Ask a context-aware career question', '/career-assistant', Bot],
  ['Mock interviews', 'Start or revisit an interview', '/interviews', MessageSquareText],
  ['Analytics', 'Review trends and skill signals', '/analytics', BarChart3],
  ['Settings', 'Appearance and workspace preferences', '/settings', Settings],
]

export default function CommandPalette({ open, onClose }) {
  const navigate = useNavigate()
  const [query, setQuery] = useState('')
  const [active, setActive] = useState(0)
  const dialogRef = useRef(null)
  const searchRef = useRef(null)
  const results = useMemo(() => destinations.filter(([label, detail]) => `${label} ${detail}`.toLowerCase().includes(query.toLowerCase())), [query])
  useEffect(() => { if (open) { setQuery(''); setActive(0) } }, [open])
  useEffect(() => {
    if (!open) return undefined
    const previouslyFocused = document.activeElement
    const frame = window.requestAnimationFrame(() => searchRef.current?.focus())
    return () => {
      window.cancelAnimationFrame(frame)
      previouslyFocused?.focus?.()
    }
  }, [open])
  useEffect(() => {
    if (!open) return undefined
    function handleKey(event) {
      if (event.key === 'Escape') onClose()
      if (event.key === 'ArrowDown') { event.preventDefault(); setActive((value) => Math.max(0, Math.min(value + 1, results.length - 1))) }
      if (event.key === 'ArrowUp') { event.preventDefault(); setActive((value) => Math.max(value - 1, 0)) }
      if (event.key === 'Enter' && event.target === searchRef.current && results[active]) { event.preventDefault(); navigate(results[active][2]); onClose() }
    }
    window.addEventListener('keydown', handleKey)
    return () => window.removeEventListener('keydown', handleKey)
  }, [active, navigate, onClose, open, results])

  function keepFocusInside(event) {
    if (event.key !== 'Tab') return
    const focusable = dialogRef.current?.querySelectorAll('input:not([disabled]), button:not([disabled])')
    if (!focusable?.length) return
    const first = focusable[0]
    const last = focusable[focusable.length - 1]
    if (event.shiftKey && document.activeElement === first) {
      event.preventDefault()
      last.focus()
    } else if (!event.shiftKey && document.activeElement === last) {
      event.preventDefault()
      first.focus()
    }
  }

  return <AnimatePresence>{open && <motion.div className="fixed inset-0 z-[70] flex items-start justify-center bg-slate-950/35 px-4 pt-[12vh] backdrop-blur-sm" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} onMouseDown={onClose}>
    <motion.div ref={dialogRef} role="dialog" aria-modal="true" aria-label="Quick navigation" initial={{ opacity: 0, y: -8, scale: .985 }} animate={{ opacity: 1, y: 0, scale: 1 }} exit={{ opacity: 0, y: -5, scale: .99 }} transition={{ duration: .18 }} className="w-full max-w-xl overflow-hidden rounded-xl border bg-white shadow-[0_24px_80px_-20px_rgba(15,23,42,.35)] dark:border-[#334860] dark:bg-[#0f1c2e] dark:shadow-[0_24px_90px_-24px_rgba(37,99,235,.3)]" onKeyDown={keepFocusInside} onMouseDown={(event) => event.stopPropagation()}>
      <label className="flex items-center gap-3 border-b px-4"><Search size={18} className="text-slate-400" /><span className="sr-only">Open a SkillSync page</span><input ref={searchRef} role="combobox" aria-autocomplete="list" aria-controls="command-results" aria-expanded="true" aria-activedescendant={results[active] ? `command-option-${active}` : undefined} value={query} onChange={(event) => { setQuery(event.target.value); setActive(0) }} placeholder="Open a page…" className="h-14 flex-1 bg-transparent text-sm outline-none placeholder:text-slate-400" /><kbd className="rounded border bg-slate-50 px-1.5 py-0.5 text-[10px] text-slate-400 dark:bg-slate-800">ESC</kbd></label>
      <div id="command-results" role="listbox" aria-label="SkillSync pages" className="max-h-96 overflow-y-auto p-2"><p className="px-2 pb-2 pt-1 text-[10px] font-semibold uppercase tracking-[.14em] text-slate-400">Navigate</p>{results.map(([label, detail, to, Icon], index) => <button id={`command-option-${index}`} role="option" aria-selected={active === index} type="button" key={to} onMouseEnter={() => setActive(index)} onClick={() => { navigate(to); onClose() }} className={`flex w-full items-center gap-3 rounded-lg px-3 py-2.5 text-left transition ${active === index ? 'bg-slate-100 dark:bg-slate-800' : ''}`}><Icon size={17} className={active === index ? 'text-indigo-600 dark:text-indigo-400' : 'text-slate-400'} /><span className="min-w-0 flex-1"><span className="block text-sm font-medium">{label}</span><span className="block truncate text-xs text-slate-500">{detail}</span></span><span className="text-xs text-slate-400">↵</span></button>)}{!results.length && <p className="px-3 py-10 text-center text-sm text-slate-500">No matching destination</p>}</div>
    </motion.div>
  </motion.div>}</AnimatePresence>
}
