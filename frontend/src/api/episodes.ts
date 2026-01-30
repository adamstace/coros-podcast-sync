import { apiClient } from './client'
import { Episode } from '../types/episode'

export interface EpisodeListResponse {
  episodes: Episode[]
  total: number
}

export interface EpisodeFilters {
  podcast_id?: number
  download_status?: string
  limit?: number
  offset?: number
}

export const episodeApi = {
  // Get all episodes with filters
  getAll: async (filters?: EpisodeFilters): Promise<EpisodeListResponse> => {
    const response = await apiClient.get<EpisodeListResponse>('/api/episodes', {
      params: filters
    })
    return response.data
  },

  // Get episode by ID
  getById: async (id: number): Promise<Episode> => {
    const response = await apiClient.get<Episode>(`/api/episodes/${id}`)
    return response.data
  },

  // Download episode
  download: async (id: number): Promise<{ message: string; episode_id: number; status: string }> => {
    const response = await apiClient.post(`/api/episodes/${id}/download`)
    return response.data
  },

  // Cancel download
  cancelDownload: async (id: number): Promise<{ message: string; episode_id: number }> => {
    const response = await apiClient.delete(`/api/episodes/${id}/download`)
    return response.data
  },

  // Delete episode
  delete: async (id: number): Promise<void> => {
    await apiClient.delete(`/api/episodes/${id}`)
  },

  // Get download status
  getDownloadStatus: async (id: number): Promise<{
    status: string
    progress: number
    is_downloading: boolean
    local_path?: string
    file_size?: number
  }> => {
    const response = await apiClient.get(`/api/episodes/${id}/status`)
    return response.data
  },

  // Download all episodes for a podcast
  downloadAll: async (podcastId: number, limit?: number): Promise<{
    message: string
    podcast_id: number
    queued_count: number
    total_pending: number
  }> => {
    const response = await apiClient.post(`/api/episodes/podcast/${podcastId}/download-all`, null, {
      params: { limit }
    })
    return response.data
  },

  // Convert episode to MP3
  convert: async (id: number): Promise<{
    message: string
    episode_id: number
    converted_path: string
  }> => {
    const response = await apiClient.post(`/api/episodes/${id}/convert`)
    return response.data
  },
}
