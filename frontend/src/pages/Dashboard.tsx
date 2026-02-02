import { usePodcasts } from '../hooks/usePodcasts'
import { useEpisodes } from '../hooks/useEpisodes'
import { useSyncStatus, useDetectWatch } from '../hooks/useSync'
import { useLocalStorage } from '../hooks/useStorage'
import { Link } from 'react-router-dom'
import './Dashboard.css'

export default function Dashboard() {
  const { data: podcastsData } = usePodcasts()
  const { data: episodesData } = useEpisodes()
  const { data: syncStatus } = useSyncStatus()
  const { data: watchDetect } = useDetectWatch()
  const { data: localStorage } = useLocalStorage()

  // Extract data
  const podcasts = podcastsData?.podcasts || []
  const episodes = episodesData?.episodes || []

  // Calculate stats
  const totalPodcasts = podcasts.length
  const totalEpisodes = episodes.length
  const downloadedEpisodes = episodes.filter((e) => e.download_status === 'downloaded').length
  const pendingDownloads = episodes.filter((e) => e.download_status === 'pending').length
  const syncedEpisodes = syncStatus?.synced_episodes || 0
  const watchConnected = watchDetect?.connected || false
  const storageUsedMb = localStorage?.total_podcast_mb || 0

  return (
    <div className="dashboard-page">
      <div className="page-header">
        <h2>Dashboard</h2>
        <p className="page-subtitle">Overview of your podcast sync application</p>
      </div>

      {/* Quick Stats */}
      <div className="stats-grid">
        <div className="stat-card">
          <div className="stat-icon">📻</div>
          <div className="stat-content">
            <div className="stat-value">{totalPodcasts}</div>
            <div className="stat-label">Podcasts</div>
          </div>
          <Link to="/podcasts" className="stat-link">
            Manage →
          </Link>
        </div>

        <div className="stat-card">
          <div className="stat-icon">🎧</div>
          <div className="stat-content">
            <div className="stat-value">{totalEpisodes}</div>
            <div className="stat-label">Episodes</div>
          </div>
          <Link to="/episodes" className="stat-link">
            View all →
          </Link>
        </div>

        <div className="stat-card">
          <div className="stat-icon">⬇️</div>
          <div className="stat-content">
            <div className="stat-value">{downloadedEpisodes}</div>
            <div className="stat-label">Downloaded</div>
          </div>
          <div className="stat-secondary">{pendingDownloads} pending</div>
        </div>

        <div className="stat-card">
          <div className="stat-icon">⌚</div>
          <div className="stat-content">
            <div className="stat-value">{syncedEpisodes}</div>
            <div className="stat-label">On Watch</div>
          </div>
          <Link to="/sync" className="stat-link">
            Sync →
          </Link>
        </div>

        <div className="stat-card">
          <div className="stat-icon">💾</div>
          <div className="stat-content">
            <div className="stat-value">{storageUsedMb.toFixed(1)}</div>
            <div className="stat-label">MB Used</div>
          </div>
          <Link to="/storage" className="stat-link">
            Manage →
          </Link>
        </div>

        <div className={`stat-card ${watchConnected ? 'watch-connected' : 'watch-disconnected'}`}>
          <div className="stat-icon">{watchConnected ? '✅' : '⚠️'}</div>
          <div className="stat-content">
            <div className="stat-value">{watchConnected ? 'Connected' : 'Not Connected'}</div>
            <div className="stat-label">Watch Status</div>
          </div>
          {watchConnected && (
            <Link to="/sync" className="stat-link">
              Sync now →
            </Link>
          )}
        </div>
      </div>

      {/* Quick Actions */}
      <div className="card quick-actions-card">
        <h3>Quick Actions</h3>
        <div className="quick-actions">
          <Link to="/podcasts" className="action-button">
            <span className="action-icon">➕</span>
            <span className="action-text">
              <strong>Add Podcast</strong>
              <small>Subscribe to a new podcast via RSS</small>
            </span>
          </Link>

          <Link to="/episodes" className="action-button">
            <span className="action-icon">📥</span>
            <span className="action-text">
              <strong>Download Episodes</strong>
              <small>Manage episode downloads</small>
            </span>
          </Link>

          <Link to="/sync" className="action-button">
            <span className="action-icon">🔄</span>
            <span className="action-text">
              <strong>Sync to Watch</strong>
              <small>Transfer episodes to your Coros watch</small>
            </span>
          </Link>

          <Link to="/storage" className="action-button">
            <span className="action-icon">🗂️</span>
            <span className="action-text">
              <strong>Manage Storage</strong>
              <small>Clean up old episodes</small>
            </span>
          </Link>
        </div>
      </div>

      {/* Getting Started Guide */}
      {totalPodcasts === 0 && (
        <div className="card getting-started-card">
          <h3>Getting Started</h3>
          <div className="getting-started">
            <div className="step">
              <div className="step-number">1</div>
              <div className="step-content">
                <strong>Add your first podcast</strong>
                <p>Go to the Podcasts page and add a podcast using its RSS feed URL</p>
              </div>
            </div>

            <div className="step">
              <div className="step-number">2</div>
              <div className="step-content">
                <strong>Download episodes</strong>
                <p>Episodes will auto-download, or you can manually download from the Episodes page</p>
              </div>
            </div>

            <div className="step">
              <div className="step-number">3</div>
              <div className="step-content">
                <strong>Connect your watch</strong>
                <p>Plug in your Coros watch via USB and wait for detection</p>
              </div>
            </div>

            <div className="step">
              <div className="step-number">4</div>
              <div className="step-content">
                <strong>Sync to watch</strong>
                <p>Go to the Sync page and click "Start Sync" to transfer episodes</p>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Status Messages */}
      <div className="status-messages">
        {!watchConnected && totalEpisodes > 0 && (
          <div className="status-message status-info">
            <span className="status-icon">ℹ️</span>
            <span>Connect your Coros watch via USB to sync {syncedEpisodes > 0 ? 'new' : ''} episodes</span>
          </div>
        )}

        {pendingDownloads > 0 && (
          <div className="status-message status-info">
            <span className="status-icon">⏳</span>
            <span>{pendingDownloads} episode{pendingDownloads !== 1 ? 's' : ''} pending download</span>
          </div>
        )}

        {watchConnected && downloadedEpisodes > syncedEpisodes && (
          <div className="status-message status-success">
            <span className="status-icon">✨</span>
            <span>
              Your watch is connected! You have {downloadedEpisodes - syncedEpisodes} new episode
              {downloadedEpisodes - syncedEpisodes !== 1 ? 's' : ''} ready to sync
            </span>
          </div>
        )}
      </div>
    </div>
  )
}
