import { apiClient } from './client'

export interface SyncStats {
  total_episodes: number
  synced_episodes: number
  pending_sync: number
  watch_connected: boolean
}

export interface SyncHistory {
  id: number
  sync_type: string
  episodes_added: number
  episodes_removed: number
  bytes_transferred: number
  status: string
  error_message?: string
  started_at: string
  completed_at?: string
  created_at: string
}

export interface WatchInfo {
  connected: boolean
  mount_point?: string
  music_folder?: string
  os?: string
  total_mb?: number
  free_mb?: number
  used_mb?: number
  used_percent?: number
}

export const syncApi = {
  // Get sync status/stats
  getStatus: async (): Promise<SyncStats> => {
    const response = await apiClient.get<SyncStats>('/api/sync/status')
    return response.data
  },

  // Start manual sync
  startSync: async (): Promise<{
    message: string
    episodes_added: number
    episodes_removed: number
    bytes_transferred: number
  }> => {
    const response = await apiClient.post('/api/sync/start')
    return response.data
  },

  // Get sync history
  getHistory: async (limit = 20): Promise<SyncHistory[]> => {
    const response = await apiClient.get<SyncHistory[]>('/api/sync/history', {
      params: { limit }
    })
    return response.data
  },

  // Detect watch
  detectWatch: async (): Promise<{
    connected: boolean
    mount_point?: string
    music_folder?: string
  }> => {
    const response = await apiClient.get('/api/sync/watch/detect')
    return response.data
  },

  // Get watch info
  getWatchInfo: async (): Promise<WatchInfo> => {
    const response = await apiClient.get<WatchInfo>('/api/sync/watch/info')
    return response.data
  },
}
