import { AnimatePresence, motion } from 'framer-motion'
import { MessageSquareText, Plus, X } from 'lucide-react'
import { useRef } from 'react'
import useMobileDialog from '../../hooks/useMobileDialog'

function formatDate(value) {
  if (!value) return 'Recently'
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) return 'Recently'
  return date.toLocaleDateString(undefined, { month: 'short', day: 'numeric' })
}

function ConversationPanel({ conversations, activeId, isLoading, disabled, onSelect, onNew, onClose, mobile = false }) {
  return (
    <div className="flex h-full min-h-0 flex-col">
      <div className="flex items-center justify-between gap-3 border-b px-4 py-4">
        <div>
          <p className="text-sm font-semibold">Conversations</p>
          <p className="mt-0.5 text-xs text-slate-400">Your recent questions</p>
        </div>
        {mobile && <button type="button" onClick={onClose} className="grid h-8 w-8 place-items-center rounded-lg text-slate-500 transition hover:bg-slate-100 dark:hover:bg-slate-800" aria-label="Close conversations"><X size={17} /></button>}
      </div>

      <div className="p-3">
        <button type="button" onClick={onNew} disabled={disabled} className="button-secondary w-full gap-2 disabled:cursor-not-allowed disabled:opacity-50"><Plus size={16} />New conversation</button>
      </div>

      <nav className="min-h-0 flex-1 overflow-y-auto px-3 pb-4" aria-label="Career assistant conversations">
        {isLoading ? (
          <div className="space-y-2" aria-label="Loading conversations">
            {[0, 1, 2].map((item) => <div key={item} className="h-16 animate-pulse rounded-xl bg-slate-100 dark:bg-slate-800" />)}
          </div>
        ) : conversations.length ? (
          <div className="space-y-1.5">
            {conversations.map((conversation) => {
              const isActive = conversation.id === activeId
              return (
                <button key={conversation.id} type="button" disabled={disabled} onClick={() => onSelect(conversation.id)} aria-current={isActive ? 'page' : undefined} className={`w-full rounded-xl px-3 py-3 text-left transition disabled:cursor-not-allowed disabled:opacity-60 ${isActive ? 'bg-indigo-50 text-indigo-800 dark:bg-indigo-950/50 dark:text-indigo-200' : 'text-slate-600 hover:bg-slate-100 dark:text-slate-300 dark:hover:bg-slate-800'}`}>
                  <span className="block truncate text-sm font-medium">{conversation.title || 'Career conversation'}</span>
                  <span className="mt-1 block text-xs text-slate-400">{formatDate(conversation.updated_at || conversation.created_at)}</span>
                </button>
              )
            })}
          </div>
        ) : (
          <div className="px-3 py-8 text-center">
            <MessageSquareText size={20} className="mx-auto text-slate-300 dark:text-slate-700" />
            <p className="mt-3 text-xs leading-5 text-slate-400">Your saved conversations will appear here.</p>
          </div>
        )}
      </nav>
    </div>
  )
}

export default function ConversationList(props) {
  const { mobileOpen, onClose } = props

  const panelRef = useRef(null)
  useMobileDialog(panelRef, mobileOpen, onClose)

  return (
    <>
      <aside className="hidden min-h-0 border-r bg-[#fafaff] dark:bg-slate-950/40 lg:block">
        <ConversationPanel {...props} />
      </aside>

      <AnimatePresence>
        {mobileOpen && (
          <motion.div className="absolute inset-0 z-30 lg:hidden" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}>
            <button type="button" className="absolute inset-0 bg-slate-950/35" onClick={onClose} aria-label="Close conversations" />
            <motion.aside ref={panelRef} role="dialog" aria-modal="true" aria-label="Career assistant conversations" initial={{ x: -24 }} animate={{ x: 0 }} exit={{ x: -24 }} transition={{ duration: 0.18 }} className="absolute inset-y-0 left-0 w-[min(84vw,20rem)] border-r bg-[#fafaff] shadow-2xl dark:bg-slate-950">
              <ConversationPanel {...props} mobile />
            </motion.aside>
          </motion.div>
        )}
      </AnimatePresence>
    </>
  )
}
