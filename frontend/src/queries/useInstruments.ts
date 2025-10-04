import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { apiClient } from '../lib/api';
import { InstrumentDTO, SelectedInstrumentDTO, InstrumentCacheStatusDTO } from '../lib/types';

export function useInstruments(search?: string, limit?: number) {
  return useQuery({
    queryKey: ['instruments', search, limit],
    queryFn: async (): Promise<InstrumentDTO[]> => {
      const params = new URLSearchParams();
      if (search) params.append('search', search);
      if (limit) params.append('limit', limit.toString());
      
      const response = await apiClient.get(`/api/instruments?${params}`);
      return response.data;
    },
    retry: 1
  });
}

export function useInstrumentCacheStatus() {
  return useQuery({
    queryKey: ['instrument-cache-status'],
    queryFn: async (): Promise<InstrumentCacheStatusDTO> => {
      const response = await apiClient.get('/api/instruments/cache-status');
      return response.data;
    },
    refetchInterval: 5000 // Refresh every 5 seconds while refreshing
  });
}

export function useRefreshInstruments() {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: async (): Promise<InstrumentCacheStatusDTO> => {
      const response = await apiClient.post('/api/instruments/refresh');
      return response.data;
    },
    onSuccess: () => {
      // Invalidate instruments cache to trigger refetch
      queryClient.invalidateQueries({ queryKey: ['instruments'] });
      queryClient.invalidateQueries({ queryKey: ['instrument-cache-status'] });
    }
  });
}

export function useSelectedInstruments() {
  return useQuery({
    queryKey: ['selected-instruments'],
    queryFn: async (): Promise<SelectedInstrumentDTO[]> => {
      const response = await apiClient.get('/api/instruments/selected');
      return response.data;
    }
  });
}

export function useSelectedInstrumentKeys() {
  return useQuery({
    queryKey: ['selected-instrument-keys'],
    queryFn: async (): Promise<string[]> => {
      const response = await apiClient.get('/api/instruments/selected-keys');
      return response.data.selected_keys;
    }
  });
}

export function useSelectInstrument() {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: async (instrument: InstrumentDTO) => {
      const response = await apiClient.post('/api/instruments/select', instrument);
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['selected-instruments'] });
      queryClient.invalidateQueries({ queryKey: ['selected-instrument-keys'] });
    }
  });
}

export function useDeselectInstrument() {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: async (instrumentKey: string) => {
      const response = await apiClient.delete(`/api/instruments/select/${instrumentKey}`);
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['selected-instruments'] });
      queryClient.invalidateQueries({ queryKey: ['selected-instrument-keys'] });
    }
  });
}
