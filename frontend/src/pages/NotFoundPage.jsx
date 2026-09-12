import { ArrowLeft } from 'lucide-react'
import { Link } from 'react-router-dom'
import Brand from '../components/ui/Brand'
import { useAuth } from '../context/AuthContext'

export default function NotFoundPage() {
  const { user } = useAuth()
  const destination = user ? '/dashboard' : '/'
  return <main className="grid min-h-screen place-items-center bg-[var(--app-bg)] px-5"><div className="w-full max-w-lg"><Brand /><div className="mt-12 border-l-2 border-blue-600 pl-6"><p className="text-sm font-semibold text-blue-600 dark:text-blue-400">404</p><h1 className="mt-3 text-3xl font-semibold tracking-[-0.035em]">This page is not part of your workspace.</h1><p className="mt-4 text-sm leading-6 text-slate-500">The address may be outdated, or the page may have moved. Your saved SkillSync data has not been affected.</p><Link to={destination} className="button-primary mt-7 gap-2"><ArrowLeft size={15} />{user ? 'Return to dashboard' : 'Return home'}</Link></div></div></main>
}
