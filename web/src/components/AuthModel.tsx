import {
    createUserWithEmailAndPassword,
    GoogleAuthProvider,
    signInWithEmailAndPassword,
    signInWithPopup
} from 'firebase/auth'
import { doc, getDoc, setDoc } from 'firebase/firestore'
import { useState } from 'react'
import { auth, db } from '../firebase'

export default function AuthModal({ onClose }: any) {
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [isLogin, setIsLogin] = useState(true)

  const handleEmailAuth = async () => {
  try {
    let userCredential

    if (isLogin) {
      userCredential = await signInWithEmailAndPassword(auth, email, password)
    } else {
      userCredential = await createUserWithEmailAndPassword(auth, email, password)
    }

    const user = userCredential.user

    // 🔥 create Firestore doc if not exists
    const ref = doc(db, 'users', user.uid)
    const snap = await getDoc(ref)

    if (!snap.exists()) {
      await setDoc(ref, {
        points: 0,
        streak: 0,
        completedSigns: []
      })
      console.log("✅ User created in Firestore")
    }

    onClose()

  } catch (e) {
    alert('Error: ' + (e as any).message)
  }
}

 const handleGoogle = async () => {
  console.log("CLICKED GOOGLE")

  try {
    const provider = new GoogleAuthProvider()
    await signInWithPopup(auth, provider)
    onClose()
  } catch (e) {
    console.error("GOOGLE ERROR:", e)
    alert((e as any).message)
  }
}

  return (
    <div style={overlay}>
      <div style={modal}>
        <h2>{isLogin ? 'Login' : 'Register'}</h2>

        <input
          placeholder="Email"
          value={email}
          onChange={e => setEmail(e.target.value)}
          style={input}
        />

        <input
          type="password"
          placeholder="Password"
          value={password}
          onChange={e => setPassword(e.target.value)}
          style={input}
        />

        <button onClick={handleEmailAuth} style={button}>
          {isLogin ? 'Login' : 'Register'}
        </button>

        <button
  style={{
    height: '48px',  
    marginTop : "9px",
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    gap: '10px',
    width: '100%',
    padding: '12px',
    borderRadius: '12px',
    border: 'none',
    background: '#fff',
    color: '#000',
    fontWeight: 'bold',
    cursor: 'pointer'
  }}
  onClick={handleGoogle} 
>
  <img
    src="https://www.gstatic.com/firebasejs/ui/2.0.0/images/auth/google.svg"
    alt="Google"
    style={{ width: 20, height: 20 }}
  />
  Continue with Google
</button>
        <p
          style={{ marginTop: 10, cursor: 'pointer', color: '#aaa' }}
          onClick={() => setIsLogin(!isLogin)}
        >
          {isLogin ? 'No account? Register' : 'Have account? Login'}
        </p>

        <button onClick={onClose} style={closeBtn}>
          ✕
        </button>
      </div>
    </div>
  )
}

const overlay = {
  position: 'fixed' as const,
  top: 0,
  left: 0,
  width: '100%',
  height: '100%',
  background: 'rgba(0,0,0,0.7)',
  display: 'flex',
  alignItems: 'center',
  justifyContent: 'center',
  zIndex: 9999
}

const modal = {
  background: '#0f172a',
  padding: '30px',
  borderRadius: '16px',
  width: '320px',
  position: 'relative' as const
}

const input = {
  width: '100%',
  padding: '10px',
  marginTop: '10px',
  borderRadius: '8px',
  border: '1px solid #333',
  background: '#020617',
  color: '#fff'
}

const button = {
    fontSize : "14px",
  width: '100%',
  marginTop: '15px',
  padding: '10px',
  background: '#22c55e',
  border: 'none',
  borderRadius: '8px',
  color: '#fff',
  fontWeight: 'bold',
  height: '48px',  
}

const googleBtn = {
  ...button,
  background: '#fff',
  color: '#000'
}

const closeBtn = {
  position: 'absolute' as const,
  top: 10,
  right: 10,
  background: 'transparent',
  border: 'none',
  color: '#fff',
  fontSize: '16px',
  cursor: 'pointer'
}