import { apiClient } from './client'

export interface Settings {
  // Podcast settings
  default_episode_limit: number
  auto_download: boolean
  check_interval_minutes: number

  // Audio conversion
  audio_format: string
  audio_bitrate: string

  // Storage
  max_storage_mb: number
  auto_cleanup_enabled: boolean
  cleanup_interval_hours: number

  // Watch
  watch_mount_path: string | null
  music_folder_name: string
  auto_sync_enabled: boolean

  // Server info
  host: string
  port: number
  debug: boolean
  log_level: string
}

export interface SettingsUpdate {
  // Podcast settings
  default_episode_limit?: number
  auto_download?: boolean
  check_interval_minutes?: number

  // Audio conversion
  audio_format?: string
  audio_bitrate?: string

  // Storage
  max_storage_mb?: number
  auto_cleanup_enabled?: boolean
  cleanup_interval_hours?: number

  // Watch
  watch_mount_path?: string
  music_folder_name?: string
  auto_sync_enabled?: boolean
}

export const settingsApi = {
  // Get current settings
  getSettings: async (): Promise<Settings> => {
    const response = await apiClient.get<Settings>('/api/settings')
    return response.data
  },

  // Update settings
  updateSettings: async (updates: SettingsUpdate): Promise<Settings> => {
    const response = await apiClient.put<Settings>('/api/settings', updates)
    return response.data
  },

  // Reset to defaults
  resetSettings: async (): Promise<{ message: string }> => {
    const response = await apiClient.post('/api/settings/reset')
    return response.data
  },
}
