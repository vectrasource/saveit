import { Link, useLocation } from 'react-router-dom'
import { TOOLS } from '../App.jsx'

export default function Layout({ children }) {
  const location = useLocation()

  return (
    <div style={{ minHeight: '100vh', display: 'flex', flexDirection: 'column', background: '#0d0d14', color: '#f0f0f0', fontFamily: "'DM Sans', sans-serif" }}>
      <style>{`
        @import url('https://fonts.googleapis.com/css2?family=Unbounded:wght@700;900&family=DM+Sans:wght@300;400;500;600&display=swap');
        *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }
        body { background: #0d0d14; }
        a { color: inherit; text-decoration: none; }
        button { font-family: 'DM Sans', sans-serif; }
        input { font-family: 'DM Sans', sans-serif; }
        @keyframes spin { from{transform:rotate(0deg)} to{transform:rotate(360deg)} }
        @keyframes fadeUp { from{opacity:0;transform:translateY(20px)} to{opacity:1;transform:translateY(0)} }
        @keyframes pulse { 0%,100%{opacity:1} 50%{opacity:0.4} }
        .tool-tab:hover { background: rgba(255,255,255,0.1) !important; color: #fff !important; }
        .footer-link:hover { color: #ccc !important; }
        input::placeholder { color: #555; }
      `}</style>

      {/* Header */}
      <header style={{
        background: 'rgba(13,13,20,0.95)', backdropFilter: 'blur(20px)',
        borderBottom: '1px solid rgba(255,255,255,0.06)',
        padding: '0 20px', position: 'sticky', top: 0, zIndex: 100,
      }}>
        <div style={{ maxWidth: 900, margin: '0 auto', height: 56, display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
          <Link to="/" style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
            <div style={{
              width: 30, height: 30, borderRadius: 8,
              background: 'linear-gradient(135deg, #E1306C, #833AB4)',
              display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: 14,
            }}>⬇</div>
            <span style={{ fontFamily: 'Unbounded', fontWeight: 700, fontSize: 16, letterSpacing: '-0.5px' }}>SaveIt</span>
          </Link>
          <nav style={{ display: 'flex', gap: 2, overflowX: 'auto', alignItems: 'center' }}>
            {TOOLS.map(t => (
              <Link key={t.path} to={t.path} className="tool-tab" style={{
                padding: '6px 12px', borderRadius: 8, fontSize: 13, fontWeight: 500,
                whiteSpace: 'nowrap', transition: 'all 0.15s',
                background: location.pathname === t.path ? 'rgba(255,255,255,0.1)' : 'transparent',
                color: location.pathname === t.path ? '#fff' : '#666',
              }}>{t.label}</Link>
            ))}
          </nav>
        </div>
      </header>

      <main style={{ flex: 1 }}>{children}</main>

      {/* Footer */}
      <footer style={{ borderTop: '1px solid rgba(255,255,255,0.05)', padding: '36px 20px', background: 'rgba(0,0,0,0.3)' }}>
        <div style={{ maxWidth: 900, margin: '0 auto' }}>
          <div style={{ display: 'flex', flexWrap: 'wrap', gap: 32, marginBottom: 28 }}>
            <div style={{ minWidth: 200 }}>
              <div style={{ fontFamily: 'Unbounded', fontWeight: 700, fontSize: 15, marginBottom: 10 }}>SaveIt</div>
              <p style={{ color: '#444', fontSize: 13, lineHeight: 1.7, maxWidth: 240 }}>
                Free tool to download Instagram & YouTube videos. No signup, no watermark.
              </p>
            </div>
            <div>
              <div style={{ fontSize: 11, color: '#555', fontWeight: 600, letterSpacing: '1px', textTransform: 'uppercase', marginBottom: 12 }}>Tools</div>
              <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
                {TOOLS.map(t => (
                  <Link key={t.path} to={t.path} className="footer-link" style={{ color: '#555', fontSize: 13, transition: 'color 0.2s' }}>
                    {t.label} Downloader
                  </Link>
                ))}
              </div>
            </div>
          </div>
          <div style={{ borderTop: '1px solid rgba(255,255,255,0.05)', paddingTop: 20, display: 'flex', flexWrap: 'wrap', gap: 12, justifyContent: 'space-between', color: '#333', fontSize: 12 }}>
            <span>© {new Date().getFullYear()} SaveIt — Not affiliated with Instagram™ or YouTube™</span>
            <span>For personal use only. We do not store any files.</span>
          </div>
        </div>
      </footer>
    </div>
  )
}
