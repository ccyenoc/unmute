import { useCallback, useEffect, useRef, useState } from 'react';
import LandmarkCanvas from '../components/LandmarkCanvas';
import SentenceBuilder from '../components/SentenceBuilder';
import SignBadge from '../components/SignBadge';

interface Landmark { x: number; y: number; z: number }

interface HistoryEntry {
  text: string
  timestamp: number
  type: 'phrase' | 'word'
}

interface TranslatorPageProps {
  onAddHistory: (entry: HistoryEntry) => void
}

const DIRECT_PHRASES: Record<string, string> = {
  hi: 'Hi',
  iloveyou: 'I love you',
  thankyou: 'Thank you',
  goodbye: 'Goodbye',
}

const HISTORY_MAXLEN = 12
const CONFIDENCE_THRESHOLD = 0.5
const PHRASE_DURATION_TICKS = 30
const INTERVAL_MS = 200


const EMOTION = [
  { key: 'happy', icon: '😊', label: 'Happy' },
  { key: 'sad', icon: '😢', label: 'Sad' },
  { key: 'angry', icon: '😠', label: 'Angry' },
  { key: 'fear', icon: '😨', label: 'Fear' },
  { key: 'surprise', icon: '😲', label: 'Surprise' },
  { key: 'disgust', icon: '🤢', label: 'Disgust' },
  { key: 'neutral', icon: '😐', label: 'Neutral' },
]


