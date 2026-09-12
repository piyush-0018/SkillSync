import { Link } from 'react-router-dom'

export default function Brand({ compact = false }) {
  return (
    <Link to="/" className="group inline-flex items-center gap-2.5" aria-label="SkillSync home">
      <span className="brand-mark relative grid h-8 w-8 place-items-center text-blue-700">
        <span className="absolute h-2.5 w-2.5 -translate-x-1 -translate-y-1 rotate-45 rounded-[3px] bg-current" /><span className="absolute h-2.5 w-2.5 translate-x-1 translate-y-1 rotate-45 rounded-[3px] bg-current" /><span className="absolute h-1.5 w-1.5 translate-x-1.5 -translate-y-1.5 rounded-full bg-current opacity-80 dark:opacity-100" /><span className="absolute h-1.5 w-1.5 -translate-x-1.5 translate-y-1.5 rounded-full bg-current opacity-80 dark:opacity-100" />
      </span>
      {!compact && <span className="brand-wordmark text-lg font-semibold tracking-[-0.035em]">SkillSync</span>}
    </Link>
  )
}
