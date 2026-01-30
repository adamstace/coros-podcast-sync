import { useState } from 'react'
import { useLocalStorage, useStorageByPodcast, useCleanup } from '../hooks/useStorage'
import './Storage.css'

export default function Storage() {
  const [cleanupType, setCleanupType] = useState<'age' | 'storage_limit' | 'failed' | 'orphaned'>('failed')
  const [daysOld, setDaysOld] = useState(30)
  const [maxStorageMb, setMaxStorageMb] = useState(1000)
  const [keepSynced, setKeepSynced] = useState(true)

  const { data: localStorage, isLoading: localLoading } = useLocalStorage()
  const { data: podcastStorage, isLoading: podcastLoading } = useStorageByPodcast()
  const cleanupMutation = useCleanup()

  const handleCleanup = async () => {
    if (!confirm('Are you sure you want to run cleanup? This will permanently delete files.')) {
      return
    }

    try {
      const result = await cleanupMutation.mutateAsync({
        cleanup_type: cleanupType,
        days_old: daysOld,
        max_storage_mb: maxStorageMb,
        keep_synced: keepSynced,
      })
      alert(`${result.message}\nFreed ${result.mb_freed} MB`)
    } catch (error: any) {
      alert(error.response?.data?.detail || 'Cleanup failed')
    }
  }

  const formatBytes = (bytes: number) => {
    return (bytes / (1024 * 1024)).toFixed(2) + ' MB'
  }

  const formatPercent = (percent: number) => {
    return percent.toFixed(1) + '%'
  }

  return (
    <div className="storage-page">
      <div className="page-header">
        <h2>Storage Management</h2>
      </div>

      {/* Local Storage Overview */}
      <div className="card storage-overview-card">
        <h3>Local Storage</h3>
        {localLoading ? (
          <p>Loading storage info...</p>
        ) : localStorage ? (
          <div className="storage-overview">
            <div className="storage-stat-grid">
              <div className="storage-stat-item">
                <div className="stat-label">Total Podcast Data</div>
                <div className="stat-value">{localStorage.total_podcast_mb.toFixed(2)} MB</div>
                <div className="stat-breakdown">
                  <div>Episodes: {localStorage.episodes_mb.toFixed(2)} MB</div>
                  <div>Converted: {localStorage.converted_mb.toFixed(2)} MB</div>
                </div>
              </div>

              <div className="storage-stat-item">
                <div className="stat-label">Disk Usage</div>
                <div className="stat-value">{formatPercent(localStorage.disk_used_percent)}</div>
                <div className="stat-breakdown">
                  <div>Used: {formatBytes(localStorage.disk_used_bytes)}</div>
                  <div>Free: {formatBytes(localStorage.disk_free_bytes)}</div>
                  <div>Total: {formatBytes(localStorage.disk_total_bytes)}</div>
                </div>
              </div>
            </div>

            {/* Progress bar */}
            <div className="storage-progress">
              <div className="storage-progress-label">
                <span>Disk Space</span>
                <span>{formatPercent(localStorage.disk_used_percent)} used</span>
              </div>
              <div className="storage-progress-bar">
                <div
                  className="storage-progress-fill"
                  style={{ width: `${localStorage.disk_used_percent}%` }}
                ></div>
              </div>
            </div>
          </div>
        ) : (
          <p>No storage data available</p>
        )}
      </div>

      {/* Storage by Podcast */}
      <div className="card podcast-storage-card">
        <h3>Storage by Podcast</h3>
        {podcastLoading ? (
          <p>Loading podcast storage...</p>
        ) : podcastStorage && podcastStorage.podcasts.length > 0 ? (
          <div className="podcast-storage-list">
            {podcastStorage.podcasts.map((podcast) => (
              <div key={podcast.podcast_id} className="podcast-storage-item">
                <div className="podcast-storage-info">
                  <div className="podcast-storage-title">{podcast.podcast_title}</div>
                  <div className="podcast-storage-stats">
                    <span>{podcast.episode_count} episodes</span>
                    <span className="separator">•</span>
                    <span>{podcast.synced_count} synced</span>
                  </div>
                </div>
                <div className="podcast-storage-size">
                  {podcast.total_mb.toFixed(2)} MB
                </div>
              </div>
            ))}
          </div>
        ) : (
          <p className="empty-message">No podcasts found</p>
        )}
      </div>

      {/* Cleanup Actions */}
      <div className="card cleanup-card">
        <h3>Cleanup Actions</h3>
        <div className="cleanup-form">
          <div className="form-group">
            <label htmlFor="cleanup-type">Cleanup Type</label>
            <select
              id="cleanup-type"
              value={cleanupType}
              onChange={(e) => setCleanupType(e.target.value as any)}
              className="form-control"
            >
              <option value="failed">Failed Downloads</option>
              <option value="orphaned">Orphaned Files</option>
              <option value="age">Episodes Older Than</option>
              <option value="storage_limit">Meet Storage Limit</option>
            </select>
          </div>

          {cleanupType === 'age' && (
            <div className="form-group">
              <label htmlFor="days-old">Delete Episodes Older Than (days)</label>
              <input
                id="days-old"
                type="number"
                value={daysOld}
                onChange={(e) => setDaysOld(parseInt(e.target.value))}
                className="form-control"
                min="1"
              />
            </div>
          )}

          {cleanupType === 'storage_limit' && (
            <div className="form-group">
              <label htmlFor="max-storage">Maximum Storage (MB)</label>
              <input
                id="max-storage"
                type="number"
                value={maxStorageMb}
                onChange={(e) => setMaxStorageMb(parseInt(e.target.value))}
                className="form-control"
                min="100"
              />
            </div>
          )}

          {(cleanupType === 'age' || cleanupType === 'storage_limit') && (
            <div className="form-group checkbox-group">
              <label>
                <input
                  type="checkbox"
                  checked={keepSynced}
                  onChange={(e) => setKeepSynced(e.target.checked)}
                />
                <span>Keep episodes synced to watch</span>
              </label>
            </div>
          )}

          <div className="cleanup-info">
            <p>
              {cleanupType === 'failed' && 'Delete all episodes with failed download status.'}
              {cleanupType === 'orphaned' && 'Delete files on disk that have no database record.'}
              {cleanupType === 'age' && `Delete episodes older than ${daysOld} days${keepSynced ? ' (excluding synced)' : ''}.`}
              {cleanupType === 'storage_limit' && `Delete oldest episodes to keep storage under ${maxStorageMb} MB${keepSynced ? ' (excluding synced)' : ''}.`}
            </p>
          </div>

          <button
            className="btn btn-danger btn-large"
            onClick={handleCleanup}
            disabled={cleanupMutation.isPending}
          >
            {cleanupMutation.isPending ? 'Cleaning up...' : 'Run Cleanup'}
          </button>
        </div>
      </div>
    </div>
  )
}
