import { onAuthStateChanged, signOut } from 'firebase/auth'
import {
  collection,
  doc,
  getDoc,
  getDocs,
  updateDoc
} from 'firebase/firestore'
import { useEffect, useRef, useState } from 'react'
import AuthModal from '../components/AuthModel'
import { auth, db } from '../firebase'

interface SignItem {
  id: string
  word: string
  videoUrl: string
  day: number
  xp?: number
}

interface UserProgress {
  points: number
  streak: number
  completedSigns: string[]
}

export default function LearnPage() {
  useEffect(() => {
  const loadSigns = async () => {
    const snap = await getDocs(collection(db, 'signs'))

    const data = snap.docs.map(doc => ({
      id: doc.id,
      ...doc.data()
    })) as SignItem[]

    setSigns(data)
  }

  loadSigns()
}, [])

  const [user, setUser] = useState<any>(null)
  useEffect(() => {
  const unsub = onAuthStateChanged(auth, (u) => {
    setUser(u)
    console.log("LOGGED USER:", u)
  })

  return () => unsub()
}, [])

const handleLogout = async () => {
  try {
    await signOut(auth)
    console.log("Logged out")
  } catch (e) {
    console.error("Logout error:", e)
  }
}

const [showHistory, setShowHistory] = useState(false)
const [historySearch, setHistorySearch] = useState('')

  const dayMap: Record<number, string[]> = {
  1: ['hi', 'bye', 'thankyou', 'sorry'],
  2: ['hungry', 'tired', 'help'],
  3: ['yes', 'no', 'sure']
}

const normalize = (word: string) =>
  word.toLowerCase().replace(/\s/g, '')

  const videoRef = useRef<HTMLVideoElement>(null)
  const [signs, setSigns] = useState<SignItem[]>([])
  const [current, setCurrent] = useState<SignItem | null>(null)
 const [progress, setProgress] = useState<UserProgress>({
  points: 0,
  streak: 0,
  completedSigns: []
})
  const [search, setSearch] = useState('')
  const [showAuth, setShowAuth] = useState(false)

  const userId = user?.uid
  const [currentDay, setCurrentDay] = useState(1)
  const [showCamera, setShowCamera] = useState(false)

  const holdTimerRef = useRef<number | null>(null)
const passedRef = useRef(false)

  const [currentWord, setCurrentWord] = useState('')
const [confidence, setConfidence] = useState(0)
const [emotion, setEmotion] = useState('')

const [liveSentence, setLiveSentence] = useState('')
const [status, setStatus] = useState<'idle' | 'correct' | 'wrong'>('idle')


  useEffect(() => {
  if (!showCamera) return

  let interval: any

  navigator.mediaDevices.getUserMedia({ video: true })
    .then(stream => {
      if (videoRef.current) {
        videoRef.current.srcObject = stream
        videoRef.current.play()
      }
    })

  interval = setInterval(async () => {
    const video = videoRef.current
    if (!video) return

    const canvas = document.createElement('canvas')
    canvas.width = 640
    canvas.height = 480

    const ctx = canvas.getContext('2d')
    ctx?.drawImage(video, 0, 0)

    canvas.toBlob(async blob => {
      if (!blob) return

      try {
        const fd = new FormData()
        fd.append('file', blob)

        // 🔥 SIGN DETECTION
        const res = await fetch('/api/detection/predict', {
          method: 'POST',
          body: fd
        })

        const data = await res.json()

        const prediction = data.prediction ?? ''
const conf = data.confidence ?? 0

setCurrentWord(prediction)
setConfidence(conf)

const cleanPred = prediction.toLowerCase().replace(/\s/g, '')
const target = current?.word.toLowerCase().replace(/\s/g, '')

const isValid = prediction && conf >= 0.6

if (!isValid) {
  setStatus('idle')
} else {
  setLiveSentence(cleanPred)

  if (cleanPred === target && conf > 0.6) {
  if (!holdTimerRef.current && !passedRef.current) {
    // ⏳ start delay (1.2s feels good)
    holdTimerRef.current = window.setTimeout(() => {
      passedRef.current = true

      alert('✅ Correct!')
      handlePracticeSuccess()
      setShowCamera(false)

      holdTimerRef.current = null
    }, 1200)
  }
  } else {
    setStatus('wrong')
  }
}

        // 🔥 EMOTION DETECTION
        const emoRes = await fetch('/api/emotion/predict', {
          method: 'POST',
          body: fd
        })

        if (emoRes.ok) {
          const emoData = await emoRes.json()
          setEmotion(emoData.emotion ?? '')
        }

      } catch (e) {
        console.error(e)
      }
    }, 'image/jpeg', 0.8)

  }, 500)

  return () => {
  clearInterval(interval)

  const stream = videoRef.current?.srcObject as MediaStream
  stream?.getTracks().forEach(track => track.stop())
}
}, [showCamera, current])

  // ── Practice success ──
  const handlePracticeSuccess = async () => {
    if (!current) return

    if (
  !progress.completedSigns.some(
    w => normalize(w) === normalize(current.word)
  )
) {
      const updated = {
        ...progress,
        points: progress.points + (current?.xp || 10),
        completedSigns: [...progress.completedSigns, current.word]
      }

      setProgress(updated)
      if (!userId) return
await updateDoc(doc(db, 'users', userId), updated)
      alert('✅ +10 XP!')
    }
  }

  // ── Day unlock logic ──
  const day2Unlocked = progress.points >= 20
  const day3Unlocked = progress.points >= 40

  // ── Search filter ──
  const filteredSigns = signs.filter(s =>
    s.word.toLowerCase().includes(search.toLowerCase())
  )

  const daySigns = signs.filter(s => Number(s.day) === currentDay)


useEffect(() => {
  if (!user) return

  const loadUser = async () => {
    const snap = await getDoc(doc(db, 'users', user.uid))

    if (snap.exists()) {
      setProgress(snap.data() as UserProgress)
    }
  }

  loadUser()
}, [user])

  return (
    <div className="page">
     <div
  style={{
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'space-between',
    marginBottom: '10px'
  }}
>
  <h1 style={{ margin: 0 }}>Learn Sign Language</h1>

  {user ? (
  <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
    
    {/* Avatar */}
    <div
      style={{
        width: 36,
        height: 36,
        borderRadius: '50%',
        background: '#22c55e',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        fontWeight: 'bold'
      }}
    >
      {user.email?.charAt(0).toUpperCase()}
    </div>

    {/* Email */}
    <span style={{ fontSize: '0.9rem' }}>
      {user.email}
    </span>

    {/* Logout */}
    <button
      onClick={() => signOut(auth)}
      style={{
        background: '#1e293b',
        color: '#fff',
        border: 'none',
        padding: '6px 10px',
        borderRadius: '8px',
        cursor: 'pointer'
      }}
    >
      Logout
    </button>
  </div>
) : (
  <button
    onClick={() => setShowAuth(true)}
    style={{
      background: '#22c55e',
      color: '#fff',
      padding: '8px 16px',
      borderRadius: '10px',
      border: 'none',
      fontWeight: 'bold',
      cursor: 'pointer'
    }}
  >
    🔐 Login to save progress
  </button>
)}

</div>

      {/* ── SEARCH BAR ── */}
        <input
          placeholder="🔍 Search signs..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          style={{
            marginBottom : "20px",
            marginTop : "10px",
            width: '100%',
            padding: '10px',
            borderRadius: '10px',
            border: '1px solid #333',
            background: '#0f172a',
            color: '#fff'
          }}
        />

      {/* ── STATS ── */}
      <div
  style={{
    display: 'grid',
    gridTemplateColumns: 'repeat(4, 1fr)',
    gap: 16,
    marginBottom: 20
  }}
