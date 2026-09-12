import { Laptop, Moon, Settings, Sun } from 'lucide-react'
import { Link } from 'react-router-dom'
import PageHeader from '../components/ui/PageHeader'
import { useAuth } from '../context/AuthContext'
import { useTheme } from '../context/ThemeContext'

const themeOptions = [
  { value: 'light', label: 'Light', description: 'Use the slate light palette.', icon: Sun },
  { value: 'dark', label: 'Dark', description: 'Use the deep navy palette.', icon: Moon },
  { value: 'system', label: 'System', description: 'Follow your device preference.', icon: Laptop },
]

export default function SettingsPage() {
  const { user } = useAuth()
  const { theme, setTheme } = useTheme()

  return (
    <div className="page-shell">
      <PageHeader icon={Settings} kicker="Workspace preferences" title="Settings" description="Manage appearance and review the account and data controls supported by this version of SkillSync." />

      <div className="mt-8 grid gap-6 lg:grid-cols-[1.3fr_.7fr]">
        <div className="space-y-6">
          <section className="surface-panel p-5 sm:p-6"><h2 className="font-semibold">Appearance</h2><p className="mt-1 text-sm text-slate-500">Your choice is saved on this device.</p><div className="mt-5 grid gap-3 sm:grid-cols-3">{themeOptions.map(({ value, label, description, icon: Icon }) => <button key={value} type="button" onClick={() => setTheme(value)} aria-pressed={theme === value} className={`rounded-xl border p-4 text-left transition ${theme === value ? 'border-blue-600 bg-blue-50 ring-1 ring-blue-600 dark:bg-blue-950/40' : 'bg-[var(--surface-subtle)] hover:border-blue-400'}`}><Icon size={18} className={theme === value ? 'text-blue-700 dark:text-blue-300' : 'text-slate-500'} /><span className="mt-4 block text-sm font-semibold">{label}</span><span className="mt-1 block text-xs leading-5 text-slate-500">{description}</span></button>)}</div></section>

          <section className="surface-panel p-5 sm:p-6"><h2 className="font-semibold">Career preferences</h2><p className="mt-1 text-sm text-slate-500">These values shape the guidance and interview defaults supported by the backend.</p><dl className="mt-5 divide-y rounded-xl border bg-[var(--surface-subtle)] px-4"><div className="flex items-center justify-between gap-4 py-4"><dt className="text-sm text-slate-500">Target role</dt><dd className="text-sm font-medium">{user.target_role || 'Not set'}</dd></div><div className="flex items-center justify-between gap-4 py-4"><dt className="text-sm text-slate-500">Experience level</dt><dd className="text-sm font-medium capitalize">{user.experience_level || 'Not set'}</dd></div></dl><Link to="/profile" className="button-secondary mt-5">Edit profile preferences</Link></section>
        </div>

        <div className="space-y-6">
          <section className="surface-panel p-5 sm:p-6"><h2 className="font-semibold">Account</h2><p className="mt-1 text-sm text-slate-500">Signed in as</p><p className="mt-4 break-all text-sm font-medium">{user.email}</p><div className="mt-5 rounded-lg border border-dashed p-3 text-xs leading-5 text-slate-500">Password and email changes are not exposed by the current backend. No inactive controls are shown.</div></section>
          <section className="surface-panel p-5 sm:p-6"><h2 className="font-semibold">Resume data</h2><p className="mt-2 text-sm leading-6 text-slate-500">Resume replacement and deletion include their own validation and confirmation in Resume management.</p><Link to="/resume" className="button-secondary mt-5">Manage resume</Link></section>
        </div>
      </div>
    </div>
  )
}
