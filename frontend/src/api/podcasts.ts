import { apiClient } from './client'
import { Podcast, PodcastCreate, PodcastUpdate } from '../types/podcast'

export interface PodcastListResponse {
  podcasts: Podcast[]
  total: number
}

export const podcastApi = {
  // Get all podcasts
  getAll: async (): Promise<PodcastListResponse> => {
    const response = await apiClient.get<PodcastListResponse>('/api/podcasts')
    return response.data
  },

  // Get podcast by ID
  getById: async (id: number): Promise<Podcast> => {
    const response = await apiClient.get<Podcast>(`/api/podcasts/${id}`)
    return response.data
  },

  // Create new podcast
  create: async (data: PodcastCreate): Promise<Podcast> => {
    const response = await apiClient.post<Podcast>('/api/podcasts', data)
    return response.data
  },

  // Update podcast
  update: async (id: number, data: PodcastUpdate): Promise<Podcast> => {
    const response = await apiClient.put<Podcast>(`/api/podcasts/${id}`, data)
    return response.data
  },

  // Delete podcast
  delete: async (id: number): Promise<void> => {
    await apiClient.delete(`/api/podcasts/${id}`)
  },

  // Refresh podcast episodes
  refresh: async (id: number): Promise<{ message: string; new_episodes_count: number }> => {
    const response = await apiClient.post(`/api/podcasts/${id}/refresh`)
    return response.data
  },
}
