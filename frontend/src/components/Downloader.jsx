import { useState, useRef } from 'react'

const API_BASE = import.meta.env.VITE_API_BASE || 'http://localhost:8000'

function detectPlatform(url) {
  if (/instagram\.com|instagr\.am/.test(url)) return 'instagram'
  if (/tiktok\.com|vm\.tiktok\.com|vt\.tiktok\.com/.test(url)) return 'tiktok'
  if (/youtube\.com|youtu\.be/.test(url)) return 'youtube'
  return null
}

function formatDuration(s) {
  if (!s) return null
  const h = Math.floor(s / 3600), m = Math.floor((s % 3600) / 60), sec = s % 60
  return h > 0 ? `${h}:${String(m).padStart(2,'0')}:${String(sec).padStart(2,'0')}` : `${m}:${String(sec).padStart(2,'0')}`
}

function formatViews(n) {
  if (!n) return null
  if (n >= 1e9) return `${(n/1e9).toFixed(1)}B views`
  if (n >= 1e6) return `${(n/1e6).toFixed(1)}M views`
  if (n >= 1e3) return `${(n/1e3).toFixed(1)}K views`
  return `${n} views`
}

const PLATFORM_COLORS = {
  instagram: 'linear-gradient(135deg, #E1306C, #833AB4)',
  tiktok: 'linear-gradient(135deg, #25F4EE, #FE2C55)',
  youtube: 'linear-gradient(135deg, #FF0000, #cc0000)',
}
const PLATFORM_LABELS = {
  instagram: '📸 Instagram',
  tiktok: '🎵 TikTok',
  youtube: '▶ YouTube',
}

