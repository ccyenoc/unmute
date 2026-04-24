export default function AboutPage() {
  const signs = [
    { emoji: '👋', name: 'Hi', desc: 'Wave your open hand', key: 'hi' },
    { emoji: '🤟', name: 'I Love You', desc: 'Extend thumb, index & pinky', key: 'iloveyou' },
    { emoji: '🙏', name: 'Thank You', desc: 'Fingers to chin, move out', key: 'thankyou' },
    { emoji: '✌️', name: 'Goodbye', desc: 'Wave or peace sign', key: 'goodbye' },
    { emoji: '👆', name: 'Me', desc: 'Point index finger at yourself', key: 'me' },
    { emoji: '🍽️', name: 'Hungry', desc: 'Circle fist on stomach', key: 'hungry' },
    { emoji: '🏷️', name: 'Name', desc: 'Tap middle fingers together', key: 'name' },
    { emoji: '🤙', name: 'C', desc: 'Curve hand into letter C', key: 'c' },
  ]

  const combos = [
    { signs: 'Me + Hungry', result: '"I am hungry"', emoji: '🍽️' },
    { signs: 'Name + C', result: '"My name is C"', emoji: '🏷️' },
  ]

  const steps = [
    { num: '01', title: 'Camera capture', desc: 'Your webcam streams video to the browser in real time.' },
    { num: '02', title: 'Frame extraction', desc: 'A frame is captured every 200ms and sent as JPEG to the FastAPI backend.' },
    { num: '03', title: 'Hand detection', desc: 'MediaPipe detects hand landmarks — 21 x,y,z points per hand.' },
    { num: '04', title: 'AI prediction', desc: 'A RandomForest classifier predicts the sign from the landmark coordinates.' },
    { num: '05', title: 'Smoothing', desc: 'A 12-frame rolling history vote eliminates flicker and noise.' },
    { num: '06', title: 'Phrase assembly', desc: 'Words are combined into full phrases using a rule-based buffer.' },
  ]

  return (
    <div className="page about-page">
      <div className="about-hero">
        <h1>About <span className="text-accent">Unmute</span></h1>
        <p>
          A real-time sign language translator powered by MediaPipe hand tracking and a custom-trained machine learning model.
          Show your hands to the camera — Unmute will translate your signs into text instantly.
        </p>
      </div>

      <h2 style={{ fontFamily: 'var(--font-heading)', fontSize: '1.1rem', color: 'var(--text-muted)', marginBottom: 16, letterSpacing: '-0.01em' }}>
        Supported Signs
      </h2>
      <div className="about-grid">
        {signs.map(s => (
          <div key={s.key} className="about-sign-card">
            <div className="about-sign-emoji">{s.emoji}</div>
            <div className="about-sign-name">{s.name}</div>
            <div className="about-sign-desc">{s.desc}</div>
          </div>
        ))}
      </div>

      <h2 className="about-section-title">Sign Combos</h2>
      <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
        {combos.map((c, i) => (
          <div key={i} className="card" style={{ display: 'flex', alignItems: 'center', gap: 16 }}>
            <span style={{ fontSize: '1.8rem' }}>{c.emoji}</span>
            <div>
              <div style={{ fontFamily: 'var(--font-heading)', fontWeight: 600, color: 'var(--text)', marginBottom: 2 }}>
                {c.signs}
              </div>
              <div style={{ color: 'var(--accent-2)', fontSize: '0.9rem' }}>{c.result}</div>
            </div>
          </div>
        ))}
      </div>

      <h2 className="about-section-title">How It Works</h2>
      <div className="how-it-works">
        {steps.map(s => (
          <div key={s.num} className="how-step">
            <div className="how-step-num">{s.num}</div>
            <h4>{s.title}</h4>
            <p>{s.desc}</p>
          </div>
        ))}
      </div>

      <div className="card mt-4" style={{ marginTop: 32 }}>
        <h3 style={{ color: 'var(--text)', marginBottom: 8 }}>Tech Stack</h3>
        <div style={{ display: 'flex', flexWrap: 'wrap', gap: 8, marginTop: 8 }}>
          {['FastAPI', 'MediaPipe', 'scikit-learn', 'RandomForest', 'React', 'Vite', 'TypeScript', 'HTML5 Canvas'].map(t => (
            <span key={t} className="sentence-chip">{t}</span>
          ))}
        </div>
      </div>
    </div>
  )
}
