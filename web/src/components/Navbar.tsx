import StatusIndicator from './StatusIndicator'

type Page = 'translator' | 'history' | 'about'

interface NavbarProps {
  page: Page
  onNav: (page: Page) => void
}

export default function Navbar({ page, onNav }: NavbarProps) {
  return (
    <nav className="navbar">
      <a className="navbar-logo" href="#" onClick={e => { e.preventDefault(); onNav('translator') }}>
        <div className="navbar-logo-icon">🤟</div>
        <span className="navbar-logo-text">Unmute</span>
      </a>

      <div className="navbar-nav">
        {(['translator', 'history', 'about'] as Page[]).map(p => (
          <a
            key={p}
            href="#"
            className={`nav-link ${page === p ? 'active' : ''}`}
            onClick={e => { e.preventDefault(); onNav(p) }}
          >
            {p === 'translator' && '🎥 Translate'}
            {p === 'history' && '📋 History'}
            {p === 'about' && 'ℹ️ About'}
          </a>
        ))}
      </div>

      <div className="navbar-right">
        <StatusIndicator />
      </div>
    </nav>
  )
}
