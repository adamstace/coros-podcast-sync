import { useState } from 'react'
import { usePodcasts } from '../hooks/usePodcasts'
import PodcastCard from '../components/podcasts/PodcastCard'
import AddPodcastDialog from '../components/podcasts/AddPodcastDialog'
import './Podcasts.css'

export default function Podcasts() {
  const [isAddDialogOpen, setIsAddDialogOpen] = useState(false)
  const { data, isLoading, error } = usePodcasts()

  if (isLoading) {
    return (
      <div className="podcasts-page">
        <div className="page-header">
          <h2>Podcasts</h2>
        </div>
        <div className="loading-message">Loading podcasts...</div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="podcasts-page">
        <div className="page-header">
          <h2>Podcasts</h2>
        </div>
        <div className="error-message">
          Failed to load podcasts. Please try again.
        </div>
      </div>
    )
  }

  const podcasts = data?.podcasts || []

  return (
    <div className="podcasts-page">
      <div className="page-header">
        <h2>Podcasts</h2>
        <button
          className="btn btn-primary"
          onClick={() => setIsAddDialogOpen(true)}
        >
          Add Podcast
        </button>
      </div>

      {podcasts.length === 0 ? (
        <div className="empty-state">
          <h3>No podcasts yet</h3>
          <p>Get started by adding your first podcast!</p>
          <button
            className="btn btn-primary"
            onClick={() => setIsAddDialogOpen(true)}
          >
            Add Your First Podcast
          </button>
        </div>
      ) : (
        <div className="podcasts-grid">
          {podcasts.map((podcast) => (
            <PodcastCard key={podcast.id} podcast={podcast} />
          ))}
        </div>
      )}

      <AddPodcastDialog
        isOpen={isAddDialogOpen}
        onClose={() => setIsAddDialogOpen(false)}
      />
    </div>
  )
}
