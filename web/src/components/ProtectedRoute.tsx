import { onAuthStateChanged } from 'firebase/auth'
import { useEffect, useState } from 'react'
import { Navigate } from 'react-router-dom'
import { auth } from '../firebase.ts'

export default function ProtectedRoute({ children }: any) {
  const [user, setUser] = useState<any>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const unsub = onAuthStateChanged(auth, (u) => {
      setUser(u)
      setLoading(false)
    })
    return () => unsub()
  }, [])

  if (loading) return <div>Loading...</div>

  if (!user) {
    return <Navigate to="/login" />
  }

  return children
}