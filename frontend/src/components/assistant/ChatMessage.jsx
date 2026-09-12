import { motion } from 'framer-motion'
import { Bot, Database } from 'lucide-react'
import ReactMarkdown from 'react-markdown'

const groundingLabels = {
  user_data: 'Based on your SkillSync data',
  mixed: 'Your data + general guidance',
  general: 'General career guidance',
}

const markdownComponents = {
  h1: ({ children }) => <h2 className="mb-2 mt-5 text-base font-semibold first:mt-0">{children}</h2>,
  h2: ({ children }) => <h2 className="mb-2 mt-5 text-base font-semibold first:mt-0">{children}</h2>,
  h3: ({ children }) => <h3 className="mb-1.5 mt-4 text-sm font-semibold first:mt-0">{children}</h3>,
  p: ({ children }) => <p className="my-2 leading-7 first:mt-0 last:mb-0">{children}</p>,
  ul: ({ children }) => <ul className="my-3 list-disc space-y-1.5 pl-5">{children}</ul>,
  ol: ({ children }) => <ol className="my-3 list-decimal space-y-1.5 pl-5">{children}</ol>,
  li: ({ children }) => <li className="pl-1 leading-6">{children}</li>,
  strong: ({ children }) => <strong className="font-semibold text-slate-900 dark:text-white">{children}</strong>,
  a: ({ children, href }) => <a href={href} target="_blank" rel="noreferrer" className="font-medium text-indigo-600 underline decoration-indigo-300 underline-offset-2 dark:text-indigo-400">{children}</a>,
  blockquote: ({ children }) => <blockquote className="my-3 border-l-2 border-indigo-300 pl-4 text-slate-600 dark:border-indigo-700 dark:text-slate-300">{children}</blockquote>,
  code: ({ children }) => <code className="rounded bg-slate-100 px-1.5 py-0.5 text-[0.9em] text-slate-800 dark:bg-slate-800 dark:text-slate-100">{children}</code>,
  pre: ({ children }) => <pre className="my-3 overflow-x-auto rounded-xl bg-slate-950 p-4 text-xs leading-6 text-slate-100">{children}</pre>,
  // Generated image URLs can leak private context through automatic network requests.
  img: ({ alt }) => <span className="text-slate-500">{alt || 'Image omitted'}</span>,
}

function uniqueSources(sources = []) {
  return sources.filter((source, index) => source?.label && sources.findIndex((item) => item?.label === source.label) === index)
}

export default function ChatMessage({ message }) {
  if (message.role === 'user') {
    return (
      <motion.article initial={{ opacity: 0, y: 7 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.18 }} className="flex justify-end">
        <div className="max-w-[86%] whitespace-pre-wrap break-words rounded-2xl rounded-br-md bg-indigo-600 px-4 py-3 text-sm leading-6 text-white sm:max-w-[75%]">{message.content}</div>
      </motion.article>
    )
  }

  const sources = uniqueSources(message.sources)
  const groundingLabel = groundingLabels[message.grounding_mode] || groundingLabels.general

  return (
    <motion.article initial={{ opacity: 0, y: 7 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.2 }} className="flex items-start gap-3">
      <span className="mt-0.5 grid h-8 w-8 shrink-0 place-items-center rounded-lg bg-[#ebeafe] text-indigo-600 dark:bg-indigo-950 dark:text-indigo-300"><Bot size={16} /></span>
      <div className="min-w-0 max-w-3xl flex-1">
        <div className="mb-3 flex flex-wrap items-center gap-2 text-[11px] font-medium text-slate-500">
          <span className={`rounded-full px-2.5 py-1 ${message.grounding_mode === 'general' ? 'bg-slate-100 dark:bg-slate-800' : 'bg-indigo-50 text-indigo-700 dark:bg-indigo-950/50 dark:text-indigo-300'}`}>{groundingLabel}</span>
        </div>
        <div className="break-words text-sm text-slate-700 dark:text-slate-200">
          <ReactMarkdown components={markdownComponents}>{message.content}</ReactMarkdown>
        </div>
        {sources.length > 0 && (
          <div className="mt-4 border-t pt-3">
            <p className="flex items-center gap-1.5 text-[11px] font-semibold uppercase tracking-[0.08em] text-slate-400"><Database size={12} />Context used</p>
            <div className="mt-2 flex flex-wrap gap-2">
              {sources.map((source) => <span key={`${source.context_id || source.source_type}-${source.label}`} title={source.source_type?.replaceAll('_', ' ')} className="max-w-full truncate rounded-md border bg-[#fafaff] px-2 py-1 text-xs text-slate-500 dark:bg-slate-900">{source.label}</span>)}
            </div>
          </div>
        )}
      </div>
    </motion.article>
  )
}
