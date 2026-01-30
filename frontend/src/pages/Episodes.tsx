import { useState } from 'react'
import { useEpisodes } from '../hooks/useEpisodes'
import { usePodcasts } from '../hooks/usePodcasts'
import EpisodeCard from '../components/episodes/EpisodeCard'
import './Episodes.css'

export default function Episodes() {
  const [selectedPodcast, setSelectedPodcast] = useState<number | undefined>(undefined)
  const [selectedStatus, setSelectedStatus] = useState<string | undefined>(undefined)

  const { data: podcastsData } = usePodcasts()
  const { data, isLoading, error } = useEpisodes({
    podcast_id: selectedPodcast,
    download_status: selectedStatus,
    limit: 100
  })

  const podcasts = podcastsData?.podcasts || []
  const episodes = data?.episodes || []

  if (isLoading) {
    return (
      <div className="episodes-page">
        <div className="page-header">
          <h2>Episodes</h2>
        </div>
        <div className="loading-message">Loading episodes...</div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="episodes-page">
        <div className="page-header">
          <h2>Episodes</h2>
        </div>
        <div className="error-message">
          Failed to load episodes. Please try again.
        </div>
      </div>
    )
  }

  return (
    <div className="episodes-page">
      <div className="page-header">
        <h2>Episodes</h2>
        <div className="episode-count">
          {data?.total || 0} episode{data?.total !== 1 ? 's' : ''}
        </div>
      </div>

      <div className="filters">
        <div className="filter-group">
          <label htmlFor="podcast-filter">Podcast:</label>
          <select
            id="podcast-filter"
            value={selectedPodcast || ''}
            onChange={(e) => setSelectedPodcast(e.target.value ? parseInt(e.target.value) : undefined)}
            className="filter-select"
          >
            <option value="">All Podcasts</option>
            {podcasts.map((podcast) => (
              <option key={podcast.id} value={podcast.id}>
                {podcast.title}
              </option>
            ))}
          </select>
        </div>

        <div className="filter-group">
          <label htmlFor="status-filter">Status:</label>
          <select
            id="status-filter"
            value={selectedStatus || ''}
            onChange={(e) => setSelectedStatus(e.target.value || undefined)}
            className="filter-select"
          >
            <option value="">All Statuses</option>
            <option value="pending">Pending</option>
            <option value="downloading">Downloading</option>
            <option value="downloaded">Downloaded</option>
            <option value="failed">Failed</option>
          </select>
        </div>
      </div>

      {episodes.length === 0 ? (
        <div className="empty-state">
          <h3>No episodes found</h3>
          <p>
            {selectedPodcast || selectedStatus
              ? 'Try adjusting your filters'
              : 'Add some podcasts to see their episodes here'}
          </p>
        </div>
      ) : (
        <div className="episodes-list">
          {episodes.map((episode) => (
            <EpisodeCard key={episode.id} episode={episode} />
          ))}
        </div>
      )}
    </div>
  )
}
