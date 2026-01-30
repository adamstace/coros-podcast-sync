import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { storageApi, CleanupRequest } from '../api/storage'

const QUERY_KEY = 'storage'

// Get local storage info
export function useLocalStorage() {
  return useQuery({
    queryKey: [QUERY_KEY, 'local'],
    queryFn: () => storageApi.getLocalStorage(),
    refetchInterval: 30000, // Refresh every 30 seconds
  })
}

// Get storage by podcast
export function useStorageByPodcast() {
  return useQuery({
    queryKey: [QUERY_KEY, 'by-podcast'],
    queryFn: () => storageApi.getStorageByPodcast(),
    refetchInterval: 30000, // Refresh every 30 seconds
  })
}

// Cleanup storage
export function useCleanup() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (request: CleanupRequest) => storageApi.cleanup(request),
    onSuccess: () => {
      // Invalidate all storage queries
      queryClient.invalidateQueries({ queryKey: [QUERY_KEY] })
      // Also invalidate episodes since they might have been deleted
      queryClient.invalidateQueries({ queryKey: ['episodes'] })
    },
  })
}
