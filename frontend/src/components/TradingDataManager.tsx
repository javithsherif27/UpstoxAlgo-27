import React, { useState, useEffect } from 'react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { apiClient } from '../lib/api';

interface TradingStatus {
  historical_data: {
    complete: boolean;
    completion_percentage: number;
    instruments_complete: number;
    total_instruments: number;
    gaps_detected: number;
  };
  websocket: {
    active: boolean;
    connected_instruments: number;
  };
  recovery: {
    in_progress: boolean;
  };
  trading_ready: boolean;
  market_hours: boolean;
}

interface TradingInstrument {
  instrument_key: string;
  symbol: string;
  name: string;
  is_selected: boolean;
  historical_complete: boolean;
  websocket_active: boolean;
  last_candle_time?: string;
  data_gaps_count: number;
}

export const TradingDataManager: React.FC = () => {
  const queryClient = useQueryClient();
  const [currentPhase, setCurrentPhase] = useState<'idle' | 'initializing' | 'fetching' | 'websocket' | 'trading'>('idle');
  const [logs, setLogs] = useState<string[]>([]);
  
  const addLog = (message: string) => {
    const timestamp = new Date().toLocaleTimeString();
    setLogs(prev => [...prev.slice(-19), `[${timestamp}] ${message}`]);
  };

  // Get trading status
  const { data: tradingStatus, refetch: refetchStatus } = useQuery({
    queryKey: ['trading-status'],
    queryFn: async (): Promise<TradingStatus> => {
      const response = await apiClient.get('/api/trading/status');
      return response.data;
    },
    refetchInterval: 2000, // Refresh every 2 seconds
  });

  // Get instruments
  const { data: instruments } = useQuery({
    queryKey: ['trading-instruments'], 
    queryFn: async (): Promise<TradingInstrument[]> => {
      const response = await apiClient.get('/api/trading/instruments');
      return response.data.instruments;
    },
    refetchInterval: 5000,
  });

  // Initialize trading system
  const initializeMutation = useMutation({
    mutationFn: async () => {
      const response = await apiClient.post('/api/trading/initialize');
      return response.data;
    },
    onSuccess: (data) => {
      addLog(`✅ Trading system initialized: ${data.instruments_count} instruments`);
      setCurrentPhase('initializing');
      queryClient.invalidateQueries({ queryKey: ['trading-status'] });
      queryClient.invalidateQueries({ queryKey: ['trading-instruments'] });
    },
    onError: (error: any) => {
      addLog(`❌ Initialization failed: ${error.response?.data?.detail || error.message}`);
    }
  });

  // Fetch complete historical data
  const fetchHistoricalMutation = useMutation({
    mutationFn: async () => {
      const response = await apiClient.post('/api/trading/fetch-historical-complete');
      return response.data;
    },
    onSuccess: (data) => {
      addLog(`📊 Historical data fetch started - Monitor status for completion`);
      setCurrentPhase('fetching');
    },
    onError: (error: any) => {
      addLog(`❌ Historical fetch failed: ${error.response?.data?.detail || error.message}`);
    }
  });

  // Start websocket
  const startWebsocketMutation = useMutation({
    mutationFn: async () => {
      const response = await apiClient.post('/api/trading/start-websocket');
      return response.data;
    },
    onSuccess: (data) => {
      addLog(`🌐 Websocket started successfully - Real-time data active`);
      setCurrentPhase('websocket');
    },
    onError: (error: any) => {
      addLog(`❌ Websocket failed: ${error.response?.data?.detail || error.message}`);
    }
  });

  // Recover gaps
  const recoverGapsMutation = useMutation({
    mutationFn: async () => {
      const response = await apiClient.post('/api/trading/recover-gaps');
      return response.data;
    },
    onSuccess: () => {
      addLog(`🔧 Gap recovery initiated`);
    },
    onError: (error: any) => {
      addLog(`❌ Gap recovery failed: ${error.response?.data?.detail || error.message}`);
    }
  });

  // Auto-advance phases based on status
  useEffect(() => {
    if (tradingStatus) {
      if (tradingStatus.historical_data.complete && currentPhase === 'fetching') {
        addLog(`🎯 Historical data: 100% COMPLETE - Ready for websocket`);
        setCurrentPhase('idle');
      }
      
      if (tradingStatus.trading_ready && currentPhase === 'websocket') {
        addLog(`🚀 TRADING READY - All systems operational`);
        setCurrentPhase('trading');
      }
    }
  }, [tradingStatus, currentPhase]);

  const getStatusColor = (percentage: number) => {
    if (percentage === 100) return 'text-green-600';
    if (percentage >= 75) return 'text-yellow-600';
    return 'text-red-600';
  };

  const getStatusBg = (percentage: number) => {
    if (percentage === 100) return 'bg-green-50 border-green-200';
    if (percentage >= 75) return 'bg-yellow-50 border-yellow-200';
    return 'bg-red-50 border-red-200';
  };

  return (
    <div className="max-w-6xl mx-auto p-6 space-y-6">
      {/* Header */}
      <div className="bg-gradient-to-r from-blue-600 to-indigo-600 text-white rounded-lg p-6">
        <h1 className="text-2xl font-bold mb-2">🚀 Trading Data Manager</h1>
        <p className="text-blue-100">100% Data Integrity for Stock Trading Operations</p>
        <div className="mt-4 flex items-center space-x-4 text-sm">
          <div className={`px-3 py-1 rounded-full ${tradingStatus?.market_hours ? 'bg-green-500' : 'bg-gray-500'}`}>
            {tradingStatus?.market_hours ? '📈 Market Open' : '📊 Market Closed'}
          </div>
          <div className={`px-3 py-1 rounded-full ${tradingStatus?.trading_ready ? 'bg-green-500' : 'bg-orange-500'}`}>
            {tradingStatus?.trading_ready ? '✅ Trading Ready' : '⚠️ Not Ready'}
          </div>
        </div>
      </div>

      {/* Control Panel */}
      <div className="bg-white rounded-lg shadow-sm border p-6">
        <h2 className="text-xl font-semibold mb-4">🎛️ Control Panel</h2>
        
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          {/* Step 1: Initialize */}
          <button
            onClick={() => initializeMutation.mutate()}
            disabled={initializeMutation.isPending}
            className="bg-blue-500 hover:bg-blue-600 disabled:bg-gray-400 text-white px-4 py-3 rounded-lg font-medium transition-colors"
          >
            {initializeMutation.isPending ? '⏳ Initializing...' : '🚀 1. Initialize System'}
          </button>

          {/* Step 2: Fetch Historical */}
          <button
            onClick={() => fetchHistoricalMutation.mutate()}
            disabled={fetchHistoricalMutation.isPending || !tradingStatus}
            className="bg-green-500 hover:bg-green-600 disabled:bg-gray-400 text-white px-4 py-3 rounded-lg font-medium transition-colors"
          >
            {fetchHistoricalMutation.isPending ? '⏳ Fetching...' : '📊 2. Fetch Historical Data'}
          </button>

          {/* Step 3: Start Websocket */}
          <button
            onClick={() => startWebsocketMutation.mutate()}
            disabled={
              startWebsocketMutation.isPending || 
              !tradingStatus?.historical_data.complete
            }
            className="bg-purple-500 hover:bg-purple-600 disabled:bg-gray-400 text-white px-4 py-3 rounded-lg font-medium transition-colors"
          >
            {startWebsocketMutation.isPending ? '⏳ Starting...' : '🌐 3. Start Websocket'}
          </button>

          {/* Gap Recovery */}
          <button
            onClick={() => recoverGapsMutation.mutate()}
            disabled={recoverGapsMutation.isPending}
            className="bg-orange-500 hover:bg-orange-600 disabled:bg-gray-400 text-white px-4 py-3 rounded-lg font-medium transition-colors"
          >
            {recoverGapsMutation.isPending ? '⏳ Recovering...' : '🔧 Recover Gaps'}
          </button>
        </div>

        {/* Usage Instructions */}
        <div className="mt-4 p-4 bg-blue-50 border border-blue-200 rounded-lg">
          <h3 className="font-semibold text-blue-900 mb-2">📋 Trading Workflow:</h3>
          <ol className="list-decimal list-inside text-sm text-blue-800 space-y-1">
            <li><strong>Initialize:</strong> Set up trading instruments and validate token</li>
            <li><strong>Fetch Historical:</strong> Download complete historical data (all timeframes)</li>
            <li><strong>Start Websocket:</strong> Begin real-time data feed (only after 100% historical)</li>
            <li><strong>Monitor:</strong> System continuously validates data integrity and fills gaps</li>
          </ol>
        </div>
      </div>

      {/* Status Dashboard */}
      {tradingStatus && (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {/* Historical Data Status */}
          <div className={`rounded-lg border p-6 ${getStatusBg(tradingStatus.historical_data.completion_percentage)}`}>
            <h3 className="text-lg font-semibold mb-4">📊 Historical Data Status</h3>
            
            <div className="space-y-3">
              <div className="flex justify-between items-center">
                <span className="font-medium">Completion:</span>
                <span className={`font-bold text-lg ${getStatusColor(tradingStatus.historical_data.completion_percentage)}`}>
                  {tradingStatus.historical_data.completion_percentage.toFixed(1)}%
                </span>
              </div>
              
              <div className="w-full bg-gray-200 rounded-full h-3">
                <div 
                  className={`h-3 rounded-full transition-all duration-500 ${
                    tradingStatus.historical_data.completion_percentage === 100 
                      ? 'bg-green-500' 
                      : 'bg-yellow-500'
                  }`}
                  style={{ width: `${tradingStatus.historical_data.completion_percentage}%` }}
                />
              </div>
              
              <div className="grid grid-cols-2 gap-4 text-sm">
                <div>
                  <div className="text-gray-600">Instruments Complete:</div>
                  <div className="font-semibold">{tradingStatus.historical_data.instruments_complete} / {tradingStatus.historical_data.total_instruments}</div>
                </div>
                <div>
                  <div className="text-gray-600">Gaps Detected:</div>
                  <div className={`font-semibold ${tradingStatus.historical_data.gaps_detected > 0 ? 'text-red-600' : 'text-green-600'}`}>
                    {tradingStatus.historical_data.gaps_detected}
                  </div>
                </div>
              </div>
            </div>
          </div>

          {/* Websocket Status */}
          <div className={`rounded-lg border p-6 ${tradingStatus.websocket.active ? 'bg-green-50 border-green-200' : 'bg-gray-50 border-gray-200'}`}>
            <h3 className="text-lg font-semibold mb-4">🌐 Real-time Feed Status</h3>
            
            <div className="space-y-3">
              <div className="flex items-center space-x-2">
                <div className={`w-4 h-4 rounded-full ${tradingStatus.websocket.active ? 'bg-green-500 animate-pulse' : 'bg-gray-400'}`} />
                <span className="font-medium">
                  {tradingStatus.websocket.active ? 'Connected & Active' : 'Disconnected'}
                </span>
              </div>
              
              <div className="text-sm">
                <div className="text-gray-600">Connected Instruments:</div>
                <div className="font-semibold text-lg">{tradingStatus.websocket.connected_instruments}</div>
              </div>
              
              <div className="text-xs text-gray-500">
                {tradingStatus.websocket.active 
                  ? '✅ Real-time market data flowing' 
                  : '⏳ Waiting for websocket activation'}
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Instruments Grid */}
      {instruments && instruments.length > 0 && (
        <div className="bg-white rounded-lg shadow-sm border">
          <div className="p-4 border-b">
            <h3 className="text-lg font-semibold">📈 Trading Instruments Status</h3>
          </div>
          
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 p-4">
            {instruments.map((instrument) => (
              <div 
                key={instrument.instrument_key}
                className={`p-4 rounded-lg border-2 transition-all ${
                  instrument.historical_complete && instrument.websocket_active
                    ? 'border-green-200 bg-green-50'
                    : instrument.historical_complete
                    ? 'border-yellow-200 bg-yellow-50'  
                    : 'border-red-200 bg-red-50'
                }`}
              >
                <div className="flex items-center justify-between mb-2">
                  <div className="font-semibold text-lg">{instrument.symbol}</div>
                  <div className="flex space-x-1">
                    <div className={`w-3 h-3 rounded-full ${instrument.historical_complete ? 'bg-green-500' : 'bg-red-500'}`} 
                         title="Historical Data" />
                    <div className={`w-3 h-3 rounded-full ${instrument.websocket_active ? 'bg-green-500 animate-pulse' : 'bg-gray-400'}`} 
                         title="Websocket" />
                  </div>
                </div>
                
                <div className="text-sm text-gray-600 mb-2">{instrument.name}</div>
                
                <div className="text-xs space-y-1">
                  <div className={`${instrument.historical_complete ? 'text-green-600' : 'text-red-600'}`}>
                    📊 Historical: {instrument.historical_complete ? 'Complete' : 'Incomplete'}
                  </div>
                  <div className={`${instrument.websocket_active ? 'text-green-600' : 'text-gray-500'}`}>
                    🌐 Websocket: {instrument.websocket_active ? 'Active' : 'Inactive'}
                  </div>
                  {instrument.data_gaps_count > 0 && (
                    <div className="text-orange-600">
                      ⚠️ Gaps: {instrument.data_gaps_count}
                    </div>
                  )}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Activity Log */}
      <div className="bg-white rounded-lg shadow-sm border">
        <div className="p-4 border-b">
          <h3 className="text-lg font-semibold">📋 System Activity Log</h3>
        </div>
        <div className="p-4">
          <div className="bg-gray-900 text-green-400 font-mono text-sm p-4 rounded-lg h-64 overflow-y-auto">
            {logs.length === 0 ? (
              <div className="text-gray-500">System ready - Start by clicking "Initialize System"</div>
            ) : (
              logs.map((log, index) => (
                <div key={index} className="mb-1">{log}</div>
              ))
            )}
          </div>
        </div>
      </div>

      {/* Trading Readiness */}
      {tradingStatus && (
        <div className={`rounded-lg border-2 p-6 ${
          tradingStatus.trading_ready 
            ? 'border-green-500 bg-green-50' 
            : 'border-orange-500 bg-orange-50'
        }`}>
          <div className="flex items-center space-x-3">
            <div className={`text-3xl ${tradingStatus.trading_ready ? '🟢' : '🟡'}`}>
              {tradingStatus.trading_ready ? '🟢' : '🟡'}
            </div>
            <div>
              <div className={`text-xl font-bold ${tradingStatus.trading_ready ? 'text-green-800' : 'text-orange-800'}`}>
                {tradingStatus.trading_ready ? 'READY FOR TRADING' : 'PREPARING TRADING SYSTEM'}
              </div>
              <div className={`text-sm ${tradingStatus.trading_ready ? 'text-green-600' : 'text-orange-600'}`}>
                {tradingStatus.trading_ready 
                  ? 'All systems operational - Historical data complete, real-time feed active'
                  : 'Complete historical data fetch and start websocket to enable trading'
                }
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};