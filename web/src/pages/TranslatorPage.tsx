import { useCallback, useEffect, useRef, useState } from 'react'
import LandmarkCanvas from '../components/LandmarkCanvas'
import SignBadge from '../components/SignBadge'
import SentenceBuilder from '../components/SentenceBuilder'

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

const SUPPORTED_SIGNS = [
  { key: 'hi', icon: '👋', label: 'Hi' },
  { key: 'iloveyou', icon: '🤟', label: 'I love you' },
  { key: 'thankyou', icon: '🙏', label: 'Thank you' },
  { key: 'goodbye', icon: '✌️', label: 'Goodbye' },
  { key: 'me', icon: '👆', label: 'Me' },
  { key: 'hungry', icon: '🍽️', label: 'Hungry' },
  { key: 'name', icon: '🏷️', label: 'Name' },
  { key: 'c', icon: '🤙', label: 'C' },
]

export default function TranslatorPage({ onAddHistory }: TranslatorPageProps) {
  const videoRef = useRef<HTMLVideoElement>(null)
  const captureCanvasRef = useRef<HTMLCanvasElement>(null)
  const panelRef = useRef<HTMLDivElement>(null)

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
          const res = await fetch('/api/detection/predict', { method: 'POST', body: fd })
          if (!res.ok) { isSending.current = false; return }
          const data = await res.json()

          setLandmarks(data.landmarks ?? [])
          processPrediction(data.prediction ?? '', data.confidence ?? 0)

          frameCount.current++
          const now = Date.now()
          if (now - lastFpsTime.current >= 1000) {
            setFps(frameCount.current)
            frameCount.current = 0
            lastFpsTime.current = now
          }
        } catch { /* network error */ }
        finally { isSending.current = false }
      }, 'image/jpeg', 0.8)
    }, INTERVAL_MS)

    return () => clearInterval(id)
  }, [cameraReady, processPrediction])

  // ── Phrase decay timer ────────────────────────────────────────
  useEffect(() => {
    const id = setInterval(() => {
      phrasesRef.current.forEach(p => { p.timer-- })
      phrasesRef.current = phrasesRef.current.filter(p => p.timer > 0)
      setSentence(phrasesRef.current.map(p => p.text).join(' • '))
    }, INTERVAL_MS)
    return () => clearInterval(id)
  }, [])

  const handleClear = () => {
    phrasesRef.current = []
    wordBufferRef.current = []
    historyRef.current = []
    setWordBuffer([])
    setSentence('')
    setCurrentWord('')
  }

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
              <div className="section-label">Supported Signs</div>
              <span className="text-dim" style={{ fontSize: '0.75rem' }}>{SUPPORTED_SIGNS.length} signs</span>
            </div>
            <div className="signs-grid">
              {SUPPORTED_SIGNS.map(s => (
                <div key={s.key} className="sign-chip">
                  <div className="sign-chip-icon">{s.icon}</div>
                  <div className="sign-chip-name">{s.label}</div>
                </div>
              ))}
            </div>
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
    </div>
  )
}
