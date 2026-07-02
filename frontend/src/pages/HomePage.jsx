import { useState, useRef } from 'react'
import { Link } from 'react-router-dom'
import Downloader from '../components/Downloader.jsx'
import { TOOLS } from '../App.jsx'

const FAQS = [
  { q: 'How do I download an Instagram Reel?', a: 'Copy the Reel link from Instagram, paste it into the box above, and click Download. Choose your quality and save.' },
  { q: 'Does it work for YouTube videos?', a: 'Yes! Paste any YouTube link and it auto-detects. You can download in multiple quality options.' },
  { q: 'Is it completely free?', a: 'Yes, 100% free. No signup, no limits, no hidden charges.' },
  { q: 'Will the video have a watermark?', a: 'No watermarks. You get the original file exactly as uploaded.' },
  { q: 'Does it work on mobile?', a: 'Yes, works on all devices — Android, iPhone, tablet, and desktop.' },
  { q: 'Do you store my videos?', a: 'No. We never store files on our servers. Downloads go directly from the source to your device.' },
]

export default function HomePage() {
  const [openFaq, setOpenFaq] = useState(null)

  return (
    <div>
      {/* Hero */}
      <div style={{
        background: 'linear-gradient(180deg, rgba(225,48,108,0.08) 0%, transparent 60%)',
        borderBottom: '1px solid rgba(255,255,255,0.04)',
        padding: '60px 20px 48px',
        textAlign: 'center',
      }}>
        <div style={{ maxWidth: 680, margin: '0 auto' }}>
          <h1 style={{
            fontFamily: 'Unbounded', fontWeight: 900,
            fontSize: 'clamp(26px, 5vw, 44px)',
            letterSpacing: '-1.5px', lineHeight: 1.15,
            marginBottom: 16,
            background: 'linear-gradient(135deg, #fff 50%, #888)',
            WebkitBackgroundClip: 'text', WebkitTextFillColor: 'transparent',
          }}>
            Instagram, TikTok & YouTube<br />Downloader
          </h1>
          <p style={{ color: '#666', fontSize: 16, marginBottom: 40, lineHeight: 1.6 }}>
            Paste any Instagram, TikTok or YouTube link — we auto-detect the platform.<br />
            Download in HD quality, free, no watermark, no signup.
          </p>

          <Downloader />
        </div>
      </div>

      {/* Tool cards */}
      <div style={{ maxWidth: 900, margin: '0 auto', padding: '48px 20px' }}>
        <h2 style={{ fontFamily: 'Unbounded', fontSize: 18, fontWeight: 700, marginBottom: 24, letterSpacing: '-0.5px' }}>
          All Downloaders
        </h2>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(160px, 1fr))', gap: 12, marginBottom: 56 }}>
          {TOOLS.map(t => (
            <Link key={t.path} to={t.path} style={{
              background: 'rgba(255,255,255,0.03)',
              border: '1px solid rgba(255,255,255,0.07)',
              borderRadius: 16, padding: '20px 16px',
              display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 10,
              transition: 'all 0.2s', cursor: 'pointer',
              textAlign: 'center',
            }}>
              <span style={{ fontSize: 28 }}>{t.icon}</span>
              <div style={{ fontWeight: 600, fontSize: 14 }}>{t.label}</div>
              <div style={{ color: '#555', fontSize: 12, lineHeight: 1.5 }}>{t.desc}</div>
            </Link>
          ))}
        </div>

        {/* Why section */}
        <h2 style={{ fontFamily: 'Unbounded', fontSize: 18, fontWeight: 700, marginBottom: 24, letterSpacing: '-0.5px' }}>
          Why Xendrop?
        </h2>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))', gap: 12, marginBottom: 56 }}>
          {[
            { icon: '⚡', title: 'Instant', text: 'Downloads start in seconds, no waiting.' },
            { icon: '🆓', title: 'Always Free', text: 'No plans, no subscriptions, ever.' },
            { icon: '🚫', title: 'No Watermark', text: 'Pure original file, nothing added.' },
            { icon: '🔒', title: 'Private', text: 'We never store your files or data.' },
            { icon: '📱', title: 'All Devices', text: 'Works on Android, iPhone, and desktop.' },
            { icon: '🌍', title: 'Any Link', text: 'Instagram, TikTok and YouTube in one place.' },
          ].map(f => (
            <div key={f.title} style={{
              background: 'rgba(255,255,255,0.02)',
              border: '1px solid rgba(255,255,255,0.05)',
              borderRadius: 14, padding: '20px 16px',
            }}>
              <div style={{ fontSize: 26, marginBottom: 10 }}>{f.icon}</div>
              <div style={{ fontWeight: 600, fontSize: 14, marginBottom: 6 }}>{f.title}</div>
              <div style={{ color: '#555', fontSize: 13, lineHeight: 1.6 }}>{f.text}</div>
            </div>
          ))}
        </div>

        {/* FAQ */}
        <h2 style={{ fontFamily: 'Unbounded', fontSize: 18, fontWeight: 700, marginBottom: 24, letterSpacing: '-0.5px' }}>
          Frequently Asked Questions
        </h2>
        <div style={{
          background: 'rgba(255,255,255,0.02)',
          border: '1px solid rgba(255,255,255,0.06)',
          borderRadius: 20, overflow: 'hidden',
        }}>
          {FAQS.map((faq, i) => (
            <div key={i} style={{ borderBottom: i < FAQS.length - 1 ? '1px solid rgba(255,255,255,0.05)' : 'none' }}>
              <button onClick={() => setOpenFaq(openFaq === i ? null : i)} style={{
                width: '100%', background: 'transparent', border: 'none',
                color: '#ddd', textAlign: 'left', padding: '18px 24px',
                cursor: 'pointer', display: 'flex', justifyContent: 'space-between',
                alignItems: 'center', gap: 12, fontSize: 15, fontWeight: 500,
                fontFamily: 'DM Sans, sans-serif',
              }}>
                <span>{faq.q}</span>
                <span style={{ color: '#555', fontSize: 20, transition: 'transform 0.2s', transform: openFaq === i ? 'rotate(45deg)' : 'none', flexShrink: 0 }}>+</span>
              </button>
              {openFaq === i && (
                <p style={{ color: '#666', fontSize: 14, lineHeight: 1.8, padding: '0 24px 18px', paddingRight: 48 }}>
                  {faq.a}
                </p>
              )}
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}
