import { useEffect, useRef } from 'react'

interface SignBadgeProps {
  word: string
  confidence: number
}

const DISPLAY_NAMES: Record<string, string> = {
  hi: 'Hi',
  iloveyou: 'I Love You',
  thankyou: 'Thank You',
  goodbye: 'Goodbye',
  me: 'Me',
  hungry: 'Hungry',
  name: 'Name',
  c: 'C',
  Uncertain: '...',
  'No hand': '...',
  '...': '...',
}

export default function SignBadge({ word, confidence }: SignBadgeProps) {
  const isIdle = !word || word === '...' || word === 'No hand' || word === 'Uncertain'
  const prevWordRef = useRef('')
  const badgeRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    if (!isIdle && word !== prevWordRef.current && badgeRef.current) {
      badgeRef.current.classList.remove('pop')
      void badgeRef.current.offsetWidth // force reflow
      badgeRef.current.classList.add('pop')
      prevWordRef.current = word
    }
  }, [word, isIdle])

  const displayWord = DISPLAY_NAMES[word] ?? word
  const pct = Math.round(confidence * 100)

  return (
    <div className="sign-badge">
      <div className="sign-badge-label">Detected Sign</div>
      <div ref={badgeRef} className={`sign-badge-word ${isIdle ? 'idle' : ''}`}>
        {isIdle ? 'Show your hand' : displayWord}
      </div>
      {!isIdle && (
        <div className="confidence-bar-wrap">
          <div className="confidence-bar-label">
            <span>Confidence</span>
            <span>{pct}%</span>
          </div>
          <div className="confidence-bar">
            <div
              className="confidence-bar-fill"
              style={{ width: `${pct}%` }}
            />
          </div>
        </div>
      )}
    </div>
  )
}
