interface SentenceBuilderProps {
  sentence: string
  wordBuffer: string[]
  onClear: () => void
}

const DISPLAY_NAMES: Record<string, string> = {
  hi: 'Hi', iloveyou: 'I Love You', thankyou: 'Thank You',
  goodbye: 'Goodbye', me: 'Me', hungry: 'Hungry', name: 'Name', c: 'C',
}

export default function SentenceBuilder({ sentence, wordBuffer, onClear }: SentenceBuilderProps) {
  const hasContent = sentence || wordBuffer.length > 0

  return (
    <div className="sentence-builder">
      <div className="sentence-header">
        <div className="sentence-label">Sentence</div>
        {hasContent && (
          <button className="btn-clear" onClick={onClear}>Clear</button>
        )}
      </div>

      <div className={`sentence-text ${!sentence ? 'detecting' : ''}`}>
        {sentence || 'Waiting for signs...'}
      </div>

      {wordBuffer.length > 0 && (
        <div className="sentence-chips">
          {wordBuffer.map((w, i) => (
            <span key={i} className="sentence-chip">
              {DISPLAY_NAMES[w] ?? w}
            </span>
          ))}
          <span className="sentence-chip" style={{ opacity: 0.4 }}>...</span>
        </div>
      )}
    </div>
  )
}
