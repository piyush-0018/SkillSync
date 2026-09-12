import { ArrowLeft, Check, FileSearch, Target } from 'lucide-react'
import { Link, Outlet } from 'react-router-dom'
import Brand from '../components/ui/Brand'
import ThemeToggle from '../components/ui/ThemeToggle'

export default function AuthLayout() {
  return (
    <main className="grid min-h-screen bg-[var(--app-bg)] lg:grid-cols-[.92fr_1.08fr]">
      <section className="relative hidden overflow-hidden border-r bg-slate-950 p-10 text-white lg:flex lg:flex-col dark:bg-[#02050b]">
        <Brand />
        <div className="my-auto max-w-lg"><p className="text-sm font-medium text-blue-300">Your career evidence, connected</p><h1 className="mt-4 text-4xl font-semibold leading-tight tracking-[-0.04em]">Prepare for the role with context, not guesswork.</h1><p className="mt-5 text-sm leading-7 text-slate-400">SkillSync brings your resume, job comparisons, practice history, and next actions into one private workspace.</p><div className="mt-10 space-y-5">{[[FileSearch, 'Transparent readiness analysis'], [Target, 'Role-specific skill evidence'], [Check, 'Progress based on saved results']].map(([Icon, label]) => <div key={label} className="flex items-center gap-3 text-sm"><span className="grid h-8 w-8 place-items-center rounded-lg border border-white/10 bg-white/5 text-blue-300"><Icon size={15} /></span>{label}</div>)}</div></div>
        <p className="text-xs text-slate-500">Local AI support · Private account workspace</p>
      </section>
      <section className="flex min-h-screen flex-col">
        <header className="flex h-16 items-center justify-between px-5 sm:px-8"><div className="lg:hidden"><Brand /></div><Link to="/" className="hidden items-center gap-2 text-sm text-slate-500 transition hover:text-slate-900 dark:hover:text-white lg:inline-flex"><ArrowLeft size={15} />Back to home</Link><ThemeToggle /></header>
        <div className="mx-auto flex w-full max-w-md flex-1 flex-col justify-center px-5 pb-16"><Link to="/" className="mb-7 inline-flex w-fit items-center gap-2 text-sm text-slate-500 lg:hidden"><ArrowLeft size={15} />Back to home</Link><Outlet /></div>
      </section>
    </main>
  )
}
