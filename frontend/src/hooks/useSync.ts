import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { syncApi } from '../api/sync'

const QUERY_KEY = 'sync'

// Get sync status
export function useSyncStatus() {
  return useQuery({
    queryKey: [QUERY_KEY, 'status'],
    queryFn: () => syncApi.getStatus(),
    refetchInterval: 5000, // Refresh every 5 seconds
  })
}

// Start sync
export function useStartSync() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: () => syncApi.startSync(),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: [QUERY_KEY] })
      queryClient.invalidateQueries({ queryKey: ['episodes'] })
    },
  })
}

// Get sync history
export function useSyncHistory(limit = 20) {
  return useQuery({
    queryKey: [QUERY_KEY, 'history', limit],
    queryFn: () => syncApi.getHistory(limit),
  })
}

// Detect watch
export function useDetectWatch() {
  return useQuery({
    queryKey: [QUERY_KEY, 'detect'],
    queryFn: () => syncApi.detectWatch(),
    refetchInterval: 3000, // Check every 3 seconds
  })
}

// Get watch info
export function useWatchInfo() {
  return useQuery({
    queryKey: [QUERY_KEY, 'watch-info'],
    queryFn: () => syncApi.getWatchInfo(),
    retry: false, // Don't retry if watch not connected
    refetchInterval: (data) => (data ? 10000 : false), // Refresh every 10s if connected
  })
}
