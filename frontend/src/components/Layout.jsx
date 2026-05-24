import { useState } from 'react'
import { Link, useLocation } from 'react-router-dom'

const NAV_GROUPS = [
  {
    label: 'Instagram',
    color: '#E1306C',
    links: [
      { path: '/', label: 'Reels' },
      { path: '/instagram-video-downloader', label: 'Video' },
      { path: '/instagram-photo-downloader', label: 'Photo' },
      { path: '/instagram-story-downloader', label: 'Story' },
    ]
  },
  {
    label: 'YouTube',
    color: '#FF0000',
    links: [
      { path: '/youtube-video-downloader', label: 'Video' },
      { path: '/youtube-audio-downloader', label: 'MP3' },
    ]
  }
]

export default function Layout({ children }) {
  const [menuOpen, setMenuOpen] = useState(false)
  const location = useLocation()

  return (
    <div style={{ minHeight: '100vh', display: 'flex', flexDirection: 'column' }}>
      {/* Ambient background */}
      <div style={{
        position: 'fixed', inset: 0, zIndex: 0, pointerEvents: 'none', overflow: 'hidden'
      }}>
        <div style={{
          position: 'absolute', top: '-30%', left: '-20%',
          width: '60vw', height: '60vw', borderRadius: '50%',
          background: 'radial-gradient(circle, rgba(225,48,108,0.12) 0%, transparent 65%)',
        }} />
        <div style={{
          position: 'absolute', bottom: '-20%', right: '-15%',
          width: '50vw', height: '50vw', borderRadius: '50%',
          background: 'radial-gradient(circle, rgba(131,58,180,0.1) 0%, transparent 65%)',
        }} />
      </div>

      {/* Header */}
      <header style={{
        position: 'sticky', top: 0, zIndex: 100,
        background: 'rgba(8,8,16,0.85)', backdropFilter: 'blur(20px)',
        borderBottom: '1px solid rgba(255,255,255,0.06)',
        padding: '0 24px',
      }}>
        <div style={{
          maxWidth: 1100, margin: '0 auto',
          height: 60, display: 'flex', alignItems: 'center', justifyContent: 'space-between',
        }}>
          {/* Logo */}
          <Link to="/" style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
            <div style={{
              width: 32, height: 32, borderRadius: 8,
              background: 'linear-gradient(135deg, #E1306C, #833AB4)',
              display: 'flex', alignItems: 'center', justifyContent: 'center',
              fontSize: 16, fontWeight: 900,
            }}>⬇</div>
            <span style={{
              fontFamily: 'var(--font-display)', fontWeight: 700,
              fontSize: 18, letterSpacing: '-0.5px',
              background: 'linear-gradient(135deg, #fff 40%, #888)',
              WebkitBackgroundClip: 'text', WebkitTextFillColor: 'transparent',
            }}>SaveIt</span>
          </Link>

          {/* Desktop nav */}
          <nav style={{ display: 'flex', gap: 4, alignItems: 'center' }}>
            {NAV_GROUPS.map(group => (
              <div key={group.label} style={{ display: 'flex', alignItems: 'center', gap: 2 }}>
                <span style={{
                  fontSize: 11, color: group.color, fontWeight: 600,
                  padding: '0 8px', letterSpacing: '0.5px',
                  display: window.innerWidth < 600 ? 'none' : 'block',
                }}>{group.label}</span>
                {group.links.map(link => (
                  <Link
                    key={link.path}
                    to={link.path}
                    style={{
                      padding: '6px 12px', borderRadius: 8, fontSize: 13,
                      fontWeight: 500, transition: 'all 0.2s',
                      background: location.pathname === link.path
                        ? 'rgba(255,255,255,0.1)' : 'transparent',
                      color: location.pathname === link.path ? '#fff' : '#888',
                    }}
                  >{link.label}</Link>
                ))}
                <div style={{ width: 1, height: 16, background: 'rgba(255,255,255,0.08)', margin: '0 4px' }} />
              </div>
            ))}
          </nav>
        </div>
      </header>

      {/* Page content */}
      <main style={{ flex: 1, position: 'relative', zIndex: 1 }}>
        {children}
      </main>

      {/* Footer */}
      <footer style={{
        position: 'relative', zIndex: 1,
        borderTop: '1px solid rgba(255,255,255,0.06)',
        padding: '40px 24px',
        background: 'rgba(0,0,0,0.3)',
      }}>
        <div style={{ maxWidth: 1100, margin: '0 auto' }}>
          <div style={{ display: 'flex', flexWrap: 'wrap', gap: 40, marginBottom: 32 }}>
            <div>
              <div style={{ fontFamily: 'var(--font-display)', fontWeight: 700, marginBottom: 16 }}>SaveIt</div>
              <p style={{ color: '#555', fontSize: 13, lineHeight: 1.7, maxWidth: 260 }}>
                Free online tool to download Instagram and YouTube videos in original quality. No signup, no watermark.
              </p>
            </div>
            {NAV_GROUPS.map(group => (
              <div key={group.label}>
                <div style={{ fontSize: 12, color: group.color, fontWeight: 600, marginBottom: 12, letterSpacing: '0.5px' }}>
                  {group.label}
                </div>
                <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
                  {group.links.map(link => (
                    <Link key={link.path} to={link.path} style={{ color: '#666', fontSize: 13, transition: 'color 0.2s' }}>
                      {link.label} Downloader
                    </Link>
                  ))}
                </div>
              </div>
            ))}
          </div>
          <div style={{
            display: 'flex', flexWrap: 'wrap', gap: 16,
            justifyContent: 'space-between', alignItems: 'center',
            paddingTop: 24, borderTop: '1px solid rgba(255,255,255,0.05)',
            color: '#444', fontSize: 12,
          }}>
            <span>© {new Date().getFullYear()} SaveIt. Not affiliated with Instagram™ or YouTube™.</span>
            <span>For personal use only. We do not store any files.</span>
          </div>
        </div>
      </footer>
    </div>
  )
}
