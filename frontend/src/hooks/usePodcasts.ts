import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { podcastApi } from '../api/podcasts'
import { PodcastCreate, PodcastUpdate } from '../types/podcast'

const QUERY_KEY = 'podcasts'

// Get all podcasts
export function usePodcasts() {
  return useQuery({
    queryKey: [QUERY_KEY],
    queryFn: () => podcastApi.getAll(),
  })
}

// Get single podcast
export function usePodcast(id: number) {
  return useQuery({
    queryKey: [QUERY_KEY, id],
    queryFn: () => podcastApi.getById(id),
    enabled: !!id,
  })
}

// Create podcast
export function useCreatePodcast() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (data: PodcastCreate) => podcastApi.create(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: [QUERY_KEY] })
    },
  })
}

// Update podcast
export function useUpdatePodcast() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: ({ id, data }: { id: number; data: PodcastUpdate }) =>
      podcastApi.update(id, data),
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: [QUERY_KEY] })
      queryClient.invalidateQueries({ queryKey: [QUERY_KEY, variables.id] })
    },
  })
}

// Delete podcast
export function useDeletePodcast() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (id: number) => podcastApi.delete(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: [QUERY_KEY] })
    },
  })
}

// Refresh podcast
export function useRefreshPodcast() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (id: number) => podcastApi.refresh(id),
    onSuccess: (_, id) => {
      queryClient.invalidateQueries({ queryKey: [QUERY_KEY, id] })
      queryClient.invalidateQueries({ queryKey: [QUERY_KEY] })
    },
  })
}
