import { BriefcaseBusiness, Menu, PanelLeft, Search } from 'lucide-react'
import { useCallback, useEffect, useState } from 'react'
import { Link, Outlet } from 'react-router-dom'
import CommandPalette from '../components/navigation/CommandPalette'
import DashboardSidebar from '../components/navigation/DashboardSidebar'
import ThemeToggle from '../components/ui/ThemeToggle'
import { useAuth } from '../context/AuthContext'

export default function DashboardLayout() {
  const [sidebarOpen, setSidebarOpen] = useState(false)
  const [collapsed, setCollapsed] = useState(false)
  const [commandOpen, setCommandOpen] = useState(false)
  const openCommands = useCallback(() => setCommandOpen(true), [])
  const closeSidebar = useCallback(() => setSidebarOpen(false), [])
  const { user } = useAuth()
  const initials = user.full_name.split(' ').slice(0, 2).map((part) => part[0]).join('').toUpperCase()

  useEffect(() => {
    function handleShortcut(event) { if ((event.ctrlKey || event.metaKey) && event.key.toLowerCase() === 'k') { event.preventDefault(); openCommands() } }
    window.addEventListener('keydown', handleShortcut)
    return () => window.removeEventListener('keydown', handleShortcut)
  }, [openCommands])

  return (
    <div className="career-shell min-h-screen bg-[var(--app-bg)]">
      <a href="#workspace-content" className="sr-only focus:not-sr-only focus:fixed focus:left-4 focus:top-3 focus:z-50 focus:rounded-lg focus:bg-[var(--surface)] focus:p-3">Skip to main content</a>
      <DashboardSidebar open={sidebarOpen} collapsed={collapsed} onClose={closeSidebar} />
      <div className={`transition-[padding] duration-200 ${collapsed ? 'lg:pl-[76px]' : 'lg:pl-64'}`}>
        <header className="career-topbar sticky top-0 z-20 flex h-16 items-center justify-between border-b px-4 sm:px-6 lg:px-8">
          <div className="flex min-w-0 items-center gap-3">
            <button type="button" onClick={() => setSidebarOpen(true)} className="icon-button lg:hidden" aria-label="Open navigation"><Menu size={19} /></button>
            <button type="button" onClick={() => setCollapsed((value) => !value)} className="icon-button hidden lg:grid" aria-label={collapsed ? 'Expand sidebar' : 'Collapse sidebar'}><PanelLeft size={18} /></button>
            <div className="hidden h-7 w-px bg-[var(--border)] sm:block" />
            <div className="min-w-0">
              <p className="text-[10px] font-semibold uppercase tracking-[.14em] text-slate-400">Target role</p>
              <p className="flex items-center gap-1.5 truncate text-sm font-semibold"><BriefcaseBusiness size={14} className="text-[var(--primary)]" />{user.target_role}</p>
            </div>
          </div>
          <div className="flex items-center gap-1.5">
            <button type="button" onClick={openCommands} className="command-trigger hidden h-9 w-64 items-center gap-2 rounded-lg border px-3 text-sm text-slate-400 sm:flex"><Search size={15} />Search workspace<span className="ml-auto rounded border px-1.5 py-0.5 text-[10px]">Ctrl K</span></button>
            <button type="button" onClick={openCommands} className="icon-button sm:hidden" aria-label="Search workspace"><Search size={18} /></button>
            <ThemeToggle />
            <Link to="/profile" className="profile-avatar ml-1 grid h-9 w-9 place-items-center rounded-full text-xs font-bold" aria-label="Open profile">{initials}</Link>
          </div>
        </header>
        <main id="workspace-content" tabIndex={-1} className="p-4 sm:p-6 lg:p-8"><Outlet /></main>
      </div>
      <CommandPalette open={commandOpen} onClose={() => setCommandOpen(false)} />
    </div>
  )
}
