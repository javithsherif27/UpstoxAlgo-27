import React, { useState, useMemo, useEffect } from 'react';
import { InstrumentSearch } from './InstrumentSearch';
import { Watchlist } from './Watchlist';
import { TradingChart } from './TradingChart';
import { HistoricalDataFetcher } from './HistoricalDataFetcher';
import { TradingDataManager } from './TradingDataManager';
import { useSelectedInstruments, useSelectInstrument, useDeselectInstrument } from '../queries/useInstruments';
import { useFetchHistoricalData } from '../queries/useMarketData';
import { getUpstoxToken, saveUpstoxToken } from '../lib/auth';

interface SelectedInstrument {
  instrumentKey: string;
  symbol: string;
  name: string;
}

export const TradingWorkspace: React.FC = () => {
  const [selectedInstrument, setSelectedInstrument] = useState<SelectedInstrument | null>(null);
  const [upstoxToken, setUpstoxToken] = useState<string>('');
  const [activeTab, setActiveTab] = useState<'market' | 'trading-manager'>('market');
  
  // Load cached token on component mount
  useEffect(() => {
    const cachedTokenEntry = getUpstoxToken();
    if (cachedTokenEntry && cachedTokenEntry.token) {
      setUpstoxToken(cachedTokenEntry.token);
    }
  }, []);
  
  // Get selected instruments from the backend
  const { data: backendSelectedInstruments = [], isLoading } = useSelectedInstruments();
  const selectMutation = useSelectInstrument();
  const deselectMutation = useDeselectInstrument();
  const fetchHistoricalMutation = useFetchHistoricalData();
  
  // Transform backend data to match our interface
  const watchlistInstruments = useMemo(() => {
    return backendSelectedInstruments.map(instrument => ({
      instrumentKey: instrument.instrument_key,
      symbol: instrument.symbol,
      name: instrument.name
    }));
  }, [backendSelectedInstruments]);

  const handleAddToWatchlist = (instrument: SelectedInstrument) => {
    // Check if instrument is already in watchlist
    const exists = watchlistInstruments.some(item => item.instrumentKey === instrument.instrumentKey);
    if (!exists) {
      // Add to backend selection
      selectMutation.mutate({
        instrument_key: instrument.instrumentKey,
        symbol: instrument.symbol,
        name: instrument.name,
        exchange: instrument.instrumentKey.split('|')[0] || 'NSE_EQ' // Extract exchange from instrument_key
      });
    }
  };

  const handleRemoveFromWatchlist = (instrumentKey: string) => {
    // Remove from backend selection
    deselectMutation.mutate(instrumentKey);
    
    // If removed instrument was selected, clear selection
    if (selectedInstrument?.instrumentKey === instrumentKey) {
      setSelectedInstrument(null);
    }
  };

  const handleSelectInstrument = (instrument: SelectedInstrument) => {
    setSelectedInstrument(instrument);
  };

  const handleFetchHistoricalData = () => {
    fetchHistoricalMutation.mutate(30); // Fetch last 30 days
  };

  const handleTokenChange = (newToken: string) => {
    setUpstoxToken(newToken);
    // Auto-save to cache when token is entered manually
    if (newToken.trim()) {
      // Set expiry to end of current day (tokens typically expire daily)
      const endOfDay = new Date();
      endOfDay.setHours(23, 59, 59, 999);
      saveUpstoxToken(newToken.trim(), endOfDay.toISOString());
    }
  };

  return (
    <div className="h-screen flex flex-col bg-gray-50">
      {/* Top Navigation Bar */}
      <div className="bg-white border-b border-gray-200 px-4 py-2">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-6">
            <h1 className="text-xl font-semibold text-gray-800">Trading Terminal</h1>
            <nav className="flex space-x-4">
              <button 
                onClick={() => setActiveTab('market')}
                className={`font-medium ${activeTab === 'market' ? 'text-blue-600' : 'text-gray-600 hover:text-gray-800'}`}
              >
                📈 Market
              </button>
              <button 
                onClick={() => setActiveTab('trading-manager')}
                className={`font-medium ${activeTab === 'trading-manager' ? 'text-blue-600' : 'text-gray-600 hover:text-gray-800'}`}
              >
                🚀 Trading Data Manager
              </button>
              <button className="text-gray-600 hover:text-gray-800">Orders</button>
              <button className="text-gray-600 hover:text-gray-800">Positions</button>
              <button className="text-gray-600 hover:text-gray-800">Holdings</button>
            </nav>
          </div>
          
          {/* Search Bar */}
          <div className="flex-1 max-w-md mx-8">
            <InstrumentSearch onAddToWatchlist={handleAddToWatchlist} />
          </div>

          {/* Token Input & User Info */}
          <div className="flex items-center space-x-3">
            <div className="flex items-center space-x-2">
              <input
                type="text"
                placeholder="Upstox Token (for data fetch)"
                value={upstoxToken}
                onChange={(e) => handleTokenChange(e.target.value)}
                className="px-3 py-1 text-sm border border-gray-300 rounded focus:outline-none focus:ring-2 focus:ring-blue-500 w-48"
              />
              <div className={`w-2 h-2 rounded-full ${upstoxToken ? 'bg-green-500' : 'bg-gray-300'}`}></div>
            </div>
            <div className="text-sm text-gray-600">
              <div className="font-medium">Portfolio: ₹0.00</div>
            </div>
            <div className="w-8 h-8 bg-blue-500 rounded-full flex items-center justify-center">
              <span className="text-white text-sm font-medium">U</span>
            </div>
          </div>
        </div>
      </div>

      {/* Main Trading Interface */}
      <div className="flex-1 flex overflow-hidden">
        {activeTab === 'market' ? (
          <>
            {/* Left Sidebar - Watchlist */}
            <div className="w-80 bg-white border-r border-gray-200 flex flex-col">
              <div className="p-3 border-b border-gray-200">
                <div className="flex justify-between items-center mb-2">
                  <h2 className="font-semibold text-gray-800">Watchlist</h2>
                  {isLoading && (
                    <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-blue-500"></div>
                  )}
                </div>
                {/* Enhanced Historical Data Fetcher */}
                {watchlistInstruments.length > 0 && (
                  <HistoricalDataFetcher 
                    token={upstoxToken || null}
                    className="mb-3"
                  />
                )}
              </div>
              <div className="flex-1 overflow-hidden">
                {isLoading ? (
                  <div className="flex items-center justify-center h-32">
                    <div className="text-center">
                      <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500 mx-auto mb-2"></div>
                      <div className="text-sm text-gray-500">Loading watchlist...</div>
                    </div>
                  </div>
                ) : watchlistInstruments.length === 0 ? (
                  <div className="flex items-center justify-center h-32">
                    <div className="text-center">
                      <div className="text-gray-400 text-3xl mb-2">📈</div>
                      <div className="text-sm font-medium text-gray-600 mb-1">No instruments in watchlist</div>
                      <div className="text-xs text-gray-500">Search and add instruments above</div>
                    </div>
                  </div>
                ) : (
                  <Watchlist
                    instruments={watchlistInstruments}
                    selectedInstrument={selectedInstrument}
                    onSelectInstrument={handleSelectInstrument}
                    onRemoveInstrument={handleRemoveFromWatchlist}
                  />
                )}
              </div>
            </div>

            {/* Main Content Area - Charts */}
            <div className="flex-1 flex flex-col">
              {selectedInstrument ? (
                <TradingChart 
                  instrument={selectedInstrument}
                />
              ) : (
                <div className="flex-1 flex items-center justify-center bg-gray-50">
                  <div className="text-center max-w-md">
                    <div className="text-gray-400 text-4xl mb-4">📈</div>
                    {watchlistInstruments.length === 0 ? (
                      <>
                        <h3 className="text-lg font-medium text-gray-600 mb-2">Build Your Watchlist</h3>
                        <p className="text-gray-500 mb-4">Start by adding instruments to your watchlist using the search bar above, or go to the Instruments page to select your favorites.</p>
                        <div className="text-sm text-gray-400">
                          💡 Tip: Use the search bar to find stocks like "INFY", "TCS", "RELIANCE"
                        </div>
                      </>
                    ) : (
                      <>
                        <h3 className="text-lg font-medium text-gray-600 mb-2">Select an instrument to view chart</h3>
                        <p className="text-gray-500">Click on any instrument from your watchlist to display its chart and trading data</p>
                      </>
                    )}
                  </div>
                </div>
              )}
            </div>
          </>
        ) : activeTab === 'trading-manager' ? (
          // Trading Data Manager - Full Width
          <div className="flex-1 overflow-auto">
            <TradingDataManager />
          </div>
        ) : null}
      </div>
    </div>
  );
};