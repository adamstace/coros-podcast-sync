import { useState } from 'react'
import { useCreatePodcast } from '../../hooks/usePodcasts'
import './AddPodcastDialog.css'

interface AddPodcastDialogProps {
  isOpen: boolean
  onClose: () => void
}

export default function AddPodcastDialog({ isOpen, onClose }: AddPodcastDialogProps) {
  const [rssUrl, setRssUrl] = useState('')
  const [episodeLimit, setEpisodeLimit] = useState(5)
  const [autoDownload, setAutoDownload] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const createMutation = useCreatePodcast()

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError(null)

    if (!rssUrl.trim()) {
      setError('Please enter an RSS feed URL')
      return
    }

    try {
      await createMutation.mutateAsync({
        rss_url: rssUrl.trim(),
        episode_limit: episodeLimit,
        auto_download: autoDownload,
      })

      // Reset form and close
      setRssUrl('')
      setEpisodeLimit(5)
      setAutoDownload(true)
      onClose()
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to add podcast. Please check the RSS URL.')
    }
  }

  if (!isOpen) return null

  return (
    <div className="dialog-overlay" onClick={onClose}>
      <div className="dialog" onClick={(e) => e.stopPropagation()}>
        <div className="dialog-header">
          <h2>Add Podcast</h2>
          <button className="close-button" onClick={onClose}>
            ×
          </button>
        </div>

        <form onSubmit={handleSubmit} className="dialog-form">
          {error && <div className="error-message">{error}</div>}

          <div className="form-group">
            <label htmlFor="rss-url">RSS Feed URL</label>
            <input
              id="rss-url"
              type="url"
              value={rssUrl}
              onChange={(e) => setRssUrl(e.target.value)}
              placeholder="https://example.com/podcast/feed.xml"
              className="form-input"
              required
            />
            <span className="form-hint">
              Enter the RSS feed URL of the podcast you want to subscribe to
            </span>
          </div>

          <div className="form-group">
            <label htmlFor="episode-limit">Episode Limit</label>
            <input
              id="episode-limit"
              type="number"
              min="1"
              max="100"
              value={episodeLimit}
              onChange={(e) => setEpisodeLimit(parseInt(e.target.value))}
              className="form-input"
              required
            />
            <span className="form-hint">
              Maximum number of episodes to keep (older episodes will be removed)
            </span>
          </div>

          <div className="form-group checkbox-group">
            <label>
              <input
                type="checkbox"
                checked={autoDownload}
                onChange={(e) => setAutoDownload(e.target.checked)}
              />
              <span>Automatically download new episodes</span>
            </label>
          </div>

          <div className="dialog-actions">
            <button type="button" className="btn btn-secondary" onClick={onClose}>
              Cancel
            </button>
            <button
              type="submit"
              className="btn btn-primary"
              disabled={createMutation.isPending}
            >
              {createMutation.isPending ? 'Adding...' : 'Add Podcast'}
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}
