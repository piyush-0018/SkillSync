import { Navigate, Outlet, useLocation } from 'react-router-dom'
import { useAuth } from '../../context/AuthContext'
import Brand from '../ui/Brand'

function SessionLoader() {
  return <div className="grid min-h-screen place-items-center bg-[#f4f3fa] dark:bg-slate-950"><div className="flex flex-col items-center gap-4"><Brand /><span className="h-5 w-5 animate-spin rounded-full border-2 border-indigo-600 border-t-transparent" aria-label="Checking your session" /></div></div>
}

export function ProtectedRoute() {
  const { user, isLoading } = useAuth()
  const location = useLocation()
  if (isLoading) return <SessionLoader />
  if (!user) return <Navigate to="/login" state={{ from: location }} replace />
  return <Outlet />
}

export function GuestRoute() {
  const { user, isLoading } = useAuth()
  if (isLoading) return <SessionLoader />
  if (user) return <Navigate to={user.target_role && user.experience_level ? '/dashboard' : '/profile/setup'} replace />
  return <Outlet />
}

export function ProfileCompleteRoute() {
  const { user } = useAuth()
  if (!user?.target_role || !user?.experience_level) return <Navigate to="/profile/setup" replace />
  return <Outlet />
}
