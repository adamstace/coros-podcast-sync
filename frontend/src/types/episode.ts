export interface Episode {
  id: number
  podcast_id: number
  title: string
  description?: string
  audio_url: string
  guid: string
  pub_date?: string
  duration?: number
  file_size?: number
  download_status: 'pending' | 'downloading' | 'downloaded' | 'failed'
  download_progress: number
  local_path?: string
  converted_path?: string
  synced_to_watch: boolean
  sync_date?: string
  created_at: string
  updated_at: string
}
