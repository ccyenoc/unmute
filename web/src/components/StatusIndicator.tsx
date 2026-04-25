import { useEffect, useState } from 'react'

type Status = 'checking' | 'online' | 'offline'

export default function StatusIndicator() {
  const [status, setStatus] = useState<Status>('checking')
  const [latency, setLatency] = useState<number | null>(null)

  useEffect(() => {
    const check = async () => {
      const t0 = Date.now()
      try {
        const res = await fetch('/api/../health', { signal: AbortSignal.timeout(3000) })
        if (res.ok) {
          setLatency(Date.now() - t0)
          setStatus('online')
        } else {
          setStatus('offline')
        }
      } catch {
        setStatus('offline')
      }
    }

    check()
    const id = setInterval(check, 8000)
    return () => clearInterval(id)
  }, [])

  const label =
    status === 'checking' ? 'Connecting...' :
    status === 'online' ? `Backend • ${latency}ms` :
    'Backend offline'

  return (
    <div className="status-indicator">
      <div className={`status-dot ${status}`} />
      <span>{label}</span>
    </div>
  )
}