>
  {/* 🎯 LEVEL + XP */}
  {(() => {
    const xpForNextLevel = 50
    const level = Math.floor(progress.points / xpForNextLevel) + 1
    const currentXp = progress.points % xpForNextLevel
    const percent = (currentXp / xpForNextLevel) * 100

    return (
     <div className="card" style={{ padding: 18 }}>
  <div style={{ fontSize: '0.8rem', color: '#94a3b8' }}>
    🎯 Level Progress
  </div>

  <div style={{ fontSize: '0.85rem', color: '#64748b', marginTop: 2 }}>
    XP towards next level
  </div>

  <div style={{ fontSize: '1.8rem', fontWeight: 'bold', marginTop: 10 }}>
    Level {level}
  </div>

  <div style={{ fontSize: '0.85rem', color: '#94a3b8', marginTop: 4 }}>
    ✨ {currentXp} / {xpForNextLevel} XP
  </div>

  <div
    style={{
      height: 6,
      background: '#1e293b',
      borderRadius: 6,
      marginTop: 10,
      overflow: 'hidden'
    }}
  >
    <div
      style={{
        width: `${percent}%`,
        height: '100%',
        background: 'linear-gradient(90deg, #22c55e, #4ade80)'
      }}
    />
  </div>

  <div style={{ fontSize: '0.75rem', color: '#64748b', marginTop: 6 }}>
    🚀 {xpForNextLevel - currentXp} XP to level up
  </div>
</div>
    )
  })()}

  {/* 🏆 BADGES */}
  <div className="card" style={{ padding: 18 }}>
  <div style={{ fontSize: '0.8rem', color: '#94a3b8' }}>
    🏆 Achievements
  </div>

  <div style={{ fontSize: '0.85rem', color: '#64748b', marginTop: 2 }}>
    Badges collected
  </div>

  <div style={{ fontSize: '2rem', fontWeight: 'bold', marginTop: 14 }}>
    {Math.floor(progress.completedSigns.length / 2)}
  </div>

  <div style={{ fontSize: '0.75rem', color: '#64748b', marginTop: 4 }}>
    🎉 Keep going!
  </div>
