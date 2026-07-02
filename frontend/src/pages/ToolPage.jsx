import Downloader from '../components/Downloader.jsx'

const FAQS = {
  instagram: [
    { q: 'How do I download an Instagram Reel?', a: 'Copy the link from Instagram, paste above, click Download.' },
    { q: 'Do I need to log in?', a: 'No account needed. Works for all public content.' },
    { q: 'Will there be a watermark?', a: 'No watermarks — original file only.' },
  ],
  tiktok: [
    { q: 'How do I download a TikTok video?', a: 'Copy the video link from TikTok, paste above, click Download.' },
    { q: 'Will the TikTok video have a watermark?', a: 'No watermarks — you get the original file exactly as uploaded.' },
    { q: 'Does it work for private TikTok accounts?', a: 'No, only videos from public accounts can be downloaded.' },
  ],
  youtube: [
    { q: 'Can I download in HD?', a: 'Yes, up to 1080p depending on the video.' },
    { q: 'Can I download audio only?', a: 'Yes, choose the Audio Only option after fetching.' },
    { q: 'Does it work for YouTube Shorts?', a: 'Yes, paste any Shorts URL and it works.' },
  ],
}

export default function ToolPage({ tool }) {
  const faqs = FAQS[tool.platform] || []

  return (
    <div>
      <div style={{
        background: 'linear-gradient(180deg, rgba(225,48,108,0.07) 0%, transparent 60%)',
        padding: '56px 20px 48px', textAlign: 'center',
        borderBottom: '1px solid rgba(255,255,255,0.04)',
      }}>
        <div style={{ maxWidth: 680, margin: '0 auto' }}>
          <div style={{ fontSize: 44, marginBottom: 12 }}>{tool.icon}</div>
          <h1 style={{
            fontFamily: 'Unbounded', fontWeight: 900,
            fontSize: 'clamp(22px, 4vw, 36px)', letterSpacing: '-1px',
            lineHeight: 1.2, marginBottom: 12,
            background: 'linear-gradient(135deg, #fff 50%, #888)',
            WebkitBackgroundClip: 'text', WebkitTextFillColor: 'transparent',
          }}>{tool.label} Downloader</h1>
          <p style={{ color: '#666', fontSize: 15, marginBottom: 36, lineHeight: 1.6 }}>{tool.desc}</p>
          <Downloader />
        </div>
      </div>

      {/* How it works + FAQ */}
      <div style={{ maxWidth: 900, margin: '0 auto', padding: '48px 20px 64px' }}>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(260px, 1fr))', gap: 16, marginBottom: 48 }}>
          {[
            { n: '01', t: 'Copy the link', d: `Open Instagram or YouTube, find the content, tap Share and copy the link.` },
            { n: '02', t: 'Paste it above', d: 'Paste the link into the input box. The platform is detected automatically.' },
            { n: '03', t: 'Download', d: 'Click Download, choose quality if needed, and save to your device.' },
          ].map(s => (
            <div key={s.n} style={{ background: 'rgba(255,255,255,0.02)', border: '1px solid rgba(255,255,255,0.06)', borderRadius: 16, padding: 24 }}>
              <div style={{ fontFamily: 'Unbounded', fontSize: 11, color: '#444', marginBottom: 10 }}>{s.n}</div>
              <div style={{ fontWeight: 600, fontSize: 15, marginBottom: 8 }}>{s.t}</div>
              <div style={{ color: '#555', fontSize: 14, lineHeight: 1.7 }}>{s.d}</div>
            </div>
          ))}
        </div>

        {faqs.length > 0 && (
          <>
            <h2 style={{ fontFamily: 'Unbounded', fontSize: 18, fontWeight: 700, marginBottom: 20, letterSpacing: '-0.5px' }}>FAQ</h2>
            <div style={{ background: 'rgba(255,255,255,0.02)', border: '1px solid rgba(255,255,255,0.06)', borderRadius: 20, overflow: 'hidden' }}>
              {faqs.map((faq, i) => (
                <div key={i} style={{ padding: '18px 24px', borderBottom: i < faqs.length - 1 ? '1px solid rgba(255,255,255,0.05)' : 'none' }}>
                  <div style={{ fontWeight: 600, fontSize: 14, marginBottom: 8, color: '#ddd' }}>{faq.q}</div>
                  <div style={{ color: '#666', fontSize: 14, lineHeight: 1.7 }}>{faq.a}</div>
                </div>
              ))}
            </div>
          </>
        )}
      </div>
    </div>
  )
}
