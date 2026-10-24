import { useEffect, useState } from 'react'

type ApiStatus = 'checking' | 'online' | 'offline'

export default function App() {
  const [status, setStatus] = useState<ApiStatus>('checking')

  useEffect(() => {
    fetch('/api/v1/health')
      .then((response) => setStatus(response.ok ? 'online' : 'offline'))
      .catch(() => setStatus('offline'))
  }, [])

  return (
    <main>
      <h1>EduTrack</h1>
      <p>API: {status}</p>
    </main>
  )
}