</div>

  {/* 🔥 STREAK */}
  <div className="card" style={{ padding: 18 }}>
  <div style={{ fontSize: '0.8rem', color: '#94a3b8' }}>
    🔥 Activity Streak
  </div>

  <div style={{ fontSize: '0.85rem', color: '#64748b', marginTop: 2 }}>
    Daily consistency
  </div>

  <div style={{ fontSize: '2rem', fontWeight: 'bold', marginTop: 14 }}>
    {progress.streak}
  </div>

  <div style={{ fontSize: '0.75rem', color: '#64748b', marginTop: 4 }}>
    ⚡ Best: {progress.streak} days
  </div>
</div>

  {/* 📜 HISTORY (CLICKABLE) */}
 <div
  className="card"
  onClick={() => setShowHistory(true)}
  style={{
    padding: 18,
    cursor: 'pointer'
  }}
>
  <div style={{ fontSize: '0.8rem', color: '#94a3b8' }}>
    📜 Learning History
  </div>

  <div style={{ fontSize: '0.85rem', color: '#64748b', marginTop: 2 }}>
    Words you've mastered
  </div>

  <div style={{ fontSize: '1.6rem', marginTop: 14 }}>
    👀
  </div>

  <div style={{ fontSize: '0.75rem', color: '#64748b', marginTop: 4 }}>
    Click to explore
  </div>
