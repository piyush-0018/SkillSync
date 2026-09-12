import { useEffect, useState } from 'react'
import { getHealthStatus } from '../../services/healthService'

export default function BackendStatus() {
  const [status, setStatus] = useState('checking')

  useEffect(() => {
    let active = true
    getHealthStatus().then(() => active && setStatus('online')).catch(() => active && setStatus('offline'))
    return () => { active = false }
  }, [])

  const styles = { checking: 'bg-amber-400', online: 'bg-emerald-500', offline: 'bg-rose-500' }
  return <div className="inline-flex items-center gap-2 text-xs text-slate-500" title="FastAPI service status"><span className={`h-2 w-2 rounded-full ${styles[status]}`} />Backend {status}</div>
}
