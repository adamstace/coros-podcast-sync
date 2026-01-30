import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { episodeApi, EpisodeFilters } from '../api/episodes'

const QUERY_KEY = 'episodes'

// Get all episodes
export function useEpisodes(filters?: EpisodeFilters) {
  return useQuery({
    queryKey: [QUERY_KEY, filters],
    queryFn: () => episodeApi.getAll(filters),
  })
}

// Get single episode
export function useEpisode(id: number) {
  return useQuery({
    queryKey: [QUERY_KEY, id],
    queryFn: () => episodeApi.getById(id),
    enabled: !!id,
  })
}

// Download episode
export function useDownloadEpisode() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (id: number) => episodeApi.download(id),
    onSuccess: (_, id) => {
      queryClient.invalidateQueries({ queryKey: [QUERY_KEY] })
      queryClient.invalidateQueries({ queryKey: [QUERY_KEY, id] })
    },
  })
}

// Cancel download
export function useCancelDownload() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (id: number) => episodeApi.cancelDownload(id),
    onSuccess: (_, id) => {
      queryClient.invalidateQueries({ queryKey: [QUERY_KEY] })
      queryClient.invalidateQueries({ queryKey: [QUERY_KEY, id] })
    },
  })
}

// Delete episode
export function useDeleteEpisode() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (id: number) => episodeApi.delete(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: [QUERY_KEY] })
      queryClient.invalidateQueries({ queryKey: ['podcasts'] })
    },
  })
}

// Download all episodes for a podcast
export function useDownloadAllEpisodes() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: ({ podcastId, limit }: { podcastId: number; limit?: number }) =>
      episodeApi.downloadAll(podcastId, limit),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: [QUERY_KEY] })
    },
  })
}

// Convert episode to MP3
export function useConvertEpisode() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (id: number) => episodeApi.convert(id),
    onSuccess: (_, id) => {
      queryClient.invalidateQueries({ queryKey: [QUERY_KEY] })
      queryClient.invalidateQueries({ queryKey: [QUERY_KEY, id] })
    },
  })
}
