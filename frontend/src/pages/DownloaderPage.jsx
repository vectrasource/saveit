import { useState, useRef, useEffect } from 'react'

const API_BASE = import.meta.env.VITE_API_BASE || 'http://localhost:8000'

function formatDuration(s) {
  if (!s) return null
  const h = Math.floor(s / 3600), m = Math.floor((s % 3600) / 60), sec = s % 60
  return h > 0
    ? `${h}:${String(m).padStart(2, '0')}:${String(sec).padStart(2, '0')}`
    : `${m}:${String(sec).padStart(2, '0')}`
}

function formatViews(n) {
  if (!n) return null
  if (n >= 1e9) return `${(n / 1e9).toFixed(1)}B views`
  if (n >= 1e6) return `${(n / 1e6).toFixed(1)}M views`
  if (n >= 1e3) return `${(n / 1e3).toFixed(1)}K views`
  return `${n} views`
}

function Spinner() {
  return <span style={{ display: 'inline-block', animation: 'spin 0.7s linear infinite' }}>⟳</span>
}

function FormatBadge({ type }) {
  const colors = { video: '#3b82f6', audio: '#10b981', photo: '#f59e0b' }
  return (
    <span style={{
      fontSize: 10, fontWeight: 600, padding: '2px 6px', borderRadius: 4,
      background: colors[type] || '#555', color: '#fff', letterSpacing: '0.5px',
      textTransform: 'uppercase',
    }}>{type}</span>
  )
}