</div>
</div>

     <div className="card" style={{ marginBottom: 20 }}>
  <h3>📅 Learning Path</h3>

  {/* 🔥 DAY NAVIGATION */}
  <div
    style={{
      display: 'flex',
      justifyContent: 'space-between',
      alignItems: 'center',
      marginTop: 10
    }}
  >
    <button
      onClick={() => setCurrentDay(prev => Math.max(1, prev - 1))}
      style={{
        background: '#1e293b',
        border: 'none',
        color: '#fff',
        padding: '8px 12px',
        borderRadius: '8px',
        cursor: 'pointer'
      }}
    >
      ←
    </button>

    <div style={{ fontWeight: 'bold' }}>
      Day {currentDay} — {
        currentDay === 1 ? 'Basics' :
        currentDay === 2 ? 'Needs' :
        'Responses'
      }
    </div>

    <button
      onClick={() => setCurrentDay(prev => Math.min(3, prev + 1))}
      style={{
        background: '#1e293b',
        border: 'none',
        color: '#fff',
        padding: '8px 12px',
        borderRadius: '8px',
        cursor: 'pointer'
      }}
    >
      →
    </button>

  </div>
</div>


      {/* ── SEARCH RESULTS / SIGN LIST ── */}
      <div className="card">
        <h3>🎯 Practice Signs</h3>

        <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
          {daySigns.map(sign => {
  const done = progress.completedSigns.some(
    w => normalize(w) === normalize(sign.word)
  )

  return (
    <div
  key={sign.id}
  onClick={() => {
      setShowCamera(true)
      setCurrent(sign)
  }}
  style={{
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    padding: '14px 18px',
    borderRadius: '12px',
    background: done ? '#065f46' : '#0f172a',
    border: '1px solid #1e293b',
    cursor: done ? 'default' : 'pointer',
    transition: '0.2s'
  }}
>
  {/* LEFT SIDE */}
  <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
    <span style={{ fontSize: '1.1rem' }}>
      {done ? '✅' : '○'}
    </span>
    <span style={{ fontSize: '1rem' }}>
      {sign.word}
    </span>
  </div>

  {/* RIGHT SIDE */}
  <div style={{ display: 'flex', gap: 20, fontSize: '0.9rem' }}>
    
    {/* Accuracy */}
    <span style={{ color: '#aaa' }}>
      {done ? '85%' : '--'}
    </span>

    {/* Difficulty */}
    <span style={{ color: '#22c55e' }}>
      Easy
    </span>

    {/* Lock */}
    <span>
      {done ? '🔓' : '🔒'}
    </span>
  </div>
</div>
  )
})}
        </div>
      </div>

