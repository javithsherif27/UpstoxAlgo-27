import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { apiClient } from '../lib/api';
import { 
  CandleDataDTO, 
  WebSocketStatusDTO, 
  LivePriceDTO, 
  MarketDataCollectionStatusDTO 
} from '../lib/types';

// Market data collection management
export function useMarketDataCollectionStatus() {
  return useQuery({
    queryKey: ['market-data-collection-status'],
    queryFn: async (): Promise<MarketDataCollectionStatusDTO> => {
      const response = await apiClient.get('/api/market-data/collection-status');
      return response.data;
    },
    refetchInterval: 2000, // Refresh every 2 seconds
  });
}

export function useStartMarketDataCollection() {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: async (): Promise<{status: string, message: string}> => {
      const response = await apiClient.post('/api/market-data/start');
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['market-data-collection-status'] });
      queryClient.invalidateQueries({ queryKey: ['websocket-status'] });
    }
  });
}

export function useStopMarketDataCollection() {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: async (): Promise<{status: string, message: string}> => {
      const response = await apiClient.post('/api/market-data/stop');
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['market-data-collection-status'] });
      queryClient.invalidateQueries({ queryKey: ['websocket-status'] });
    }
  });
}

// WebSocket status
export function useWebSocketStatus() {
  return useQuery({
    queryKey: ['websocket-status'],
    queryFn: async (): Promise<WebSocketStatusDTO> => {
      const response = await apiClient.get('/api/market-data/status');
      return response.data;
    },
    refetchInterval: 5000, // Refresh every 5 seconds
  });
}

// Candle data
export function useCandles(
  instrumentKey: string, 
  interval: string = '1m',
  startTime?: string,
  endTime?: string,
  limit: number = 100
) {
  return useQuery({
    queryKey: ['candles', instrumentKey, interval, startTime, endTime, limit],
    queryFn: async (): Promise<CandleDataDTO[]> => {
      const params = new URLSearchParams({
        interval,
        limit: limit.toString()
      });
      
      if (startTime) params.append('start_time', startTime);
      if (endTime) params.append('end_time', endTime);
      
      const response = await apiClient.get(`/api/market-data/candles/${instrumentKey}?${params}`);
      return response.data;
    },
    enabled: !!instrumentKey,
  });
}

export function useCandlesForSelectedInstruments(
  interval: string = '1m',
  limit: number = 10
) {
  return useQuery({
    queryKey: ['candles-selected-instruments', interval, limit],
    queryFn: async () => {
      const params = new URLSearchParams({
        interval,
        limit: limit.toString()
      });
      
      const response = await apiClient.get(`/api/market-data/candles?${params}`);
      return response.data;
    },
    refetchInterval: 10000, // Refresh every 10 seconds
  });
}

// Live prices
export function useLivePrices() {
  return useQuery({
    queryKey: ['live-prices'],
    queryFn: async () => {
      const response = await apiClient.get('/api/market-data/live-prices');
      return response.data;
    },
    refetchInterval: 3000, // Refresh every 3 seconds
  });
}