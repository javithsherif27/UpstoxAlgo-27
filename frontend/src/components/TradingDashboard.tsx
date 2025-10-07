import React, { useState, useEffect } from 'react';
import { Search, Plus, TrendingUp, TrendingDown, Volume2 } from 'lucide-react';
import { TVChart } from './TVChart';

interface WatchlistItem {
  symbol: string;
  instrumentKey: string;
  ltp: number;
  change: number;
  changePercent: number;
  volume: number;
  high: number;
  low: number;
  open: number;
  close: number;
}

interface InstrumentMaster {
  instrument_key: string;
  exchange_token: string;
  tradingsymbol: string;
  name: string;
  last_price: number;
  expiry: string;
  strike: number;
  tick_size: number;
  lot_size: number;
  instrument_type: string;
  segment: string;
  exchange: string;
}

export const TradingDashboard: React.FC = () => {
  const [watchlist, setWatchlist] = useState<WatchlistItem[]>([]);
  const [selectedStock, setSelectedStock] = useState<string>('');
  const [searchQuery, setSearchQuery] = useState('');
  const [searchResults, setSearchResults] = useState<InstrumentMaster[]>([]);
  const [showSearchResults, setShowSearchResults] = useState(false);
  const [isLoading, setIsLoading] = useState(false);

  // Mock initial watchlist (you can replace this with data from backend)
  useEffect(() => {
    const initialWatchlist: WatchlistItem[] = [
      {
        symbol: 'INFY',
        instrumentKey: 'NSE_EQ|INFY-EQ',
        ltp: 1458.50,
        change: -17.50,
        changePercent: -1.19,
        volume: 179000,
        high: 1476.00,
        low: 1455.00,
        open: 1470.00,
        close: 1476.00
      },
      {
        symbol: 'TCS',
        instrumentKey: 'NSE_EQ|TCS-EQ',
        ltp: 2973.85,
        change: -14.20,
        changePercent: -0.48,
        volume: 65000,
        high: 2988.05,
        low: 2970.00,
        open: 2985.00,
        close: 2988.05
      },
      {
        symbol: 'GOLDBEES',
        instrumentKey: 'NSE_EQ|GOLDBEES-EQ',
        ltp: 99.66,
        change: 0.44,
        changePercent: 0.44,
        volume: 139965,
        high: 100.20,
        low: 99.40,
        open: 99.80,
        close: 99.22
      },
      {
        symbol: 'RELIANCE',
        instrumentKey: 'NSE_EQ|RELIANCE-EQ',
        ltp: 1384.80,
        change: 9.80,
        changePercent: 0.71,
        volume: 0,
        high: 1390.00,
        low: 1375.00,
        open: 1385.00,
        close: 1375.00
      }
    ];
    
    setWatchlist(initialWatchlist);
    if (initialWatchlist.length > 0) {
      setSelectedStock(initialWatchlist[0].symbol);
    }
  }, []);

  // Search instruments
  const handleSearch = async (query: string) => {
    setSearchQuery(query);
    if (query.length < 2) {
      setSearchResults([]);
      setShowSearchResults(false);
      return;
    }

    setIsLoading(true);
    try {
      // Replace with actual API call to search instruments
      const response = await fetch(`/api/instruments/search?query=${query}`);
      if (response.ok) {
        const results = await response.json();
        setSearchResults(results.slice(0, 10)); // Limit to 10 results
        setShowSearchResults(true);
      }
    } catch (error) {
      console.error('Search error:', error);
      // Mock search results for demo
      const mockResults: InstrumentMaster[] = [
        {
          instrument_key: 'NSE_EQ|HDFC-EQ',
          exchange_token: '1330',
          tradingsymbol: 'HDFC',
          name: 'HDFC Bank Limited',
          last_price: 1650.00,
          expiry: '',
          strike: 0,
          tick_size: 0.05,
          lot_size: 1,
          instrument_type: 'EQ',
          segment: 'NSE_EQ',
          exchange: 'NSE'
        }
      ].filter(item => 
        item.tradingsymbol.toLowerCase().includes(query.toLowerCase()) ||
        item.name.toLowerCase().includes(query.toLowerCase())
      );
      setSearchResults(mockResults);
      setShowSearchResults(true);
    }
    setIsLoading(false);
  };

  // Add instrument to watchlist
  const addToWatchlist = (instrument: InstrumentMaster) => {
    const newWatchlistItem: WatchlistItem = {
      symbol: instrument.tradingsymbol,
      instrumentKey: instrument.instrument_key,
      ltp: instrument.last_price || 0,
      change: 0,
      changePercent: 0,
      volume: 0,
      high: 0,
      low: 0,
      open: 0,
      close: instrument.last_price || 0
    };

    // Check if already in watchlist
    if (!watchlist.find(item => item.instrumentKey === instrument.instrument_key)) {
      setWatchlist(prev => [...prev, newWatchlistItem]);
    }

    setSearchQuery('');
    setShowSearchResults(false);
  };

  // Remove from watchlist
  const removeFromWatchlist = (instrumentKey: string) => {
    setWatchlist(prev => prev.filter(item => item.instrumentKey !== instrumentKey));
    if (selectedStock && watchlist.find(item => item.instrumentKey === instrumentKey)?.symbol === selectedStock) {
      setSelectedStock(watchlist.length > 1 ? watchlist[0].symbol : '');
    }
  };

  // Format number with appropriate decimals
  const formatNumber = (num: number, decimals: number = 2) => {
    return num.toLocaleString('en-IN', { 
      minimumFractionDigits: decimals,
      maximumFractionDigits: decimals 
    });
  };

  // Format volume
  const formatVolume = (volume: number) => {
    if (volume >= 10000000) return `${(volume / 10000000).toFixed(1)}Cr`;
    if (volume >= 100000) return `${(volume / 100000).toFixed(1)}L`;
    if (volume >= 1000) return `${(volume / 1000).toFixed(1)}K`;
    return volume.toString();
  };

  return (
    <div className="h-screen flex flex-col bg-gray-50">
      {/* Top Search Bar */}
      <div className="bg-white shadow-sm border-b px-4 py-3">
        <div className="flex items-center space-x-4">
          <div className="relative flex-1 max-w-md">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-4 h-4" />
            <input
              type="text"
              placeholder="Search stocks, ETFs, indices..."
              value={searchQuery}
              onChange={(e) => handleSearch(e.target.value)}
              className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            />
            
            {/* Search Results Dropdown */}
            {showSearchResults && (
              <div className="absolute top-full left-0 right-0 bg-white border border-gray-200 rounded-lg shadow-lg mt-1 z-50 max-h-60 overflow-y-auto">
                {isLoading ? (
                  <div className="p-3 text-center text-gray-500">Searching...</div>
                ) : searchResults.length > 0 ? (
                  searchResults.map((instrument) => (
                    <div
                      key={instrument.instrument_key}
                      onClick={() => addToWatchlist(instrument)}
                      className="p-3 hover:bg-gray-50 cursor-pointer border-b last:border-b-0 flex items-center justify-between"
                    >
                      <div>
                        <div className="font-semibold text-sm">{instrument.tradingsymbol}</div>
                        <div className="text-xs text-gray-500">{instrument.name}</div>
                        <div className="text-xs text-gray-400">{instrument.exchange}</div>
                      </div>
                      <Plus className="w-4 h-4 text-gray-400" />
                    </div>
                  ))
                ) : (
                  <div className="p-3 text-center text-gray-500">No results found</div>
                )}
              </div>
            )}
          </div>
          
          <div className="text-sm text-gray-600">
            {watchlist.length} stocks in watchlist
          </div>
        </div>
      </div>

      {/* Main Content */}
      <div className="flex-1 flex overflow-hidden">
        {/* Left Watchlist Panel */}
        <div className="w-80 bg-white shadow-sm border-r flex flex-col">
          <div className="px-4 py-3 bg-gray-50 border-b">
            <h2 className="font-semibold text-gray-800">Watchlist</h2>
          </div>
          
          <div className="flex-1 overflow-y-auto">
            {watchlist.map((item) => (
              <div
                key={item.instrumentKey}
                onClick={() => setSelectedStock(item.symbol)}
                className={`p-4 border-b hover:bg-gray-50 cursor-pointer transition-colors ${
                  selectedStock === item.symbol ? 'bg-blue-50 border-l-4 border-l-blue-500' : ''
                }`}
              >
                <div className="flex items-center justify-between mb-1">
                  <div className="font-semibold text-gray-800">{item.symbol}</div>
                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      removeFromWatchlist(item.instrumentKey);
                    }}
                    className="text-gray-400 hover:text-red-500 text-xs"
                  >
                    ×
                  </button>
                </div>
                
                <div className="flex items-center justify-between mb-2">
                  <div className="text-lg font-bold text-gray-900">
                    ₹{formatNumber(item.ltp)}
                  </div>
                  <div className={`flex items-center text-sm ${
                    item.change >= 0 ? 'text-green-600' : 'text-red-600'
                  }`}>
                    {item.change >= 0 ? (
                      <TrendingUp className="w-4 h-4 mr-1" />
                    ) : (
                      <TrendingDown className="w-4 h-4 mr-1" />
                    )}
                    {formatNumber(Math.abs(item.change))} ({Math.abs(item.changePercent).toFixed(2)}%)
                  </div>
                </div>
                
                <div className="grid grid-cols-2 gap-2 text-xs text-gray-600">
                  <div>High: ₹{formatNumber(item.high)}</div>
                  <div>Low: ₹{formatNumber(item.low)}</div>
                  <div>Open: ₹{formatNumber(item.open)}</div>
                  <div className="flex items-center">
                    <Volume2 className="w-3 h-3 mr-1" />
                    {formatVolume(item.volume)}
                  </div>
                </div>
              </div>
            ))}
            
            {watchlist.length === 0 && (
              <div className="p-8 text-center text-gray-500">
                <div className="mb-2">No stocks in watchlist</div>
                <div className="text-sm">Search and add stocks to get started</div>
              </div>
            )}
          </div>
        </div>

        {/* Right Chart Panel */}
        <div className="flex-1 flex flex-col bg-white">
          {selectedStock ? (
            <>
              <div className="px-6 py-4 bg-gray-50 border-b">
                <div className="flex items-center justify-between">
                  <div>
                    <h1 className="text-xl font-bold text-gray-800">{selectedStock}</h1>
                    {watchlist.find(item => item.symbol === selectedStock) && (
                      <div className="flex items-center space-x-4 mt-1">
                        <span className="text-2xl font-bold text-gray-900">
                          ₹{formatNumber(watchlist.find(item => item.symbol === selectedStock)!.ltp)}
                        </span>
                        <span className={`flex items-center text-sm ${
                          watchlist.find(item => item.symbol === selectedStock)!.change >= 0 
                            ? 'text-green-600' : 'text-red-600'
                        }`}>
                          {watchlist.find(item => item.symbol === selectedStock)!.change >= 0 ? (
                            <TrendingUp className="w-4 h-4 mr-1" />
                          ) : (
                            <TrendingDown className="w-4 h-4 mr-1" />
                          )}
                          {formatNumber(Math.abs(watchlist.find(item => item.symbol === selectedStock)!.change))} 
                          ({Math.abs(watchlist.find(item => item.symbol === selectedStock)!.changePercent).toFixed(2)}%)
                        </span>
                      </div>
                    )}
                  </div>
                </div>
              </div>
              
              <div className="flex-1 p-4">
                <TVChart 
                  symbol={selectedStock}
                  instrumentKey={watchlist.find(item => item.symbol === selectedStock)?.instrumentKey}
                  height={window.innerHeight - 200}
                />
              </div>
            </>
          ) : (
            <div className="flex-1 flex items-center justify-center text-gray-500">
              <div className="text-center">
                <div className="text-lg mb-2">No stock selected</div>
                <div className="text-sm">Select a stock from the watchlist to view chart</div>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};