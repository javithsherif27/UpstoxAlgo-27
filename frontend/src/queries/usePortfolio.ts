import { useQuery } from '@tanstack/react-query';
import { apiClient } from '../lib/api';

export function useHoldings() {
  return useQuery({
    queryKey: ['holdings'],
    queryFn: async () => {
      const { data } = await apiClient.get('/api/portfolio/holdings');
      return data.holdings as any[];
    },
    refetchInterval: 30_000,
  });
}

export function usePositions() {
  return useQuery({
    queryKey: ['positions'],
    queryFn: async () => {
      const { data } = await apiClient.get('/api/portfolio/positions');
      return data.positions as any[];
    },
    refetchInterval: 30_000,
  });
}

export function usePortfolioStreamStatus() {
  return useQuery({
    queryKey: ['portfolio-stream-status'],
    queryFn: async () => {
      const { data } = await apiClient.get('/api/portfolio/stream/status');
      return data as { isConnected: boolean; holdingsCount: number; positionsCount: number };
    },
    refetchInterval: 15000,
  });
}

export async function startPortfolioStream() {
  await apiClient.post('/api/portfolio/stream/start', {});
}

export async function stopPortfolioStream() {
  await apiClient.post('/api/portfolio/stream/stop', {});
}
