import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { useEffect } from 'react';
import { uiStream, StreamEvent } from '../lib/ws';
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
      const response = await apiClient.get('/api/market-data/collection-status-noauth');
      return response.data;
    },
    refetchInterval: 2000, // Refresh every 2 seconds
  });
}

export function useStartMarketDataCollection() {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: async (): Promise<{status: string, message: string}> => {
      // Send token in header and use noauth endpoint to simplify local runs
      const tokenEntry = (await import('../lib/auth')).getUpstoxToken?.();
      const headers = tokenEntry ? { 'X-Upstox-Access-Token': tokenEntry.token } : {};
      const response = await apiClient.post('/api/market-data/start-noauth', null, { headers });
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
      const response = await apiClient.post('/api/market-data/stop-noauth');
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
  interval: string = '1d',
  startTime?: string,
  endTime?: string,
  limit: number = 100
) {
  return useQuery({
    queryKey: ['candles', instrumentKey, interval, startTime, endTime, limit],
    queryFn: async (): Promise<CandleDataDTO[]> => {
      try {
        const params = new URLSearchParams({
          interval,
          limit: limit.toString()
        });
        
        if (startTime) params.append('start_time', startTime);
        if (endTime) params.append('end_time', endTime);
        
        const response = await apiClient.get(`/api/market-data/candles/${instrumentKey}?${params}`);
        return response.data;
      } catch (error) {
        console.error('Error fetching candles:', error);
        // Return empty array instead of failing
        return [];
      }
    },
    enabled: !!instrumentKey,
    retry: false, // Don't retry on auth failures
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

// WebSocket-powered live LTP updates that merge into the react-query cache
export function useLivePriceStream() {
  const queryClient = useQueryClient();
  useEffect(() => {
    uiStream.connect();
    const off = uiStream.on((evt: StreamEvent) => {
      if (evt.type !== 'tick') return;
      queryClient.setQueryData(['live-prices'], (prev: any) => {
        const prevPrices = prev?.prices ?? {};
        const existing = prevPrices[evt.instrument_key] ?? {
          symbol: evt.symbol,
          ltp: 0,
          open: 0,
          high: 0,
          low: 0,
          volume: 0,
          change: 0,
          change_percent: 0,
          timestamp: evt.timestamp,
        };

        const ltp = evt.ltp ?? existing.ltp;
        const open = existing.open ?? ltp;
        const change = open ? (ltp - open) : 0;
        const change_percent = open ? (change / open) * 100 : 0;

        return {
          ...(prev ?? {}),
          prices: {
            ...prevPrices,
            [evt.instrument_key]: {
              ...existing,
              symbol: evt.symbol || existing.symbol,
              ltp,
              change,
              change_percent,
              source: 'websocket',
              timestamp: evt.timestamp,
            },
          },
          timestamp: new Date().toISOString(),
        };
      });
    });
    return () => { off(); };
  }, [queryClient]);
}

// Fetch historical data for selected instruments
export function useFetchHistoricalData() {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: async (daysBack: number = 30): Promise<any> => {
      const response = await apiClient.post('/api/market-data/fetch-historical', null, {
        params: { days_back: daysBack }
      });
      return response.data;
    },
    onSuccess: () => {
      // Invalidate relevant queries to refresh data
      queryClient.invalidateQueries({ queryKey: ['live-prices'] });
      queryClient.invalidateQueries({ queryKey: ['candles'] });
      queryClient.invalidateQueries({ queryKey: ['market-data-collection-status'] });
    }
  });
}