import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import Layout from './components/layout/Layout'
import Dashboard from './pages/Dashboard'
import Podcasts from './pages/Podcasts'
import Episodes from './pages/Episodes'
import Sync from './pages/Sync'
import Storage from './pages/Storage'
import Settings from './pages/Settings'

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Layout />}>
          <Route index element={<Navigate to="/dashboard" replace />} />
          <Route path="dashboard" element={<Dashboard />} />
          <Route path="podcasts" element={<Podcasts />} />
          <Route path="episodes" element={<Episodes />} />
          <Route path="sync" element={<Sync />} />
          <Route path="storage" element={<Storage />} />
          <Route path="settings" element={<Settings />} />
        </Route>
      </Routes>
    </BrowserRouter>
  )
}

export default App
