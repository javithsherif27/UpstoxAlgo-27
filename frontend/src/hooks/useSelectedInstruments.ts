import { useQuery } from '@tanstack/react-query';

export interface SelectedInstrument {
  id: number;
  symbol: string;
  name: string;
  exchange: string;
  segment: string;
  instrument_key: string;
  is_active: boolean;
  created_at: string;
}

export const useSelectedInstruments = () => {
  return useQuery({
    queryKey: ['selectedInstruments'],
    queryFn: async (): Promise<SelectedInstrument[]> => {
      const backendUrl = import.meta.env.VITE_API_URL || 'http://localhost:8000';
      const response = await fetch(`${backendUrl}/api/instruments/selected`, {
        method: 'GET',
        credentials: 'include', // Include cookies for authentication
        headers: {
          'Content-Type': 'application/json',
        },
      });
      
      if (!response.ok) {
        let errorMessage = 'Failed to fetch selected instruments';
        try {
          const errorData = await response.json();
          errorMessage = errorData.detail || errorMessage;
        } catch {
          errorMessage = `HTTP ${response.status}: ${response.statusText}`;
        }
        throw new Error(errorMessage);
      }
      
      return response.json();
    },
    refetchInterval: 5 * 60 * 1000, // Refetch every 5 minutes
    refetchOnWindowFocus: false,
    retry: 1, // Retry once on failure
  });
};