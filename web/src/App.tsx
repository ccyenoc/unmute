import { useState } from 'react'
import Navbar from './components/Navbar'
import AboutPage from './pages/AboutPage'
import LearnPage from './pages/LearnPage'
import TranslatorPage from './pages/TranslatorPage'

type Page = 'translator' | 'learn' | 'about'

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

  return (
    <div className="app">
      <Navbar page={page} onNav={setPage} />

      {page === 'translator' && (
        <TranslatorPage onAddHistory={addHistory} />
      )}

      {page === 'learn' && (
        <LearnPage />
      )}

      {page === 'about' && (
        <AboutPage />
      )}
    </div>
  )
}
