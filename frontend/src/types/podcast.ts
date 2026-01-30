export interface Podcast {
  id: number
  title: string
  rss_url: string
  description?: string
  image_url?: string
  episode_limit: number
  auto_download: boolean
  last_checked?: string
  created_at: string
  updated_at: string
}

export interface PodcastCreate {
  rss_url: string
  episode_limit?: number
  auto_download?: boolean
}

export interface PodcastUpdate {
  title?: string
  description?: string
  image_url?: string
  episode_limit?: number
  auto_download?: boolean
}
