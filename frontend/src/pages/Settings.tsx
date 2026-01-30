import { useState, useEffect } from 'react'
import { useSettings, useUpdateSettings, useResetSettings } from '../hooks/useSettings'
import './Settings.css'

export default function Settings() {
  const { data: settings, isLoading } = useSettings()
  const updateMutation = useUpdateSettings()
  const resetMutation = useResetSettings()

  // Form state
  const [formData, setFormData] = useState({
    default_episode_limit: 5,
    auto_download: true,
    check_interval_minutes: 60,
    audio_bitrate: '128k',
    max_storage_mb: 1000,
    auto_cleanup_enabled: true,
    cleanup_interval_hours: 24,
    watch_mount_path: '',
    music_folder_name: 'Music',
    auto_sync_enabled: true,
  })

  // Update form when settings load
  useEffect(() => {
    if (settings) {
      setFormData({
        default_episode_limit: settings.default_episode_limit,
        auto_download: settings.auto_download,
        check_interval_minutes: settings.check_interval_minutes,
        audio_bitrate: settings.audio_bitrate,
        max_storage_mb: settings.max_storage_mb,
        auto_cleanup_enabled: settings.auto_cleanup_enabled,
        cleanup_interval_hours: settings.cleanup_interval_hours,
        watch_mount_path: settings.watch_mount_path || '',
        music_folder_name: settings.music_folder_name,
        auto_sync_enabled: settings.auto_sync_enabled,
      })
    }
  }, [settings])

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()

    try {
      const updates = {
        ...formData,
        watch_mount_path: formData.watch_mount_path || undefined,
      }
      await updateMutation.mutateAsync(updates)
      alert('Settings saved successfully!\n\nNote: Some settings may require restarting the application to take effect.')
    } catch (error: any) {
      alert(error.response?.data?.detail || 'Failed to save settings')
    }
  }

  const handleReset = async () => {
    if (!confirm('Reset all settings to defaults? This cannot be undone.')) {
      return
    }

    try {
      await resetMutation.mutateAsync()
      alert('Settings reset to defaults. Please restart the application.')
    } catch (error: any) {
      alert(error.response?.data?.detail || 'Failed to reset settings')
    }
  }

  if (isLoading) {
    return (
      <div className="settings-page">
        <div className="page-header">
          <h2>Settings</h2>
        </div>
        <p>Loading settings...</p>
      </div>
    )
  }

  return (
    <div className="settings-page">
      <div className="page-header">
        <h2>Settings</h2>
      </div>

      <form onSubmit={handleSubmit} className="settings-form">
        {/* Podcast Settings */}
        <div className="card settings-section">
          <h3>Podcast Settings</h3>
          <div className="settings-grid">
            <div className="form-group">
              <label htmlFor="episode-limit">Default Episode Limit</label>
              <input
                id="episode-limit"
                type="number"
                value={formData.default_episode_limit}
                onChange={(e) => setFormData({ ...formData, default_episode_limit: parseInt(e.target.value) })}
                className="form-control"
                min="1"
                max="100"
              />
              <span className="form-help">Number of episodes to keep per podcast</span>
            </div>

            <div className="form-group">
              <label htmlFor="check-interval">Check Interval (minutes)</label>
              <input
                id="check-interval"
                type="number"
                value={formData.check_interval_minutes}
                onChange={(e) => setFormData({ ...formData, check_interval_minutes: parseInt(e.target.value) })}
                className="form-control"
                min="5"
                max="1440"
              />
              <span className="form-help">How often to check for new episodes</span>
            </div>

            <div className="form-group checkbox-group">
              <label>
                <input
                  type="checkbox"
                  checked={formData.auto_download}
                  onChange={(e) => setFormData({ ...formData, auto_download: e.target.checked })}
                />
                <span>Auto-download new episodes</span>
              </label>
              <span className="form-help">Automatically download episodes when found</span>
            </div>
          </div>
        </div>

        {/* Audio Settings */}
        <div className="card settings-section">
          <h3>Audio Conversion</h3>
          <div className="settings-grid">
            <div className="form-group">
              <label htmlFor="audio-bitrate">Audio Bitrate</label>
              <select
                id="audio-bitrate"
                value={formData.audio_bitrate}
                onChange={(e) => setFormData({ ...formData, audio_bitrate: e.target.value })}
                className="form-control"
              >
                <option value="64k">64 kbps (Low quality, small file)</option>
                <option value="96k">96 kbps</option>
                <option value="128k">128 kbps (Recommended)</option>
                <option value="192k">192 kbps (High quality)</option>
                <option value="256k">256 kbps (Very high quality)</option>
                <option value="320k">320 kbps (Maximum quality)</option>
              </select>
              <span className="form-help">Higher bitrate = better quality but larger files</span>
            </div>
          </div>
        </div>

        {/* Storage Settings */}
        <div className="card settings-section">
          <h3>Storage Management</h3>
          <div className="settings-grid">
            <div className="form-group">
              <label htmlFor="max-storage">Maximum Storage (MB)</label>
              <input
                id="max-storage"
                type="number"
                value={formData.max_storage_mb}
                onChange={(e) => setFormData({ ...formData, max_storage_mb: parseInt(e.target.value) })}
                className="form-control"
                min="100"
              />
              <span className="form-help">Maximum storage to use for podcast data</span>
            </div>

            <div className="form-group">
              <label htmlFor="cleanup-interval">Cleanup Interval (hours)</label>
              <input
                id="cleanup-interval"
                type="number"
                value={formData.cleanup_interval_hours}
                onChange={(e) => setFormData({ ...formData, cleanup_interval_hours: parseInt(e.target.value) })}
                className="form-control"
                min="1"
                max="168"
              />
              <span className="form-help">How often to run automatic cleanup</span>
            </div>

            <div className="form-group checkbox-group">
              <label>
                <input
                  type="checkbox"
                  checked={formData.auto_cleanup_enabled}
                  onChange={(e) => setFormData({ ...formData, auto_cleanup_enabled: e.target.checked })}
                />
                <span>Enable automatic cleanup</span>
              </label>
              <span className="form-help">Automatically clean failed downloads and orphaned files</span>
            </div>
          </div>
        </div>

        {/* Watch Settings */}
        <div className="card settings-section">
          <h3>Watch Configuration</h3>
          <div className="settings-grid">
            <div className="form-group">
              <label htmlFor="mount-path">Watch Mount Path (Optional)</label>
              <input
                id="mount-path"
                type="text"
                value={formData.watch_mount_path}
                onChange={(e) => setFormData({ ...formData, watch_mount_path: e.target.value })}
                className="form-control"
                placeholder="Leave empty for auto-detection"
              />
              <span className="form-help">Manual path to watch if auto-detection fails</span>
            </div>

            <div className="form-group">
              <label htmlFor="music-folder">Music Folder Name</label>
              <input
                id="music-folder"
                type="text"
                value={formData.music_folder_name}
                onChange={(e) => setFormData({ ...formData, music_folder_name: e.target.value })}
                className="form-control"
              />
              <span className="form-help">Name of the music folder on the watch</span>
            </div>

            <div className="form-group checkbox-group">
              <label>
                <input
                  type="checkbox"
                  checked={formData.auto_sync_enabled}
                  onChange={(e) => setFormData({ ...formData, auto_sync_enabled: e.target.checked })}
                />
                <span>Enable auto-sync</span>
              </label>
              <span className="form-help">Automatically sync when watch is connected</span>
            </div>
          </div>
        </div>

        {/* Server Info */}
        {settings && (
          <div className="card settings-section">
            <h3>Server Information</h3>
            <div className="server-info">
              <div className="info-row">
                <span className="info-label">Backend URL:</span>
                <span className="info-value">{settings.host}:{settings.port}</span>
              </div>
              <div className="info-row">
                <span className="info-label">Debug Mode:</span>
                <span className="info-value">{settings.debug ? 'Enabled' : 'Disabled'}</span>
              </div>
              <div className="info-row">
                <span className="info-label">Log Level:</span>
                <span className="info-value">{settings.log_level}</span>
              </div>
            </div>
          </div>
        )}

        {/* Actions */}
        <div className="settings-actions">
          <button
            type="submit"
            className="btn btn-primary btn-large"
            disabled={updateMutation.isPending}
          >
            {updateMutation.isPending ? 'Saving...' : 'Save Settings'}
          </button>

          <button
            type="button"
            className="btn btn-secondary btn-large"
            onClick={handleReset}
            disabled={resetMutation.isPending}
          >
            {resetMutation.isPending ? 'Resetting...' : 'Reset to Defaults'}
          </button>
        </div>
      </form>
    </div>
  )
}
