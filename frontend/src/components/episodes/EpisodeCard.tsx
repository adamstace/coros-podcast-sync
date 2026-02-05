import { Episode } from '../../types/episode'
import { useDownloadEpisode, useCancelDownload, useDeleteEpisode, useConvertEpisode } from '../../hooks/useEpisodes'
import podcastPlaceholder from '../../assets/podcast-placeholder.svg'
import './EpisodeCard.css'

interface EpisodeCardProps {
  episode: Episode
}

export default function EpisodeCard({ episode }: EpisodeCardProps) {
  const downloadMutation = useDownloadEpisode()
  const cancelMutation = useCancelDownload()
  const deleteMutation = useDeleteEpisode()
  const convertMutation = useConvertEpisode()

  const handleDownload = () => {
    downloadMutation.mutate(episode.id)
  }

  const handleCancel = () => {
    cancelMutation.mutate(episode.id)
  }

  const handleDelete = () => {
    if (window.confirm(`Are you sure you want to delete "${episode.title}"?`)) {
      deleteMutation.mutate(episode.id)
    }
  }

  const handleConvert = () => {
    convertMutation.mutate(episode.id)
  }

  const formatDuration = (seconds?: number) => {
    if (!seconds) return 'Unknown'
    const hours = Math.floor(seconds / 3600)
    const minutes = Math.floor((seconds % 3600) / 60)
    if (hours > 0) {
      return `${hours}h ${minutes}m`
    }
    return `${minutes}m`
  }

  const formatFileSize = (bytes?: number) => {
    if (!bytes) return 'Unknown'
    const mb = bytes / (1024 * 1024)
    return `${mb.toFixed(1)} MB`
  }

  const getStatusBadge = () => {
    switch (episode.download_status) {
      case 'downloaded':
        return <span className="status-badge status-success">Downloaded</span>
      case 'downloading':
        return <span className="status-badge status-progress">Downloading</span>
      case 'failed':
        return <span className="status-badge status-error">Failed</span>
      case 'pending':
      default:
        return <span className="status-badge status-pending">Pending</span>
    }
  }

  return (
    <div className="episode-card">
      <div className="episode-header">
        <div className="episode-header-main">
          <img
            src={episode.podcast_image_url || podcastPlaceholder}
            alt={`${episode.title} podcast artwork`}
            className="episode-podcast-image"
            onError={(event) => {
              event.currentTarget.src = podcastPlaceholder
            }}
          />
          <h3 className="episode-title">{episode.title}</h3>
        </div>
        {getStatusBadge()}
      </div>

      {episode.description && (
        <div
          className="episode-description"
          dangerouslySetInnerHTML={{ __html: episode.description }}
        />
      )}

      <div className="episode-meta">
        {episode.pub_date && (
          <span className="meta-item">
            {new Date(episode.pub_date).toLocaleDateString()}
          </span>
        )}
        <span className="meta-item">Duration: {formatDuration(episode.duration)}</span>
        {episode.file_size && (
          <span className="meta-item">Size: {formatFileSize(episode.file_size)}</span>
        )}
      </div>

      {episode.download_status === 'downloading' && (
        <div className="download-progress">
          <div className="progress-bar">
            <div
              className="progress-fill"
              style={{ width: `${episode.download_progress}%` }}
            />
          </div>
          <span className="progress-text">{episode.download_progress}%</span>
        </div>
      )}

      {episode.converted_path && (
        <div className="converted-indicator">
          ✓ Converted to MP3
        </div>
      )}

      {episode.synced_to_watch && (
        <div className="synced-indicator">
          ✓ Synced to watch
          {episode.sync_date && ` on ${new Date(episode.sync_date).toLocaleDateString()}`}
        </div>
      )}

      <div className="episode-actions">
        {episode.download_status === 'pending' && (
          <button
            className="btn btn-primary"
            onClick={handleDownload}
            disabled={downloadMutation.isPending}
          >
            {downloadMutation.isPending ? 'Starting...' : 'Download'}
          </button>
        )}

        {episode.download_status === 'downloading' && (
          <button
            className="btn btn-secondary"
            onClick={handleCancel}
            disabled={cancelMutation.isPending}
          >
            {cancelMutation.isPending ? 'Cancelling...' : 'Cancel'}
          </button>
        )}

        {episode.download_status === 'failed' && (
          <button
            className="btn btn-primary"
            onClick={handleDownload}
            disabled={downloadMutation.isPending}
          >
            Retry
          </button>
        )}

        {episode.download_status === 'downloaded' && episode.local_path && !episode.converted_path && (
          <button
            className="btn btn-secondary"
            onClick={handleConvert}
            disabled={convertMutation.isPending}
          >
            {convertMutation.isPending ? 'Converting...' : 'Convert to MP3'}
          </button>
        )}

        <button
          className="btn btn-danger"
          onClick={handleDelete}
          disabled={deleteMutation.isPending}
        >
          {deleteMutation.isPending ? 'Deleting...' : 'Delete'}
        </button>
      </div>
    </div>
  )
}
