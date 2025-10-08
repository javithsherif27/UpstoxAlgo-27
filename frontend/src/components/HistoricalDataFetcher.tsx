import React, { useState } from 'react';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { apiClient } from '../lib/api';
import { getUpstoxToken } from '../lib/auth';

interface FetchResult {
  status: string;
  message: string;
  interval?: string;
  instruments_processed?: number;
  instruments_successful?: number;
  total_candles?: number;
  days_back?: number;
  summary?: Record<string, any>;
  results?: Array<{
    symbol: string;
    success: boolean;
    candles: number;
    error?: string;
  }>;
}

interface HistoricalDataFetcherProps {
  token: string | null;
  className?: string;
}

export const HistoricalDataFetcher: React.FC<HistoricalDataFetcherProps> = ({ 
  token, 
  className = "" 
}) => {
  const [isExpanded, setIsExpanded] = useState(false);
  const [activeOperation, setActiveOperation] = useState<string | null>(null);
  const [lastResults, setLastResults] = useState<Record<string, FetchResult>>({});
  const queryClient = useQueryClient();

  // Individual interval fetchers
  const fetch1m = useMutation({
    mutationFn: async (days: number): Promise<FetchResult> => {
      // Token is automatically added by apiClient interceptor from cache
      const response = await apiClient.post(
        `/api/market-data/fetch-historical-1m?days_back=${days}`,
        {}
      );
      return response.data;
    },
    onSuccess: (data) => {
      setLastResults(prev => ({ ...prev, '1m': data }));
      queryClient.invalidateQueries({ queryKey: ['candles'] });
      setActiveOperation(null);
    },
    onError: () => setActiveOperation(null)
  });

  const fetch5m = useMutation({
    mutationFn: async (days: number): Promise<FetchResult> => {
      // Token is automatically added by apiClient interceptor from cache
      const response = await apiClient.post(
        `/api/market-data/fetch-historical-5m?days_back=${days}`,
        {}
      );
      return response.data;
    },
    onSuccess: (data) => {
      setLastResults(prev => ({ ...prev, '5m': data }));
      queryClient.invalidateQueries({ queryKey: ['candles'] });
      setActiveOperation(null);
    },
    onError: () => setActiveOperation(null)
  });

  const fetch15m = useMutation({
    mutationFn: async (days: number): Promise<FetchResult> => {
      // Token is automatically added by apiClient interceptor from cache
      const response = await apiClient.post(
        `/api/market-data/fetch-historical-15m?days_back=${days}`,
        {}
      );
      return response.data;
    },
    onSuccess: (data) => {
      setLastResults(prev => ({ ...prev, '15m': data }));
      queryClient.invalidateQueries({ queryKey: ['candles'] });
      setActiveOperation(null);
    },
    onError: () => setActiveOperation(null)
  });

  const fetch1d = useMutation({
    mutationFn: async (days: number): Promise<FetchResult> => {
      // Token is automatically added by apiClient interceptor from cache
      const response = await apiClient.post(
        `/api/market-data/fetch-historical-1d?days_back=${days}`,
        {}
      );
      return response.data;
    },
    onSuccess: (data) => {
      setLastResults(prev => ({ ...prev, '1d': data }));
      queryClient.invalidateQueries({ queryKey: ['candles'] });
      setActiveOperation(null);
    },
    onError: () => setActiveOperation(null)
  });

  const fetchAll = useMutation({
    mutationFn: async (days: number): Promise<FetchResult> => {
      // Token is automatically added by apiClient interceptor from cache
      const response = await apiClient.post(
        `/api/market-data/fetch-historical-all?days_back=${days}`,
        {}
      );
      return response.data;
    },
    onSuccess: (data) => {
      setLastResults(prev => ({ ...prev, 'all': data }));
      queryClient.invalidateQueries({ queryKey: ['candles'] });
      setActiveOperation(null);
    },
    onError: () => setActiveOperation(null)
  });

  const handleFetch = (interval: string, days: number) => {
    // Check for token: either from props or cached token
    const cachedToken = getUpstoxToken();
    const effectiveToken = token || (cachedToken?.token);
    
    if (!effectiveToken) {
      alert('Please provide your Upstox access token first');
      return;
    }

    setActiveOperation(interval);
    
    switch (interval) {
      case '1m':
        fetch1m.mutate(Math.min(days, 7)); // Limit 1m to 7 days
        break;
      case '5m':
        fetch5m.mutate(Math.min(days, 15)); // Limit 5m to 15 days
        break;
      case '15m':
        fetch15m.mutate(days);
        break;
      case '1d':
        fetch1d.mutate(days);
        break;
      case 'all':
        fetchAll.mutate(days);
        break;
    }
  };

  const getButtonState = (interval: string) => {
    const isActive = activeOperation === interval;
    const lastResult = lastResults[interval];
    
    if (isActive) {
      return {
        disabled: true,
        className: 'bg-blue-500 text-white animate-pulse',
        text: 'Fetching...'
      };
    }
    
    if (lastResult?.status === 'success') {
      return {
        disabled: false,
        className: 'bg-green-100 text-green-800 hover:bg-green-200 border-green-300',
        text: `✓ ${lastResult.total_candles || 0} candles`
      };
    }
    
    if (lastResult?.status === 'error') {
      return {
        disabled: false,
        className: 'bg-red-100 text-red-800 hover:bg-red-200 border-red-300',
        text: '✗ Failed'
      };
    }
    
    return {
      disabled: false,
      className: 'bg-white text-gray-700 hover:bg-gray-50 border-gray-300',
      text: 'Fetch'
    };
  };

  const formatResult = (result: FetchResult) => {
    if (result.status === 'success') {
      if (result.summary) {
        // All timeframes result
        return (
          <div className="space-y-1">
            <div className="text-sm font-medium text-green-700">
              ✅ {result.total_candles?.toLocaleString()} total candles
            </div>
            {Object.entries(result.summary).map(([interval, data]: [string, any]) => (
              <div key={interval} className="text-xs text-gray-600">
                {interval}: {data.total_candles?.toLocaleString()} candles ({data.success_rate})
              </div>
            ))}
          </div>
        );
      } else {
        // Single interval result
        return (
          <div className="text-sm text-green-700">
            ✅ {result.instruments_successful}/{result.instruments_processed} instruments
            <br />
            📊 {result.total_candles?.toLocaleString()} candles ({result.days_back} days)
          </div>
        );
      }
    }
    
    return (
      <div className="text-sm text-red-600">
        ❌ {result.message}
      </div>
    );
  };

  return (
    <div className={`bg-white border border-gray-200 rounded-lg shadow-sm ${className}`}>
      <div className="p-3 border-b border-gray-200">
        <button
          onClick={() => setIsExpanded(!isExpanded)}
          className="flex items-center justify-between w-full text-left"
        >
          <span className="font-medium text-gray-800">Historical Data Fetch</span>
          <svg
            className={`w-5 h-5 transition-transform ${isExpanded ? 'rotate-180' : ''}`}
            fill="currentColor"
            viewBox="0 0 20 20"
          >
            <path
              fillRule="evenodd"
              d="M5.293 7.293a1 1 0 011.414 0L10 10.586l3.293-3.293a1 1 0 111.414 1.414l-4 4a1 1 0 01-1.414 0l-4-4a1 1 0 010-1.414z"
              clipRule="evenodd"
            />
          </svg>
        </button>
      </div>

      {isExpanded && (
        <div className="p-4 space-y-4">
          {/* Token Status */}
          <div className="text-sm">
            <span className="font-medium">Token Status: </span>
            {(() => {
              const cachedToken = getUpstoxToken();
              const effectiveToken = token || (cachedToken?.token);
              const tokenSource = token ? '(Manual)' : cachedToken?.token ? '(Cached)' : '';
              return (
                <span className={effectiveToken ? 'text-green-600' : 'text-red-600'}>
                  {effectiveToken ? `✓ Configured ${tokenSource}` : '✗ Missing'}
                </span>
              );
            })()}
          </div>

          {/* Quick Fetch Buttons */}
          <div className="space-y-3">
            <div className="text-sm font-medium text-gray-700">Quick Fetch (Recommended Periods)</div>
            
            <div className="grid grid-cols-2 gap-2">
              <button
                onClick={() => handleFetch('1d', 30)}
                disabled={getButtonState('1d').disabled}
                className={`px-3 py-2 text-sm font-medium border rounded-md transition-colors ${getButtonState('1d').className}`}
              >
                Daily (30d) - {getButtonState('1d').text}
              </button>
              
              <button
                onClick={() => handleFetch('15m', 7)}
                disabled={getButtonState('15m').disabled}
                className={`px-3 py-2 text-sm font-medium border rounded-md transition-colors ${getButtonState('15m').className}`}
              >
                15min (7d) - {getButtonState('15m').text}
              </button>
              
              <button
                onClick={() => handleFetch('5m', 3)}
                disabled={getButtonState('5m').disabled}
                className={`px-3 py-2 text-sm font-medium border rounded-md transition-colors ${getButtonState('5m').className}`}
              >
                5min (3d) - {getButtonState('5m').text}
              </button>
              
              <button
                onClick={() => handleFetch('1m', 1)}
                disabled={getButtonState('1m').disabled}
                className={`px-3 py-2 text-sm font-medium border rounded-md transition-colors ${getButtonState('1m').className}`}
              >
                1min (1d) - {getButtonState('1m').text}
              </button>
            </div>

            {/* Fetch All Button */}
            <button
              onClick={() => handleFetch('all', 7)}
              disabled={getButtonState('all').disabled}
              className={`w-full px-4 py-3 text-sm font-medium border rounded-md transition-colors ${getButtonState('all').className}`}
            >
              🚀 Fetch All Timeframes (7d) - {getButtonState('all').text}
            </button>
          </div>

          {/* Results Display */}
          {Object.keys(lastResults).length > 0 && (
            <div className="border-t border-gray-200 pt-3 space-y-2">
              <div className="text-sm font-medium text-gray-700">Recent Results</div>
              {Object.entries(lastResults).map(([interval, result]) => (
                <div key={interval} className="p-2 bg-gray-50 rounded text-xs">
                  <div className="font-medium text-gray-600 mb-1">
                    {interval === 'all' ? 'All Timeframes' : interval.toUpperCase()}
                  </div>
                  {formatResult(result)}
                </div>
              ))}
            </div>
          )}

          {/* Rate Limiting Notice */}
          <div className="text-xs text-gray-500 bg-blue-50 p-2 rounded">
            ℹ️ <strong>Rate Limited:</strong> Fetching is automatically queued to respect Upstox API limits (~25 requests/minute).
            Large operations may take several minutes to complete.
          </div>
        </div>
      )}
    </div>
  );
};