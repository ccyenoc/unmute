interface HistoryEntry {
  text: string
  timestamp: number
  type: 'phrase' | 'word'
}

interface HistoryPageProps {
  history: HistoryEntry[]
  onClear: () => void
}

function formatTime(ts: number): string {
  return new Date(ts).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' })
}

export default function HistoryPage({ history, onClear }: HistoryPageProps) {
  return (
    <div className="page history-page">
      <div className="history-header">
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-end' }}>
          <div>
            <h1>Session History</h1>
            <p className="mt-1">All phrases detected in this session.</p>
          </div>
          {history.length > 0 && (
            <button className="btn-danger" onClick={onClear}>Clear All</button>
          )}
        </div>
      </div>

      {history.length === 0 ? (
        <div className="history-empty">
          <div className="icon">🤟</div>
          <h3>No phrases yet</h3>
          <p>Detected phrases will appear here as you sign.</p>
        </div>
      ) : (
        <div className="history-list">
          {[...history].reverse().map((entry, i) => (
            <div key={i} className="history-item">
              <div className="history-item-text">{entry.text}</div>
              <div className="history-item-meta">
                <span className="history-badge">{entry.type}</span>
                <span className="history-item-time">{formatTime(entry.timestamp)}</span>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
