import {
  doc,
  updateDoc
} from 'firebase/firestore'
import { useEffect, useRef, useState } from 'react'
import { db } from '../firebase'



interface SignItem {
  id: string
  word: string
  videoUrl: string
}

interface UserProgress {
  points: number
  streak: number
  completedSigns: string[]
}

export default function LearnPage() {
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
    points: 30, // 🔥 DEMO DATA (looks nicer)
    streak: 3,
    completedSigns: ['hi', 'thankyou']
  })
  const [search, setSearch] = useState('')

  const userId = 'demoUser'
  const [selectedDay, setSelectedDay] = useState<number | null>(null)
  const [showCamera, setShowCamera] = useState(false)
  const daySigns = selectedDay
  ? signs.filter(s =>
      dayMap[selectedDay]?.some(
        w => normalize(w) === normalize(s.word)
      )
    )
  : []

  const [currentWord, setCurrentWord] = useState('')
const [confidence, setConfidence] = useState(0)
const [emotion, setEmotion] = useState('')

  // ── Fetch signs ──
 useEffect(() => {
  setSigns([
    { id: '1', word: 'hi', videoUrl: '/videos/hi.mp4' },
    { id: '2', word: 'bye', videoUrl: '/videos/bye.mp4' },
    { id: '3', word: 'thank you', videoUrl: '/videos/thank_you.mp4' },
    { id: '4', word: 'sorry', videoUrl: '/videos/sorry.mp4' },
    { id: '5', word: 'hungry', videoUrl: '/videos/hungry.mp4' },
    { id: '6', word: 'help', videoUrl: '/videos/help.mp4' }
  ])
}, [])

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

        setCurrentWord(data.prediction ?? '')
        setConfidence(data.confidence ?? 0)

        // 🔥 EMOTION DETECTION
        const emoRes = await fetch('/api/emotion/predict', {
          method: 'POST',
          body: fd
        })

        if (emoRes.ok) {
          const emoData = await emoRes.json()
          setEmotion(emoData.emotion ?? '')
        }

        // ✅ AUTO PASS
        if (
          data.prediction === current?.word &&
          data.confidence > 0.6
        ) {
          alert('✅ Correct!')
          handlePracticeSuccess()
          setShowCamera(false)
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

    if (!progress.completedSigns.includes(current.word)) {
      const updated = {
        ...progress,
        points: progress.points + 10,
        completedSigns: [...progress.completedSigns, current.word]
      }

      setProgress(updated)
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

  return (
    <div className="page">
      <h1>Learn Sign Language</h1>

      {/* ── SEARCH BAR ── */}
      <div className="card" style={{ marginBottom: 20 }}>
        <input
          placeholder="🔍 Search signs..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          style={{
            width: '100%',
            padding: '10px',
            borderRadius: '10px',
            border: '1px solid #333',
            background: '#0f172a',
            color: '#fff'
          }}
        />
      </div>

      {/* ── STATS ── */}
      <div
        style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(4, 1fr)',
          gap: 16,
          marginBottom: 20
        }}
      >
        <div className="card" style={{ textAlign: 'center' }}>
          ✨ <br /> {progress.points} XP
        </div>
        <div className="card" style={{ textAlign: 'center' }}>
          🎯 <br /> Level {Math.floor(progress.points / 50) + 1}
        </div>
        <div className="card" style={{ textAlign: 'center' }}>
          🔥 <br /> {progress.streak} days
        </div>
        <div className="card" style={{ textAlign: 'center' }}>
          🏆 <br /> {Math.floor(progress.completedSigns.length / 2)} badges
        </div>
      </div>

      {/* ── LEARNING PATH ── */}
      <div className="card" style={{ marginBottom: 20 }}>
        <h3>📅 Learning Path</h3>

        {/* DAY 1 */}
        <div
          onClick={() => {
            console.log('clicked day 1')
            setSelectedDay(1)}}
          style={{
            padding: '12px',
            marginTop: 10,
            borderRadius: '10px',
            background: '#1e293b',
            cursor: 'pointer'
          }}
        >
          🔓 Day 1 — Basics  
          <div style={{ fontSize: '0.8rem', color: '#aaa' }}>
            hi • bye • thank you • sorry
          </div>
        </div>

        {/* DAY 2 */}
        <div
          onClick={() => {
    if (day2Unlocked) setSelectedDay(2)
  }}
          style={{
            padding: '12px',
            marginTop: 10,
            borderRadius: '10px',
            background: day2Unlocked ? '#1e293b' : '#111',
            opacity: day2Unlocked ? 1 : 0.4
          }}
        >
          {day2Unlocked ? '🔓' : '🔒'} Day 2 — Needs  
          <div style={{ fontSize: '0.8rem', color: '#aaa' }}>
            hungry • tired • help
          </div>
        </div>

        {/* DAY 3 */}
        <div
          onClick={() => {
    if (day3Unlocked) setSelectedDay(3)
  }}
          style={{
            padding: '12px',
            marginTop: 10,
            borderRadius: '10px',
            background: day3Unlocked ? '#1e293b' : '#111',
            opacity: day3Unlocked ? 1 : 0.4
          }}
        >
          {day3Unlocked ? '🔓' : '🔒'} Day 3 — Responses  
          <div style={{ fontSize: '0.8rem', color: '#aaa' }}>
            yes • no • sure
          </div>
        </div>

      
      </div>

      {selectedDay && (
        
  <div className="card" style={{ marginTop: 20 }}>
    <h3>📘 Day {selectedDay} Practice</h3>

    <div style={{ display: 'flex', flexWrap: 'wrap', gap: 10 }}>
      {daySigns.map(sign => (
        <button
          key={sign.id}
          onClick={() => {
            setShowCamera(true)
            setCurrent(sign)}}
          style={{
            padding: '8px 12px',
            borderRadius: '8px',
            border: '1px solid #333',
            background: '#0f172a',
            color: '#fff',
            cursor: 'pointer'
          }}
        >
          {sign.word}
        </button>
      ))}
    </div>
  </div>
)}

      {/* ── SEARCH RESULTS / SIGN LIST ── */}
      <div className="card">
        <h3>🎯 Practice Signs</h3>

        <div style={{ display: 'flex', flexWrap: 'wrap', gap: 10 }}>
          {filteredSigns.map(sign => (
            <button
              key={sign.id}
              onClick={() => {
                setShowCamera(true)
                setCurrent(sign)}}
              style={{
                padding: '8px 12px',
                borderRadius: '8px',
                border: '1px solid #333',
                background: '#0f172a',
                color: '#fff',
                cursor: 'pointer'
              }}
            >
              {sign.word}
            </button>
          ))}
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
        maxWidth: '95%',
        display: 'flex',
        gap: '20px'
      }}
    >
      {/* LEFT: VIDEO */}
      <div style={{ flex: 1 }}>
        <h3 style={{ marginBottom: 10 }}>{current?.word}</h3>

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
          <div>Prediction: {currentWord}</div>
          <div>
            Confidence: {(confidence * 100).toFixed(1)}%
          </div>
          <div>Emotion: {emotion || '...'}</div>
        </div>

        <button
          onClick={() => setShowCamera(false)}
          style={{
            marginTop: 10,
            width: '100%',
            padding: '10px',
            borderRadius: '10px',
            background: '#1e293b',
            color: '#fff',
            border: 'none'
          }}
        >
          Close
        </button>
      </div>
    </div>
  </div>
)}
    </div>
  )
}