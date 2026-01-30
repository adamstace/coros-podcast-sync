import { Podcast } from '../../types/podcast'
import { useDeletePodcast, useRefreshPodcast } from '../../hooks/usePodcasts'
import { useDownloadAllEpisodes } from '../../hooks/useEpisodes'
import './PodcastCard.css'

interface PodcastCardProps {
  podcast: Podcast
  onEdit?: (podcast: Podcast) => void
}

export default function PodcastCard({ podcast, onEdit }: PodcastCardProps) {
  const deleteMutation = useDeletePodcast()
  const refreshMutation = useRefreshPodcast()
  const downloadAllMutation = useDownloadAllEpisodes()

  const handleDelete = () => {
    if (window.confirm(`Are you sure you want to delete "${podcast.title}"? This will also delete all downloaded episodes.`)) {
      deleteMutation.mutate(podcast.id)
    }
  }

  const handleRefresh = () => {
    refreshMutation.mutate(podcast.id)
  }

  const handleDownloadAll = () => {
    downloadAllMutation.mutate({ podcastId: podcast.id, limit: podcast.episode_limit })
  }

  return (
    <div className="podcast-card">
      <div className="podcast-card-header">
        {podcast.image_url && (
          <img
            src={podcast.image_url}
            alt={podcast.title}
            className="podcast-image"
          />
        )}
        <div className="podcast-info">
          <h3 className="podcast-title">{podcast.title}</h3>
          {podcast.description && (
            <p className="podcast-description">{podcast.description}</p>
          )}
        </div>
      </div>

      <div className="podcast-stats">
        <div className="stat">
          <span className="stat-label">Episodes:</span>
          <span className="stat-value">{podcast.episode_count || 0}</span>
        </div>
        <div className="stat">
          <span className="stat-label">Episode Limit:</span>
          <span className="stat-value">{podcast.episode_limit}</span>
        </div>
        <div className="stat">
          <span className="stat-label">Auto Download:</span>
          <span className="stat-value">{podcast.auto_download ? 'Yes' : 'No'}</span>
        </div>
      </div>

      {podcast.last_checked && (
        <div className="podcast-last-checked">
          Last checked: {new Date(podcast.last_checked).toLocaleString()}
        </div>
      )}

      <div className="podcast-actions">
        <button
          className="btn btn-primary"
          onClick={handleDownloadAll}
          disabled={downloadAllMutation.isPending}
        >
          {downloadAllMutation.isPending ? 'Downloading...' : 'Download All'}
        </button>
        <button
          className="btn btn-secondary"
          onClick={handleRefresh}
          disabled={refreshMutation.isPending}
        >
          {refreshMutation.isPending ? 'Refreshing...' : 'Refresh'}
        </button>
        <button
          className="btn btn-secondary"
          onClick={() => onEdit?.(podcast)}
        >
          Edit
        </button>
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
