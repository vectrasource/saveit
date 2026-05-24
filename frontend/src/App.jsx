import { Routes, Route } from 'react-router-dom'
import Layout from './components/Layout.jsx'
import DownloaderPage from './pages/DownloaderPage.jsx'

const TOOLS = [
  {
    path: '/',
    platform: 'instagram',
    type: 'reels',
    title: 'Instagram Reels Downloader',
    description: 'Download Instagram Reels in HD quality — free, no watermark, no signup.',
    placeholder: 'Paste Instagram Reel link here...',
    keywords: 'instagram reels downloader, download instagram reels, save reels',
    color: 'linear-gradient(135deg, #E1306C, #833AB4)',
    icon: '🎬',
    faqs: [
      { q: 'How do I download an Instagram Reel?', a: 'Copy the Reel URL from Instagram, paste it above, and click Fetch. Then choose your quality and download.' },
      { q: 'Is it free?', a: 'Yes, completely free with no limits.' },
      { q: 'Do I need an Instagram account?', a: 'No account needed. Just paste the public Reel URL.' },
      { q: 'Will there be a watermark?', a: 'No watermarks. You get the original video file.' },
      { q: 'Does it work on mobile?', a: 'Yes, works on all devices and browsers.' },
    ]
  },
  {
    path: '/instagram-video-downloader',
    platform: 'instagram',
    type: 'video',
    title: 'Instagram Video Downloader',
    description: 'Save any Instagram video to your device in original quality for free.',
    placeholder: 'Paste Instagram Video link here...',
    keywords: 'instagram video downloader, download instagram video, save instagram video',
    color: 'linear-gradient(135deg, #E1306C, #833AB4)',
    icon: '📹',
    faqs: [
      { q: 'What types of Instagram videos can I download?', a: 'Feed videos, IGTV, and any public video post.' },
      { q: 'What quality will the video be in?', a: 'We fetch the original quality — whatever Instagram has available.' },
      { q: 'Can I download videos from private accounts?', a: 'No, only public accounts are supported.' },
      { q: 'Is there a file size limit?', a: 'No, there are no size limits.' },
    ]
  },
  {
    path: '/instagram-photo-downloader',
    platform: 'instagram',
    type: 'photo',
    title: 'Instagram Photo Downloader',
    description: 'Download Instagram photos in full resolution — no app, no login required.',
    placeholder: 'Paste Instagram Photo post link here...',
    keywords: 'instagram photo downloader, download instagram photos, save instagram pictures',
    color: 'linear-gradient(135deg, #833AB4, #E1306C)',
    icon: '🖼️',
    faqs: [
      { q: 'Can I download carousel posts?', a: 'Yes, you can download individual photos from carousel posts.' },
      { q: 'What format will photos be saved in?', a: 'Original JPG format as uploaded to Instagram.' },
      { q: 'Is the quality original?', a: 'Yes, we fetch the highest resolution available.' },
    ]
  },
  {
    path: '/instagram-story-downloader',
    platform: 'instagram',
    type: 'story',
    title: 'Instagram Story Downloader',
    description: 'Save Instagram Stories before they disappear — free and fast.',
    placeholder: 'Paste Instagram Story link here...',
    keywords: 'instagram story downloader, download instagram stories, save instagram story',
    color: 'linear-gradient(135deg, #FCAF45, #E1306C)',
    icon: '⭕',
    faqs: [
      { q: 'Can I download stories from any account?', a: 'Only from public accounts without a login.' },
      { q: 'Do stories expire before I can download?', a: 'Stories last 24 hours on Instagram. Download while they are live.' },
    ]
  },
  {
    path: '/youtube-video-downloader',
    platform: 'youtube',
    type: 'video',
    title: 'YouTube Video Downloader',
    description: 'Download YouTube videos in 1080p, 720p, 480p or audio only — completely free.',
    placeholder: 'Paste YouTube video link here...',
    keywords: 'youtube video downloader, download youtube video, save youtube video mp4',
    color: 'linear-gradient(135deg, #FF0000, #cc0000)',
    icon: '▶️',
    faqs: [
      { q: 'Can I download YouTube videos in HD?', a: 'Yes, up to 1080p depending on what the video offers.' },
      { q: 'Can I download just the audio?', a: 'Yes, choose the Audio Only option to get an MP3.' },
      { q: 'Can I download YouTube Shorts?', a: 'Yes, paste the Shorts URL and it works the same way.' },
      { q: 'Is there a length limit on videos?', a: 'No length limit. Long videos and short ones both work.' },
    ]
  },
  {
    path: '/youtube-audio-downloader',
    platform: 'youtube',
    type: 'audio',
    title: 'YouTube to MP3 Converter',
    description: 'Convert any YouTube video to MP3 audio — free, fast, high quality.',
    placeholder: 'Paste YouTube video link here...',
    keywords: 'youtube to mp3, youtube mp3 converter, download youtube audio',
    color: 'linear-gradient(135deg, #FF0000, #FF6B35)',
    icon: '🎵',
    faqs: [
      { q: 'What quality is the MP3?', a: '192kbps high quality audio extracted from the original video.' },
      { q: 'Can I convert YouTube Music?', a: 'Yes, any public YouTube URL works.' },
      { q: 'How long does conversion take?', a: 'Usually just a few seconds.' },
    ]
  },
]

export default function App() {
  return (
    <Layout tools={TOOLS}>
      <Routes>
        {TOOLS.map(tool => (
          <Route
            key={tool.path}
            path={tool.path}
            element={<DownloaderPage tool={tool} />}
          />
        ))}
      </Routes>
    </Layout>
  )
}

export { TOOLS }
