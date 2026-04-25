import { useState } from 'react'
import Navbar from './components/Navbar'
import TranslatorPage from './pages/TranslatorPage'
import HistoryPage from './pages/HistoryPage'
import AboutPage from './pages/AboutPage'

type Page = 'translator' | 'history' | 'about'

interface HistoryEntry {
  text: string
  timestamp: number
  type: 'phrase' | 'word'
}

export default function App() {
  const [page, setPage] = useState<Page>('translator')
  const [history, setHistory] = useState<HistoryEntry[]>([])

  const addHistory = (entry: HistoryEntry) => {
    setHistory(prev => [...prev, entry])
  }

  const clearHistory = () => setHistory([])

  return (
    <div className="app">
      <Navbar page={page} onNav={setPage} />

      {page === 'translator' && <TranslatorPage onAddHistory={addHistory} />}
      {page === 'history' && <HistoryPage history={history} onClear={clearHistory} />}
      {page === 'about' && <AboutPage />}
    </div>
  )
}