export default function TranslatorPage({ onAddHistory }: TranslatorPageProps) {
  const videoRef = useRef<HTMLVideoElement>(null)
  const captureCanvasRef = useRef<HTMLCanvasElement>(null)
  const panelRef = useRef<HTMLDivElement>(null)
  const [showPlayer, setShowPlayer] = useState(false)

  const videoPlayerRef = useRef<HTMLVideoElement>(null)
  const [currentPlayIndex, setCurrentPlayIndex] = useState(0)

  const [cameraReady, setCameraReady] = useState(false)
  const [cameraError, setCameraError] = useState('')
  const [panelSize, setPanelSize] = useState({ width: 0, height: 0 })

  const [landmarks, setLandmarks] = useState<Landmark[][]>([])
  const [currentWord, setCurrentWord] = useState('')
  const [confidence, setConfidence] = useState(0)
  const [sentence, setSentence] = useState('')
  const [wordBuffer, setWordBuffer] = useState<string[]>([])
  const [handDetected, setHandDetected] = useState(false)
  const [fps, setFps] = useState(0)

  // Internal refs (not re-rendered on every tick)
  const historyRef = useRef<string[]>([])
  const wordBufferRef = useRef<string[]>([])
  const phrasesRef = useRef<{ text: string; timer: number }[]>([])
  const cooldownRef = useRef(0)
  const noHandFrames = useRef(0)
  const lastWord = useRef('')
  const isSending = useRef(false)
  const frameCount = useRef(0)
  const lastFpsTime = useRef(Date.now())

  const [emotion, setEmotion] = useState('')
  const [interpretation, setInterpretation] = useState('')
  const [status, setStatus] = useState('')

  const [emotionConfidence, setEmotionConfidence] = useState(0)

  const [typedText, setTypedText] = useState('')
  const [playQueue, setPlayQueue] = useState<string[]>([])

  const normalizeText = (text: string) =>
  text.toLowerCase().trim().replace(/\s+/g, ' ')

 const handleTextSubmit = () => {
  const normalized = normalizeText(typedText)

  let videoKey = ''

  if (normalized === 'i am hungry') {
    videoKey = 'i_am_hungry'
  } else if (normalized === 'can i help you') {
    videoKey = 'can_i_help_you'
  } else if (normalized === 'sure') {
    videoKey = 'sure'
  } else {
    alert('No video available for this sentence')
    return
  }

  setPlayQueue([videoKey])
  setCurrentPlayIndex(0)
  setShowPlayer(true)
  setTypedText('')
}

  const handleClear = () => {
  setSentence('')
  setWordBuffer([])
}

  useEffect(() => {
  if (playQueue.length === 0) return

  const video = videoPlayerRef.current
  if (!video) return

  const word = playQueue[currentPlayIndex]
  if (!word) return

  video.src = `/videos/${word}.mp4`
  video.load() // 🔥 FORCE reload

  video.onerror = () => {
  console.error(`❌ Missing video: ${word}`)
}

  video.play().catch(() => {})

}, [playQueue, currentPlayIndex])

const handleVideoEnd = () => {
  if (currentPlayIndex < playQueue.length - 1) {
    setCurrentPlayIndex(prev => prev + 1)
  } else {
    setPlayQueue([])
    setCurrentPlayIndex(0)
    setShowPlayer(false) // 🔥 close popup
  }
}

  // ── Camera setup ──────────────────────────────────────────────
  useEffect(() => {
    let stream: MediaStream
    navigator.mediaDevices.getUserMedia({ video: { width: 640, height: 480, facingMode: 'user' } })
      .then(s => {
        stream = s
        if (videoRef.current) {
          videoRef.current.srcObject = s
          videoRef.current.play()
          setCameraReady(true)
        }
      })
      .catch(err => {
        setCameraError('Camera access denied. Please allow camera permissions and reload.')
        console.error(err)
      })
    return () => { stream?.getTracks().forEach(t => t.stop()) }
  }, [])

  // ── Panel size observer ───────────────────────────────────────
  useEffect(() => {
    if (!panelRef.current) return
    const ro = new ResizeObserver(entries => {
      const { width, height } = entries[0].contentRect
      setPanelSize({ width, height })
    })
    ro.observe(panelRef.current)
    return () => ro.disconnect()
  }, [])

  // ── Prediction logic (mirrors Python predict_webcam.py) ───────
  const processPrediction = useCallback((pred: string, conf: number) => {
    if (!pred || pred === 'No hand') {
      noHandFrames.current++
      if (noHandFrames.current > 15) {
        historyRef.current = []
        wordBufferRef.current = []
        setWordBuffer([])
      }
      setHandDetected(false)
      return
    }

    setHandDetected(true)
    noHandFrames.current = 0

    if (pred === 'Uncertain') {
      historyRef.current.push(pred)
      if (historyRef.current.length > HISTORY_MAXLEN) historyRef.current.shift()
      return
    }

    historyRef.current.push(pred)
    if (historyRef.current.length > HISTORY_MAXLEN) historyRef.current.shift()

    const valid = historyRef.current.filter(p => p !== 'Uncertain')
    if (valid.length === 0) return

    const counts: Record<string, number> = {}
    valid.forEach(p => { counts[p] = (counts[p] || 0) + 1 })
    const finalPred = Object.keys(counts).reduce((a, b) => counts[a] > counts[b] ? a : b)
    const freq = counts[finalPred] / valid.length

    if (finalPred !== lastWord.current) {
      setCurrentWord(finalPred)
      setConfidence(conf)
      lastWord.current = finalPred
    }

    if (cooldownRef.current > 0) { cooldownRef.current--; return }
    if (freq < 0.4) return

    // Direct phrase
    if (DIRECT_PHRASES[finalPred]) {
      const text = DIRECT_PHRASES[finalPred]
      phrasesRef.current.push({ text, timer: PHRASE_DURATION_TICKS })
      onAddHistory({ text, timestamp: Date.now(), type: 'phrase' })
      historyRef.current = []
      wordBufferRef.current = []
      setWordBuffer([])
      cooldownRef.current = 30
      return
    }

    // Word buffer combos
    if (wordBufferRef.current.length === 0) {
      wordBufferRef.current.push(finalPred)
      setWordBuffer([...wordBufferRef.current])
    } else {
      const prev = wordBufferRef.current[wordBufferRef.current.length - 1]
      let composed: string | null = null

      if (prev === 'me' && finalPred === 'hungry') composed = 'I am hungry'
      else if (prev === 'me' && finalPred === 'tired') composed = 'I am tired'
      else if (prev === 'name') composed = `My name is ${finalPred.toUpperCase()}`

      if (composed) {
        phrasesRef.current.push({ text: composed, timer: PHRASE_DURATION_TICKS })
        onAddHistory({ text: composed, timestamp: Date.now(), type: 'phrase' })
        wordBufferRef.current = []
        setWordBuffer([])
      } else {
        wordBufferRef.current.push(finalPred)
        setWordBuffer([...wordBufferRef.current])
      }
    }
    cooldownRef.current = 15
  }, [onAddHistory])

  // ── Frame capture + send loop ─────────────────────────────────
  useEffect(() => {
    const id = setInterval(async () => {
      const video = videoRef.current
      const canvas = captureCanvasRef.current
      if (!video || !canvas || !cameraReady || isSending.current) return

      const ctx = canvas.getContext('2d')
      if (!ctx) return

      canvas.width = 640
      canvas.height = 480
      ctx.drawImage(video, 0, 0, 640, 480)

      isSending.current = true
      canvas.toBlob(async blob => {
  if (!blob) { isSending.current = false; return }

  try {
    const fd = new FormData()
    fd.append('file', blob, 'frame.jpg')

    // 🔹 1. Sign detection
    const res = await fetch('/api/detection/predict', {
      method: 'POST',
      body: fd
    })

    if (!res.ok) { isSending.current = false; return }

    const data = await res.json()

    setLandmarks(data.landmarks ?? [])
    processPrediction(data.prediction ?? '', data.confidence ?? 0)

    // 🔹 2. Emotion detection
    const emotionRes = await fetch('/api/emotion/predict', {
      method: 'POST',
      body: fd
    })

   if (emotionRes.ok) {
    const emotionData = await emotionRes.json()
     setEmotion(emotionData.emotion ?? '')
     setEmotionConfidence(emotionData.confidence ?? 0)
   }

    // 🔹 FPS tracking
    frameCount.current++
    const now = Date.now()
    if (now - lastFpsTime.current >= 1000) {
      setFps(frameCount.current)
      frameCount.current = 0
      lastFpsTime.current = now
    }

  } catch (e) {
    console.error(e)
  } finally {
    isSending.current = false
  }
}, 'image/jpeg', 0.8)
}, INTERVAL_MS
  
)


  return () => clearInterval(id) 
}, [cameraReady, processPrediction])



  const isIdle = !currentWord || currentWord === '...' || currentWord === 'No hand' || currentWord === 'Uncertain'

  return (
    <div className="page">
      <div className="translator-layout">
        {/* ── Webcam Panel ── */}
        <div
          ref={panelRef}
          className={`webcam-panel ${handDetected ? 'hand-detected' : ''}`}
        >
          {cameraError ? (
            <div className="webcam-no-camera">
              <div className="icon">📷</div>
              <h3>Camera Unavailable</h3>
              <p>{cameraError}</p>
            </div>
          ) : (
            <>
              <video
                ref={videoRef}
                className="webcam-video"
                autoPlay
                playsInline
                muted
              />
              {panelSize.width > 0 && (
                <LandmarkCanvas
                  landmarks={landmarks}
                  width={panelSize.width}
                  height={panelSize.height}
                  mirrored={true}
                />
              )}
              <div className="webcam-overlay-badge">
                <div className={`status-dot ${handDetected ? 'online' : 'offline'}`} style={{ width: 8, height: 8 }} />
                <span>{handDetected ? 'Hand detected' : 'No hand'}</span>
              </div>
              <div className="webcam-fps">{fps} fps</div>
            </>
          )}
        </div>

        {/* ── Control Panel ── */}
        <div className="control-panel">
          <SignBadge word={isIdle ? '...' : currentWord} confidence={confidence} />

          <SentenceBuilder
            sentence={sentence}
            wordBuffer={wordBuffer}
            onClear={handleClear}
          />

          <div className="card">
  <div className="section-header">
    <div className="section-label">Detected Emotion</div>
  </div>

  <div className="signs-grid" style={{ textAlign: 'center' }}>
    
    {/* Emoji */}
    <div style={{ fontSize: '2rem', marginBottom: '8px' }}>
      {emotion === 'happy' && '😊'}
      {emotion === 'sad' && '😢'}
      {emotion === 'angry' && '😠'}
      {emotion === 'fear' && '😨'}
      {emotion === 'surprise' && '😲'}
      {emotion === 'disgust' && '🤢'}
      {emotion === 'neutral' && '😐'}
    </div>

    {/* Label */}
    <div style={{ fontWeight: 'bold' }}>
      {emotion || 'No emotion detected'}
    </div>

    {/* Optional confidence */}
    <div style={{ fontSize: '0.75rem', color: 'var(--text-dim)' }}>
      {emotionConfidence ? `Confidence: ${(emotionConfidence * 100).toFixed(1)}%` : ''}
    </div>

  </div>
</div>

          <div className="card">
  <div className="section-header">
    <div className="section-label">Text → Sign</div>
  </div>

  <input
    type="text"
    value={typedText}
    onChange={(e) => setTypedText(e.target.value)}
    onKeyDown={(e) => {
      if (e.key === 'Enter') handleTextSubmit()
    }}
    placeholder="Type sentence..."
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

          <div className="card" style={{ fontSize: '0.8rem', color: 'var(--text-dim)', lineHeight: 1.7 }}>
            <strong style={{ color: 'var(--text-muted)', display: 'block', marginBottom: 6 }}>💡 Combos</strong>
            <span>Me + Hungry → <em style={{ color: 'var(--accent-2)' }}>I am hungry</em></span><br />
            <span>Name + C → <em style={{ color: 'var(--accent-2)' }}>My name is C</em></span>
          </div>
        </div>
      </div>

      {/* Hidden capture canvas */}
      <canvas ref={captureCanvasRef} style={{ display: 'none' }} />

      {showPlayer && (
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
        width: '500px',
        maxWidth: '90%'
      }}
    >
      {/* Close button */}
      <div style={{ textAlign: 'right' }}>
       <button
    onClick={() => {
      setShowPlayer(false)
      setPlayQueue([])
      setCurrentPlayIndex(0)

      if (videoPlayerRef.current) {
        videoPlayerRef.current.pause()
        videoPlayerRef.current.currentTime = 0
      }
    }}
        >
          ✕
        </button>
      </div>

      {/* Video */}
      <video
        ref={videoPlayerRef}
        onEnded={handleVideoEnd}
        autoPlay
        style={{
          width: '100%',
          borderRadius: '12px',
          background: '#000'
        }}
      />

      {/* Label */}
      <div style={{ marginTop: 10, color: '#aaa', textAlign: 'center' }}>
        Playing: {playQueue[currentPlayIndex]}
      </div>
    </div>
  </div>
)}

    </div>
  )
}
