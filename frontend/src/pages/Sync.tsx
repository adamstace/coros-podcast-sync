import { useState } from 'react'
import { useSyncStatus, useStartSync, useSyncHistory, useDetectWatch, useWatchInfo } from '../hooks/useSync'
import './Sync.css'

export default function Sync() {
  const [isSyncing, setIsSyncing] = useState(false)

  const { data: syncStatus } = useSyncStatus()
  const { data: watchDetect } = useDetectWatch()
  const { data: watchInfo, isLoading: watchInfoLoading } = useWatchInfo()
  const { data: history } = useSyncHistory()
  const startSyncMutation = useStartSync()

  const handleStartSync = async () => {
    if (!watchDetect?.connected) {
      alert('Please connect your watch via USB first')
      return
    }

    setIsSyncing(true)
    try {
      await startSyncMutation.mutateAsync()
      alert('Sync completed successfully!')
    } catch (error: any) {
      alert(error.response?.data?.detail || 'Sync failed. Please try again.')
    } finally {
      setIsSyncing(false)
    }
  }

  const formatBytes = (bytes: number) => {
    return (bytes / (1024 * 1024)).toFixed(2) + ' MB'
  }

  const watchConnected = watchDetect?.connected || false

  return (
    <div className="sync-page">
      <div className="page-header">
        <h2>Sync</h2>
      </div>

      {/* Watch Status Card */}
      <div className="card watch-status-card">
        <h3>Watch Status</h3>
        <div className="watch-status">
          <div className={`connection-indicator ${watchConnected ? 'connected' : 'disconnected'}`}>
            <span className="indicator-dot"></span>
            <span className="indicator-text">
              {watchConnected ? 'Connected' : 'Not Connected'}
            </span>
          </div>

          {watchConnected && watchInfo && !watchInfoLoading && (
            <div className="watch-details">
              <div className="detail-row">
                <span className="detail-label">Mount Point:</span>
                <span className="detail-value">{watchInfo.mount_point}</span>
              </div>
              <div className="detail-row">
                <span className="detail-label">Music Folder:</span>
                <span className="detail-value">{watchInfo.music_folder}</span>
              </div>
              <div className="detail-row">
                <span className="detail-label">Storage:</span>
                <span className="detail-value">
                  {watchInfo.used_mb?.toFixed(1)} MB / {watchInfo.total_mb?.toFixed(1)} MB
                  ({watchInfo.used_percent?.toFixed(1)}% used)
                </span>
              </div>
              <div className="detail-row">
                <span className="detail-label">Free Space:</span>
                <span className="detail-value">{watchInfo.free_mb?.toFixed(1)} MB</span>
              </div>
            </div>
          )}

          {!watchConnected && (
            <div className="connection-help">
              <p>Connect your Coros watch via USB to sync episodes.</p>
              <p className="help-text">
                Make sure your watch is in USB mode and mounted as a drive.
              </p>
            </div>
          )}
        </div>
      </div>

      {/* Sync Stats Card */}
      {syncStatus && (
        <div className="card sync-stats-card">
          <h3>Sync Statistics</h3>
          <div className="sync-stats">
            <div className="stat-item">
              <span className="stat-value">{syncStatus.total_episodes}</span>
              <span className="stat-label">Total Episodes</span>
            </div>
            <div className="stat-item">
              <span className="stat-value">{syncStatus.synced_episodes}</span>
              <span className="stat-label">Synced to Watch</span>
            </div>
            <div className="stat-item">
              <span className="stat-value">{syncStatus.pending_sync}</span>
              <span className="stat-label">Pending Sync</span>
            </div>
          </div>
        </div>
      )}

      {/* Sync Actions Card */}
      <div className="card sync-actions-card">
        <h3>Sync Actions</h3>
        <div className="sync-actions">
          <button
            className="btn btn-primary btn-large"
            onClick={handleStartSync}
            disabled={!watchConnected || isSyncing}
          >
            {isSyncing ? 'Syncing...' : 'Start Sync'}
          </button>
          {syncStatus && syncStatus.pending_sync > 0 && (
            <p className="sync-info">
              {syncStatus.pending_sync} episode{syncStatus.pending_sync !== 1 ? 's' : ''} will be synced to your watch.
            </p>
          )}
        </div>
      </div>

      {/* Sync History Card */}
      {history && history.length > 0 && (
        <div className="card sync-history-card">
          <h3>Sync History</h3>
          <div className="sync-history">
            {history.map((record) => (
              <div key={record.id} className="history-item">
                <div className="history-header">
                  <span className={`history-status status-${record.status}`}>
                    {record.status}
                  </span>
                  <span className="history-date">
                    {new Date(record.started_at).toLocaleString()}
                  </span>
                </div>
                <div className="history-details">
                  <span className="history-detail">
                    +{record.episodes_added} added
                  </span>
                  <span className="history-detail">
                    -{record.episodes_removed} removed
                  </span>
                  <span className="history-detail">
                    {formatBytes(record.bytes_transferred)} transferred
                  </span>
                </div>
                {record.error_message && (
                  <div className="history-error">
                    Error: {record.error_message}
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}
