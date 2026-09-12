import { motion } from 'framer-motion'
import { LogOut } from 'lucide-react'
import { useNavigate } from 'react-router-dom'
import ProfileForm from '../components/profile/ProfileForm'
import Brand from '../components/ui/Brand'
import ThemeToggle from '../components/ui/ThemeToggle'
import { useAuth } from '../context/AuthContext'

export default function ProfileSetupPage() {
  const navigate = useNavigate()
  const { logout } = useAuth()

  async function handleLogout() {
    await logout()
    navigate('/login', { replace: true })
  }

  return (
    <main className="min-h-screen bg-[var(--app-bg)]">
      <header className="flex h-16 items-center justify-between border-b bg-[var(--surface)] px-5 sm:px-8"><Brand /><div className="flex items-center gap-2"><ThemeToggle /><button type="button" onClick={handleLogout} className="inline-flex items-center gap-2 rounded-lg px-3 py-2 text-sm font-medium text-slate-500 hover:bg-[var(--surface-subtle)] hover:text-slate-900 dark:hover:text-white"><LogOut size={16} /> Sign out</button></div></header>
      <motion.div initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: .24 }} className="mx-auto w-full max-w-2xl px-5 py-12 sm:py-16">
        <div className="mb-7"><span className="text-sm font-semibold text-indigo-600 dark:text-indigo-400">One last step</span><h1 className="mt-2 text-3xl font-bold tracking-[-0.03em]">Set your career direction</h1><p className="mt-3 max-w-xl text-sm leading-6 text-slate-500">This helps SkillSync shape your workspace around the role you are preparing for. You can change these details later.</p></div>
        <section className="surface-panel p-6 sm:p-8"><ProfileForm setup onComplete={() => navigate('/dashboard', { replace: true })} /></section>
      </motion.div>
    </main>
  )
}
