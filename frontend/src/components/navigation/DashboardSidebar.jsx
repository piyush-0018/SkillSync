import { BarChart3, Bot, FileSearch, FileText, LayoutDashboard, LogOut, MessageSquareText, Settings, Target, UserRound, X } from 'lucide-react'
import { NavLink, useNavigate } from 'react-router-dom'
import { useRef, useState } from 'react'
import { useAuth } from '../../context/AuthContext'
import useMobileDialog from '../../hooks/useMobileDialog'
import { getApiErrorMessage } from '../../services/api'
import Brand from '../ui/Brand'

const groups = [
  { label: 'Workspace', items: [
    { label: 'Overview', icon: LayoutDashboard, to: '/dashboard', end: true },
    { label: 'Profile', icon: UserRound, to: '/profile', end: true },
  ] },
  { label: 'Preparation', items: [
    { label: 'Resume', icon: FileText, to: '/resume', end: true },
    { label: 'Resume analysis', icon: FileSearch, to: '/resume/analysis', end: true },
    { label: 'Job matches', icon: Target, to: '/job-match', end: true },
    { label: 'Interviews', icon: MessageSquareText, to: '/interviews', end: false },
  ] },
  { label: 'Intelligence', items: [
    { label: 'Career assistant', icon: Bot, to: '/career-assistant', end: true },
    { label: 'Progress', icon: BarChart3, to: '/analytics', end: true },
  ] },
]

export default function DashboardSidebar({ open, collapsed, onClose }) {
  const navigate = useNavigate()
  const { logout } = useAuth()
  const sidebarRef = useRef(null)
  const [logoutError, setLogoutError] = useState('')
  const [isLoggingOut, setIsLoggingOut] = useState(false)
  useMobileDialog(sidebarRef, open, onClose)

  async function handleLogout() {
    if (isLoggingOut) return
    setIsLoggingOut(true)
    setLogoutError('')
    try {
      await logout()
      navigate('/login', { replace: true })
    } catch (error) {
      setLogoutError(getApiErrorMessage(error, 'Could not sign out. Please retry.'))
    } finally {
      setIsLoggingOut(false)
    }
  }

  return (
    <>
      {open && <button type="button" aria-label="Close sidebar" className="fixed inset-0 z-30 bg-slate-950/40 lg:hidden" onClick={onClose} />}
      <aside ref={sidebarRef} aria-label="Workspace navigation" className={`career-sidebar fixed inset-y-0 left-0 z-40 flex w-64 flex-col border-r transition-[width,transform] duration-200 ${open ? 'visible translate-x-0' : 'invisible -translate-x-full'} lg:visible lg:translate-x-0 ${collapsed ? 'lg:w-[76px]' : 'lg:w-64'}`}>
        <div className="flex h-16 items-center justify-between border-b px-5"><Brand compact={collapsed} /><button type="button" className="icon-button lg:hidden" onClick={onClose} aria-label="Close sidebar"><X size={19} /></button></div>
        <nav className="min-h-0 flex-1 overflow-y-auto px-3 py-4" aria-label="Dashboard navigation">
          {groups.map((group, groupIndex) => <div key={group.label} className={groupIndex ? 'mt-6' : ''}>
            <p className={`mb-2 px-3 text-[10px] font-semibold uppercase tracking-[.16em] text-slate-400 ${collapsed ? 'lg:hidden' : ''}`}>{group.label}</p>
            <div className="space-y-1">{group.items.map(({ label, icon: Icon, to, end }) => <NavLink aria-label={label} title={collapsed ? label : undefined} key={label} to={to} end={end} onClick={onClose} className={({ isActive }) => `sidebar-link flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm font-medium transition ${isActive ? 'active' : ''}`}><Icon size={18} className="shrink-0" /><span className={collapsed ? 'lg:hidden' : ''}>{label}</span></NavLink>)}</div>
          </div>)}
        </nav>
        <div className="space-y-1 border-t p-3">
          {logoutError && <p role="alert" className="px-3 text-xs text-rose-600 dark:text-rose-300">{logoutError}</p>}
          <NavLink aria-label="Settings" title={collapsed ? 'Settings' : undefined} to="/settings" onClick={onClose} className={({ isActive }) => `sidebar-link flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm font-medium transition ${isActive ? 'active' : ''}`}><Settings size={18} className="shrink-0" /><span className={collapsed ? 'lg:hidden' : ''}>Settings</span></NavLink>
          <button aria-label={isLoggingOut ? 'Signing out' : 'Sign out'} disabled={isLoggingOut} title={collapsed ? 'Sign out' : undefined} type="button" onClick={handleLogout} className="sidebar-link flex w-full items-center gap-3 rounded-lg px-3 py-2.5 text-sm font-medium transition hover:!text-rose-600 disabled:opacity-50"><LogOut size={18} className="shrink-0" /><span className={collapsed ? 'lg:hidden' : ''}>{isLoggingOut ? 'Signing out…' : 'Sign out'}</span></button>
        </div>
      </aside>
    </>
  )
}