export default function DownloaderPage({ tool }) {
  const [url, setUrl] = useState('')
  const [loading, setLoading] = useState(false)
  const [info, setInfo] = useState(null)
  const [error, setError] = useState('')
  const [selectedFormat, setSelectedFormat] = useState(null)
  const [openFaq, setOpenFaq] = useState(null)
  const inputRef = useRef(null)

  // Reset state when tool changes (navigating between pages)
  useEffect(() => {
    setUrl(''); setInfo(null); setError(''); setSelectedFormat(null)
    inputRef.current?.focus()
  }, [tool.path])

  // Update page title and meta description per tool
  useEffect(() => {
    document.title = `${tool.title} — SaveIt`
    const meta = document.querySelector('meta[name="description"]')
    if (meta) meta.setAttribute('content', tool.description)
  }, [tool])

  const handleFetch = async () => {
    if (!url.trim()) return
    setLoading(true); setError(''); setInfo(null); setSelectedFormat(null)
    try {
      const res = await fetch(`${API_BASE}/api/info`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ url: url.trim() }),
      })
      const data = await res.json()
      if (!res.ok) throw new Error(data.detail || 'Failed to fetch video info')
      setInfo(data)
      // Auto-select first format, or audio-only for audio pages
      if (tool.type === 'audio') {
        const audioFmt = data.formats.find(f => f.type === 'audio')
        setSelectedFormat(audioFmt?.format_id || data.formats[0]?.format_id)
      } else {
        setSelectedFormat(data.formats[0]?.format_id)
      }
    } catch (e) {
      setError(e.message)
    } finally {
      setLoading(false)
    }
  }

  const handleDownload = () => {
    const fmt = info?.formats.find(f => f.format_id === selectedFormat)
    if (!fmt?.url) return
    // Trigger browser to download the CDN URL directly
    const a = document.createElement('a')
    a.href = fmt.url
    a.download = `saveit-${Date.now()}.${fmt.ext}`
    a.target = '_blank'
    a.rel = 'noopener noreferrer'
    a.click()
  }

  return (
    <div style={{ maxWidth: 760, margin: '0 auto', padding: '48px 20px 80px' }}>

      {/* Hero */}
      <div style={{ textAlign: 'center', marginBottom: 40 }} className="fade-up">
        <div style={{ fontSize: 48, marginBottom: 12 }}>{tool.icon}</div>
        <h1 style={{
          fontFamily: 'var(--font-display)', fontWeight: 700,
          fontSize: 'clamp(22px, 5vw, 36px)', letterSpacing: '-1px',
          lineHeight: 1.2, marginBottom: 12,
        }}>{tool.title}</h1>
        <p style={{ color: '#888', fontSize: 16, maxWidth: 500, margin: '0 auto', lineHeight: 1.6 }}>
          {tool.description}
        </p>
      </div>

      {/* Input card */}
      <div className="fade-up fade-up-1" style={{
        background: 'rgba(255,255,255,0.04)',
        border: '1px solid rgba(255,255,255,0.08)',
        borderRadius: 20, padding: 24, marginBottom: 20,
        backdropFilter: 'blur(12px)',
      }}>
        <div style={{
          display: 'flex', alignItems: 'center',
          background: 'rgba(0,0,0,0.5)',
          border: '1px solid rgba(255,255,255,0.1)',
          borderRadius: 12, overflow: 'hidden', marginBottom: 14,
        }}>
          <input
            ref={inputRef}
            type="url"
            value={url}
            onChange={e => { setUrl(e.target.value); setInfo(null); setError('') }}
            onKeyDown={e => e.key === 'Enter' && handleFetch()}
            placeholder={tool.placeholder}
            style={{
              flex: 1, background: 'transparent', border: 'none', outline: 'none',
              color: '#f0f0f0', fontSize: 15, padding: '16px 18px',
              fontFamily: 'var(--font-body)',
            }}
          />
          {url && (
            <button
              onClick={() => { setUrl(''); setInfo(null); setError('') }}
              style={{
                background: 'transparent', border: 'none', color: '#555',
                cursor: 'pointer', padding: '16px 14px', fontSize: 16,
              }}
            >✕</button>
          )}
        </div>

        <button
          onClick={handleFetch}
          disabled={loading || !url.trim()}
          style={{
            width: '100%', padding: '15px',
            background: loading || !url.trim() ? 'rgba(255,255,255,0.08)' : tool.color,
            border: 'none', borderRadius: 12, color: '#fff',
            fontFamily: 'var(--font-display)', fontWeight: 600,
            fontSize: 15, cursor: loading || !url.trim() ? 'not-allowed' : 'pointer',
            transition: 'all 0.2s', letterSpacing: '0.3px',
          }}
        >
          {loading ? <><Spinner /> &nbsp;Fetching...</> : 'Fetch Video →'}
        </button>
      </div>

      {/* Error */}
      {error && (
        <div className="fade-up" style={{
          background: 'rgba(255,60,60,0.08)', border: '1px solid rgba(255,60,60,0.2)',
          borderRadius: 12, padding: '14px 18px', color: '#ff8080',
          fontSize: 14, marginBottom: 20,
        }}>
          ⚠ {error}
        </div>
      )}

      {/* Result card */}
      {info && (
        <div className="fade-up" style={{
          background: 'rgba(255,255,255,0.04)',
          border: '1px solid rgba(255,255,255,0.08)',
          borderRadius: 20, overflow: 'hidden',
          backdropFilter: 'blur(12px)', marginBottom: 20,
        }}>
          {/* Thumbnail */}
          {info.thumbnail && (
            <div style={{ position: 'relative', aspectRatio: '16/9', background: '#111', overflow: 'hidden' }}>
              <img src={info.thumbnail} alt="thumbnail" style={{ width: '100%', height: '100%', objectFit: 'cover' }} />
              {info.duration && (
                <span style={{
                  position: 'absolute', bottom: 10, right: 10,
                  background: 'rgba(0,0,0,0.85)', color: '#fff',
                  fontSize: 12, padding: '3px 8px', borderRadius: 6,
                  fontFamily: 'monospace',
                }}>{formatDuration(info.duration)}</span>
              )}
            </div>
          )}

          <div style={{ padding: 24 }}>
            <h2 style={{ fontSize: 16, fontWeight: 600, marginBottom: 10, lineHeight: 1.4, color: '#eee' }}>
              {info.title}
            </h2>

            <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap', marginBottom: 24 }}>
              {info.uploader && (
                <span style={{
                  fontSize: 13, color: '#888', background: 'rgba(255,255,255,0.06)',
                  padding: '4px 12px', borderRadius: 20, border: '1px solid rgba(255,255,255,0.08)',
                }}>👤 {info.uploader}</span>
              )}
              {info.view_count && (
                <span style={{
                  fontSize: 13, color: '#888', background: 'rgba(255,255,255,0.06)',
                  padding: '4px 12px', borderRadius: 20, border: '1px solid rgba(255,255,255,0.08)',
                }}>👁 {formatViews(info.view_count)}</span>
              )}
            </div>

            {/* Format selector */}
            {info.formats.length > 0 && (
              <div style={{ marginBottom: 20 }}>
                <div style={{
                  fontSize: 11, color: '#555', fontWeight: 600,
                  letterSpacing: '1px', textTransform: 'uppercase', marginBottom: 10,
                }}>Select Format</div>
                <div style={{ display: 'flex', flexWrap: 'wrap', gap: 8 }}>
                  {info.formats.map(fmt => (
                    <button
                      key={fmt.format_id}
                      onClick={() => setSelectedFormat(fmt.format_id)}
                      style={{
                        padding: '10px 16px', borderRadius: 10, cursor: 'pointer',
                        border: selectedFormat === fmt.format_id
                          ? '1px solid rgba(225,48,108,0.6)' : '1px solid rgba(255,255,255,0.08)',
                        background: selectedFormat === fmt.format_id
                          ? 'rgba(225,48,108,0.12)' : 'rgba(255,255,255,0.04)',
                        display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 4,
                        transition: 'all 0.15s', minWidth: 80,
                      }}
                    >
                      <span style={{ color: '#f0f0f0', fontSize: 14, fontWeight: 600 }}>{fmt.label}</span>
                      <div style={{ display: 'flex', gap: 4, alignItems: 'center' }}>
                        <FormatBadge type={fmt.type} />
                        {fmt.filesize && <span style={{ fontSize: 10, color: '#555' }}>{fmt.filesize}</span>}
                      </div>
                    </button>
                  ))}
                </div>
              </div>
            )}

            <button
              onClick={handleDownload}
              disabled={!selectedFormat}
              style={{
                width: '100%', padding: '16px',
                background: selectedFormat ? tool.color : 'rgba(255,255,255,0.06)',
                border: 'none', borderRadius: 14, color: '#fff',
                fontFamily: 'var(--font-display)', fontWeight: 600,
                fontSize: 16, cursor: selectedFormat ? 'pointer' : 'not-allowed',
                transition: 'all 0.2s', letterSpacing: '0.3px',
              }}
            >
              ⬇ Download Now
            </button>

            <p style={{ textAlign: 'center', color: '#444', fontSize: 12, marginTop: 10 }}>
              File downloads directly from the source server. We store nothing.
            </p>
          </div>
        </div>
      )}

      {/* How it works */}
      <div className="fade-up fade-up-2" style={{
        background: 'rgba(255,255,255,0.02)',
        border: '1px solid rgba(255,255,255,0.06)',
        borderRadius: 20, padding: 32, marginBottom: 20,
      }}>
        <h2 style={{
          fontFamily: 'var(--font-display)', fontSize: 18, fontWeight: 600,
          marginBottom: 24, letterSpacing: '-0.3px',
        }}>How to {tool.title}</h2>
        <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
          {[
            { n: '01', title: 'Copy the link', text: `Open Instagram or YouTube, find your video, tap Share and copy the link.` },
            { n: '02', title: 'Paste it above', text: 'Paste the copied link into the input box at the top of this page.' },
            { n: '03', title: 'Download', text: 'Click Fetch, choose your preferred quality, then hit Download Now.' },
          ].map(step => (
            <div key={step.n} style={{ display: 'flex', gap: 16, alignItems: 'flex-start' }}>
              <div style={{
                fontFamily: 'var(--font-display)', fontSize: 11, fontWeight: 700,
                color: '#333', minWidth: 28, paddingTop: 2,
              }}>{step.n}</div>
              <div>
                <div style={{ fontWeight: 600, marginBottom: 4, color: '#ddd' }}>{step.title}</div>
                <div style={{ color: '#666', fontSize: 14, lineHeight: 1.6 }}>{step.text}</div>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Features */}
      <div className="fade-up fade-up-3" style={{
        display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))',
        gap: 12, marginBottom: 20,
      }}>
        {[
          { icon: '⚡', title: 'Fast', text: 'Download starts in seconds' },
          { icon: '🆓', title: 'Free', text: 'No signup, no cost ever' },
          { icon: '🚫', title: 'No watermark', text: 'Original file, clean' },
          { icon: '📱', title: 'Works everywhere', text: 'Mobile, tablet, desktop' },
        ].map(f => (
          <div key={f.title} style={{
            background: 'rgba(255,255,255,0.03)',
            border: '1px solid rgba(255,255,255,0.06)',
            borderRadius: 14, padding: '18px 16px',
          }}>
            <div style={{ fontSize: 24, marginBottom: 8 }}>{f.icon}</div>
            <div style={{ fontWeight: 600, fontSize: 14, marginBottom: 4 }}>{f.title}</div>
            <div style={{ color: '#555', fontSize: 13 }}>{f.text}</div>
          </div>
        ))}
      </div>

      {/* FAQ */}
      {tool.faqs && tool.faqs.length > 0 && (
        <div className="fade-up fade-up-4" style={{
          background: 'rgba(255,255,255,0.02)',
          border: '1px solid rgba(255,255,255,0.06)',
          borderRadius: 20, padding: 32,
        }}>
          <h2 style={{
            fontFamily: 'var(--font-display)', fontSize: 18, fontWeight: 600,
            marginBottom: 24, letterSpacing: '-0.3px',
          }}>Frequently Asked Questions</h2>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
            {tool.faqs.map((faq, i) => (
              <div
                key={i}
                style={{
                  borderBottom: i < tool.faqs.length - 1 ? '1px solid rgba(255,255,255,0.05)' : 'none',
                }}
              >
                <button
                  onClick={() => setOpenFaq(openFaq === i ? null : i)}
                  style={{
                    width: '100%', background: 'transparent', border: 'none',
                    color: '#ddd', textAlign: 'left', padding: '16px 0',
                    cursor: 'pointer', display: 'flex', justifyContent: 'space-between',
                    alignItems: 'center', gap: 12, fontSize: 15, fontWeight: 500,
                    fontFamily: 'var(--font-body)',
                  }}
                >
                  <span>{faq.q}</span>
                  <span style={{
                    color: '#555', fontSize: 18, transition: 'transform 0.2s',
                    transform: openFaq === i ? 'rotate(45deg)' : 'none', flexShrink: 0,
                  }}>+</span>
                </button>
                {openFaq === i && (
                  <p style={{ color: '#777', fontSize: 14, lineHeight: 1.7, paddingBottom: 16, paddingRight: 24 }}>
                    {faq.a}
                  </p>
                )}
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}