export default function Downloader() {
  const [url, setUrl] = useState('')
  const [loading, setLoading] = useState(false)
  const [info, setInfo] = useState(null)
  const [error, setError] = useState('')
  const [selectedFormat, setSelectedFormat] = useState(null)
  const [downloading, setDownloading] = useState(false)
  const inputRef = useRef(null)

  const platform = url ? detectPlatform(url) : null

  const handleFetch = async () => {
    if (!url.trim()) return
    const p = detectPlatform(url.trim())
    if (!p) { setError('Please paste a valid Instagram, TikTok or YouTube URL.'); return }
    setLoading(true); setError(''); setInfo(null); setSelectedFormat(null)
    try {
      const res = await fetch(`${API_BASE}/api/info`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ url: url.trim() }),
      })
      const data = await res.json()
      if (!res.ok) throw new Error(data.detail || 'Failed to fetch')
      setInfo(data)
      setSelectedFormat(data.formats[0]?.format_id)
    } catch (e) {
      setError(e.message)
    } finally {
      setLoading(false)
    }
  }

  const handleDownload = async () => {
    const fmt = info?.formats.find(f => f.format_id === selectedFormat)
    if (!fmt?.url) return

    setDownloading(true)

    try {
      // Build full URL
      const isProxy = fmt.download_via === 'proxy' || fmt.url.startsWith('/api/')
      const href = isProxy ? `${API_BASE}${fmt.url}` : fmt.url
      const filename = `xendrop-${info.platform}-${Date.now()}.${fmt.ext}`

      // Use fetch + blob for reliable mobile download
      if (isProxy) {
        const response = await fetch(href)
        if (!response.ok) throw new Error('Download failed')
        const blob = await response.blob()
        const blobUrl = URL.createObjectURL(blob)
        const a = document.createElement('a')
        a.href = blobUrl
        a.download = filename
        document.body.appendChild(a)
        a.click()
        document.body.removeChild(a)
        setTimeout(() => URL.revokeObjectURL(blobUrl), 5000)
      } else {
        // Direct CDN link — open in new tab
        const a = document.createElement('a')
        a.href = href
        a.download = filename
        a.target = '_blank'
        a.rel = 'noopener noreferrer'
        document.body.appendChild(a)
        a.click()
        document.body.removeChild(a)
      }
    } catch (e) {
      setError(`Download failed: ${e.message}`)
    } finally {
      setDownloading(false)
    }
  }

  const handleClear = () => {
    setUrl(''); setInfo(null); setError(''); setSelectedFormat(null)
    inputRef.current?.focus()
  }

  return (
    <div>
      {/* Input */}
      <div style={{
        background: 'rgba(255,255,255,0.05)',
        border: '1px solid rgba(255,255,255,0.1)',
        borderRadius: 16, overflow: 'hidden',
        display: 'flex', alignItems: 'center',
        marginBottom: 12,
        boxShadow: '0 8px 32px rgba(0,0,0,0.4)',
      }}>
        {platform && (
          <div style={{
            background: PLATFORM_COLORS[platform],
            padding: '0 14px', height: 58,
            display: 'flex', alignItems: 'center',
            fontSize: 12, fontWeight: 600, color: '#fff',
            whiteSpace: 'nowrap', flexShrink: 0,
          }}>{PLATFORM_LABELS[platform]}</div>
        )}
        <input
          ref={inputRef}
          type="url"
          value={url}
          onChange={e => { setUrl(e.target.value); setInfo(null); setError('') }}
          onKeyDown={e => e.key === 'Enter' && handleFetch()}
          placeholder="Paste Instagram, TikTok or YouTube link here..."
          style={{
            flex: 1, background: 'transparent', border: 'none', outline: 'none',
            color: '#f0f0f0', fontSize: 15, padding: '0 18px', height: 58, minWidth: 0,
          }}
        />
        {url && (
          <button onClick={handleClear} style={{
            background: 'transparent', border: 'none', color: '#555',
            cursor: 'pointer', padding: '0 14px', fontSize: 18, height: 58,
          }}>×</button>
        )}
      </div>

      {/* Buttons */}
      <div style={{ display: 'flex', gap: 8 }}>
        <button
          onClick={handleFetch}
          disabled={loading || !url.trim()}
          style={{
            flex: 1, padding: '15px',
            background: platform ? PLATFORM_COLORS[platform] : 'linear-gradient(135deg, #E1306C, #833AB4)',
            border: 'none', borderRadius: 12, color: '#fff',
            fontFamily: 'Unbounded, sans-serif', fontWeight: 700,
            fontSize: 15, cursor: loading || !url.trim() ? 'not-allowed' : 'pointer',
            opacity: loading || !url.trim() ? 0.6 : 1, transition: 'all 0.2s',
          }}
        >
          {loading
            ? <span style={{ display: 'inline-block', animation: 'spin 0.7s linear infinite' }}>⟳</span>
            : 'Download'}
        </button>
        {url && (
          <button onClick={handleClear} style={{
            padding: '15px 20px', background: 'rgba(255,255,255,0.06)',
            border: '1px solid rgba(255,255,255,0.1)', borderRadius: 12,
            color: '#888', cursor: 'pointer', fontSize: 14,
          }}>Clear</button>
        )}
      </div>

      {/* Error */}
      {error && (
        <div style={{
          marginTop: 14, background: 'rgba(255,60,60,0.08)',
          border: '1px solid rgba(255,60,60,0.2)', borderRadius: 12,
          padding: '14px 18px', color: '#ff8080', fontSize: 14, textAlign: 'left',
        }}>⚠ {error}</div>
      )}

      {/* Result */}
      {info && (
        <div style={{
          marginTop: 20, background: 'rgba(255,255,255,0.04)',
          border: '1px solid rgba(255,255,255,0.08)',
          borderRadius: 20, overflow: 'hidden', textAlign: 'left',
          animation: 'fadeUp 0.4s ease both',
        }}>
          {/* Thumbnail */}
          {info.thumbnail && (
            <div style={{ position: 'relative', aspectRatio: '16/9', background: '#111', overflow: 'hidden' }}>
              <img
                src={info.thumbnail.startsWith('/api/') ? `${API_BASE}${info.thumbnail}` : info.thumbnail}
                alt="thumbnail"
                style={{ width: '100%', height: '100%', objectFit: 'cover' }}
                onError={e => e.target.style.display = 'none'}
              />
              {info.duration && (
                <span style={{
                  position: 'absolute', bottom: 10, right: 10,
                  background: 'rgba(0,0,0,0.85)', color: '#fff',
                  fontSize: 12, padding: '3px 8px', borderRadius: 6, fontFamily: 'monospace',
                }}>{formatDuration(info.duration)}</span>
              )}
              <div style={{
                position: 'absolute', top: 10, left: 10,
                background: PLATFORM_COLORS[info.platform],
                color: '#fff', fontSize: 11, fontWeight: 700,
                padding: '4px 10px', borderRadius: 20,
              }}>{PLATFORM_LABELS[info.platform]}</div>
            </div>
          )}

          <div style={{ padding: 20 }}>
            <h3 style={{ fontSize: 15, fontWeight: 600, marginBottom: 10, lineHeight: 1.5, color: '#eee' }}>
              {info.title}
            </h3>
            <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap', marginBottom: 20 }}>
              {info.uploader && (
                <span style={{ fontSize: 13, color: '#777', background: 'rgba(255,255,255,0.05)', padding: '4px 12px', borderRadius: 20, border: '1px solid rgba(255,255,255,0.07)' }}>
                  👤 {info.uploader}
                </span>
              )}
              {info.view_count && (
                <span style={{ fontSize: 13, color: '#777', background: 'rgba(255,255,255,0.05)', padding: '4px 12px', borderRadius: 20, border: '1px solid rgba(255,255,255,0.07)' }}>
                  👁 {formatViews(info.view_count)}
                </span>
              )}
            </div>

            {/* Format selector — only show if more than 1 format */}
            {info.formats.length > 1 && (
              <div style={{ marginBottom: 16 }}>
                <div style={{ fontSize: 11, color: '#555', fontWeight: 600, letterSpacing: '1px', textTransform: 'uppercase', marginBottom: 10 }}>
                  Select Quality
                </div>
                <div style={{ display: 'flex', flexWrap: 'wrap', gap: 8 }}>
                  {info.formats.map(fmt => (
                    <button
                      key={fmt.format_id}
                      onClick={() => setSelectedFormat(fmt.format_id)}
                      style={{
                        padding: '8px 16px', borderRadius: 10, cursor: 'pointer',
                        border: selectedFormat === fmt.format_id
                          ? '1px solid rgba(225,48,108,0.6)' : '1px solid rgba(255,255,255,0.08)',
                        background: selectedFormat === fmt.format_id
                          ? 'rgba(225,48,108,0.12)' : 'rgba(255,255,255,0.04)',
                        color: '#f0f0f0', fontSize: 13, fontWeight: 600, transition: 'all 0.15s',
                      }}
                    >
                      {fmt.label}
                    </button>
                  ))}
                </div>
              </div>
            )}

            {/* YouTube note */}
            {info.platform === 'youtube' && (
              <div style={{
                marginBottom: 14, padding: '10px 14px',
                background: 'rgba(255,200,0,0.06)',
                border: '1px solid rgba(255,200,0,0.15)',
                borderRadius: 10, fontSize: 13, color: '#aaa', lineHeight: 1.5,
              }}>
                💡 YouTube videos download without audio due to platform restrictions.
                Select <strong>Audio Only</strong> for music/podcast content.
              </div>
            )}

            {/* Download button */}
            <button
              onClick={handleDownload}
              disabled={downloading || !selectedFormat}
              style={{
                width: '100%', padding: '16px',
                background: downloading ? 'rgba(255,255,255,0.1)' : (PLATFORM_COLORS[info.platform] || 'linear-gradient(135deg, #E1306C, #833AB4)'),
                border: 'none', borderRadius: 14, color: '#fff',
                fontFamily: 'Unbounded, sans-serif', fontWeight: 700,
                fontSize: 16, cursor: downloading ? 'not-allowed' : 'pointer',
                transition: 'all 0.2s',
              }}
            >
              {downloading
                ? <span style={{ display: 'inline-block', animation: 'spin 0.7s linear infinite' }}>⟳</span>
                : '⬇ Download Now'}
            </button>

            <p style={{ textAlign: 'center', color: '#444', fontSize: 12, marginTop: 10 }}>
              Files are not stored on our servers.
            </p>
          </div>
        </div>
      )}
    </div>
  )
}
