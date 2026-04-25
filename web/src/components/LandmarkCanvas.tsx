import { useEffect, useRef } from 'react'

interface Landmark {
  x: number
  y: number
  z: number
}

interface LandmarkCanvasProps {
  landmarks: Landmark[][]
  width: number
  height: number
  mirrored?: boolean
}

const CONNECTIONS = [
  [0,1],[1,2],[2,3],[3,4],
  [0,5],[5,6],[6,7],[7,8],
  [5,9],[9,10],[10,11],[11,12],
  [9,13],[13,14],[14,15],[15,16],
  [13,17],[17,18],[18,19],[19,20],
  [0,17]
]

export default function LandmarkCanvas({ landmarks, width, height, mirrored = true }: LandmarkCanvasProps) {
  const canvasRef = useRef<HTMLCanvasElement>(null)

  useEffect(() => {
    const canvas = canvasRef.current
    if (!canvas) return
    const ctx = canvas.getContext('2d')
    if (!ctx) return

    ctx.clearRect(0, 0, width, height)

    if (!landmarks || landmarks.length === 0) return

    for (const hand of landmarks) {
      // Draw connections
      ctx.strokeStyle = '#22c55e'
      ctx.lineWidth = 2.5
      ctx.lineCap = 'round'

      for (const [a, b] of CONNECTIONS) {
        const lmA = hand[a]
        const lmB = hand[b]
        if (!lmA || !lmB) continue

        const x1 = mirrored ? (1 - lmA.x) * width : lmA.x * width
        const y1 = lmA.y * height
        const x2 = mirrored ? (1 - lmB.x) * width : lmB.x * width
        const y2 = lmB.y * height

        ctx.beginPath()
        ctx.moveTo(x1, y1)
        ctx.lineTo(x2, y2)
        ctx.stroke()
      }

      // Draw joints
      for (let i = 0; i < hand.length; i++) {
        const lm = hand[i]
        const cx = mirrored ? (1 - lm.x) * width : lm.x * width
        const cy = lm.y * height
        const isFingerTip = [4, 8, 12, 16, 20].includes(i)

        // Outer glow
        ctx.beginPath()
        ctx.arc(cx, cy, isFingerTip ? 8 : 5, 0, Math.PI * 2)
        ctx.fillStyle = isFingerTip ? 'rgba(168,85,247,0.25)' : 'rgba(34,197,94,0.15)'
        ctx.fill()

        // Inner dot
        ctx.beginPath()
        ctx.arc(cx, cy, isFingerTip ? 4 : 3, 0, Math.PI * 2)
        ctx.fillStyle = isFingerTip ? '#a855f7' : '#22c55e'
        ctx.fill()
      }
    }
  }, [landmarks, width, height, mirrored])

  return (
    <canvas
      ref={canvasRef}
      className="webcam-canvas"
      width={width}
      height={height}
      style={{ position: 'absolute', inset: 0, pointerEvents: 'none' }}
    />
  )
}