{/* ── CAMERA PANEL ── */}
{showCamera && (
  <div
    style={{
      position: 'fixed',
      top: 0,
      left: 0,
      width: '100vw',
      height: '100vh',
      background: 'rgba(0,0,0,0.7)',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      zIndex: 9999
    }}
  >
    <div
      style={{
        background: '#0f172a',
        padding: '20px',
        borderRadius: '16px',
        width: '900px',
        maxWidth: '95%'
      }}
    >
      {/* 🔥 TITLE + CLOSE (TOP RIGHT OPTIONAL) */}
      <div
        style={{
          display: 'flex',
          justifyContent: 'space-between',
          marginBottom: 10
        }}
      >
        <h3>Practice: {current?.word}</h3>
      </div>

      {/* 🔥 MAIN CONTENT */}
      <div
        style={{
          display: 'flex',
          gap: '20px'
        }}
      >
        {/* LEFT: VIDEO */}
        <div className="justify-content-center"
        style={{ 
          flex: 1 }}>
          <video
            src={current?.videoUrl}
            controls
            style={{
              width: '100%',
              borderRadius: '12px',
              background: '#000'
            }}
          />
        </div>

        {/* RIGHT: CAMERA */}
        <div style={{ flex: 1 }}>
          <video
            ref={videoRef}
            autoPlay
            playsInline
            muted
            style={{
              width: '100%',
              borderRadius: '12px',
              background: '#000'
            }}
          />

          <div style={{ marginTop: 10 }}>
            {/* TARGET */}
            <div style={{ fontSize: '0.9rem', color: '#aaa' }}>
              Target: <b>{current?.word}</b>
            </div>

            {/* PREDICTION */}
            <div style={{ marginTop: 6 }}>
              Prediction: <b>{currentWord || '...'}</b>
            </div>

            {/* STATUS */}
            <div
              style={{
                marginTop: 6,
                fontWeight: 'bold',
                color:
                  status === 'correct'
                    ? '#22c55e'
                    : status === 'wrong'
                    ? '#ef4444'
                    : '#aaa'
              }}
            >
              {status === 'correct' && '✅ Match'}
              {status === 'wrong' && '❌ Not Match'}
              {status === 'idle' && 'Waiting...'}
            </div>

            {/* CONFIDENCE BAR */}
            <div
              style={{
                height: 8,
                background: '#1e293b',
                borderRadius: 6,
                marginTop: 8,
                overflow: 'hidden'
              }}
            >
              <div
                style={{
                  width: `${confidence * 100}%`,
                  height: '100%',
                  background:
                    confidence > 0.6 ? '#22c55e' : '#ef4444',
                  transition: '0.2s'
                }}
              />
            </div>

            <div style={{ fontSize: '0.8rem', marginTop: 4 }}>
              {(confidence * 100).toFixed(1)}%
            </div>

            {/* EMOTION */}
            <div style={{ marginTop: 8 }}>
              Emotion: <b>{emotion || '...'}</b>
            </div>

            {/* LIVE SENTENCE */}
            <div style={{ marginTop: 10, fontSize: '0.85rem', color: '#aaa' }}>
              Live: {liveSentence || '...'}
            </div>
          </div>
        </div>
      </div>

      {/* 🔥 GLOBAL CLOSE BUTTON (CENTERED) */}
      <button
        onClick={() => setShowCamera(false)}
        style={{
          marginTop: 20,
          width: '100%',
          padding: '12px',
          borderRadius: '12px',
          background: '#1e293b',
          color: '#fff',
          border: 'none',
          fontWeight: 'bold',
          cursor: 'pointer'
        }}
      >
        Close
      </button>
    </div>
  </div>
)}
{showAuth && <AuthModal onClose={() => setShowAuth(false)} />}

  {showHistory && (
  <div
    style={{
      position: 'fixed',
      top: 0,
      left: 0,
      width: '100vw',
      height: '100vh',
      background: 'rgba(0,0,0,0.7)',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      zIndex: 9999
    }}
  >
    <div
      style={{
        background: '#0f172a',
        padding: 20,
        borderRadius: 16,
        width: '600px',
        maxWidth: '95%'
      }}
    >
      <h3>📜 Learning History</h3>

      {/* 🔍 SEARCH */}
      <input
        placeholder="Search history..."
        value={historySearch}
        onChange={(e) => setHistorySearch(e.target.value)}
        style={{
          width: '100%',
          padding: '10px',
          borderRadius: '10px',
          marginTop: 10,
          background: '#020617',
          border: '1px solid #333',
          color: '#fff'
        }}
      />

      {/* 🔥 HORIZONTAL SCROLL */}
      <div
        style={{
          display: 'flex',
          gap: 10,
          overflowX: 'auto',
          marginTop: 15,
          paddingBottom: 10
        }}
      >
        {progress.completedSigns
          .filter(word =>
            word.toLowerCase().includes(historySearch.toLowerCase())
          )
          .map((word, i) => (
            <div
              key={i}
              style={{
                padding: '8px 14px',
                borderRadius: '20px',
                background: '#1e293b',
                whiteSpace: 'nowrap',
                fontSize: '0.85rem'
              }}
            >
              ✅ {word}
            </div>
          ))}
      </div>

      {/* CLOSE */}
      <button
        onClick={() => setShowHistory(false)}
        style={{
          marginTop: 15,
          width: '100%',
          padding: '10px',
          borderRadius: '10px',
          background: '#1e293b',
          color: '#fff',
          border: 'none',
          cursor: 'pointer'
        }}
      >
        Close
      </button>
    </div>
  </div>
)}
    </div>
  )
}