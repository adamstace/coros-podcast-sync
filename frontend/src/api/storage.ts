import { apiClient } from './client'

export interface LocalStorageInfo {
  disk_total_bytes: number
  disk_used_bytes: number
  disk_free_bytes: number
  disk_used_percent: number
  episodes_bytes: number
  converted_bytes: number
  total_podcast_bytes: number
  episodes_mb: number
  converted_mb: number
  total_podcast_mb: number
}

export interface PodcastStorageItem {
  podcast_id: number
  podcast_title: string
  total_bytes: number
  total_mb: number
  episode_count: number
  synced_count: number
}

export interface StorageByPodcast {
  podcasts: PodcastStorageItem[]
}

export interface CleanupRequest {
  cleanup_type: 'age' | 'storage_limit' | 'failed' | 'orphaned'
  days_old?: number
  max_storage_mb?: number
  keep_synced?: boolean
}

export interface CleanupResult {
  success: boolean
  items_deleted: number
  bytes_freed: number
  mb_freed: number
  message: string
}

export const storageApi = {
  // Get local storage info
  getLocalStorage: async (): Promise<LocalStorageInfo> => {
    const response = await apiClient.get<LocalStorageInfo>('/api/storage/local')
    return response.data
  },

  // Get storage by podcast
  getStorageByPodcast: async (): Promise<StorageByPodcast> => {
    const response = await apiClient.get<StorageByPodcast>('/api/storage/by-podcast')
    return response.data
  },

  // Cleanup storage
  cleanup: async (request: CleanupRequest): Promise<CleanupResult> => {
    const response = await apiClient.post<CleanupResult>('/api/storage/cleanup', request)
    return response.data
  },
}
