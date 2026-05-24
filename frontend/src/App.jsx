import { Routes, Route } from 'react-router-dom'
import Layout from './components/Layout.jsx'
import HomePage from './pages/HomePage.jsx'
import ToolPage from './pages/ToolPage.jsx'

export const TOOLS = [
  { path: '/reels-downloader', label: 'Reels', icon: '🎬', platform: 'instagram', desc: 'Download Instagram Reels in HD — free, no watermark.' },
  { path: '/video-downloader', label: 'Video', icon: '📹', platform: 'instagram', desc: 'Download any Instagram video in original quality.' },
  { path: '/photo-downloader', label: 'Photo', icon: '🖼️', platform: 'instagram', desc: 'Save Instagram photos in full resolution.' },
  { path: '/story-downloader', label: 'Story', icon: '⭕', platform: 'instagram', desc: 'Download Instagram Stories before they disappear.' },
  { path: '/youtube-downloader', label: 'YouTube', icon: '▶️', platform: 'youtube', desc: 'Download YouTube videos in 1080p, 720p, or MP3.' },
]

export default function App() {
  return (
    <Layout>
      <Routes>
        <Route path="/" element={<HomePage />} />
        {TOOLS.map(t => (
          <Route key={t.path} path={t.path} element={<ToolPage tool={t} />} />
        ))}
      </Routes>
    </Layout>
  )
}
