import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { settingsApi, SettingsUpdate } from '../api/settings'

const QUERY_KEY = 'settings'

// Get settings
export function useSettings() {
  return useQuery({
    queryKey: [QUERY_KEY],
    queryFn: () => settingsApi.getSettings(),
  })
}

// Update settings
export function useUpdateSettings() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (updates: SettingsUpdate) => settingsApi.updateSettings(updates),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: [QUERY_KEY] })
    },
  })
}

// Reset settings
export function useResetSettings() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: () => settingsApi.resetSettings(),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: [QUERY_KEY] })
    },
  })
}
