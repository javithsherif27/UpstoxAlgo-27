import React, { useState } from 'react';
import { 
  useMarketDataCollectionStatus,
  useStartMarketDataCollection,
  useStopMarketDataCollection,
  useLivePrices,
  useCandlesForSelectedInstruments
} from '../queries/useMarketData';
import { useLivePriceStream } from '../queries/useMarketData';
import { TVChart } from './TVChart';

export const MarketDataDashboard: React.FC = () => {
  const [selectedInterval, setSelectedInterval] = useState('1m');
  useLivePriceStream();
  
  const { data: collectionStatus, isLoading: statusLoading } = useMarketDataCollectionStatus();
  const { data: livePrices, isLoading: pricesLoading } = useLivePrices();
  const { data: candlesData } = useCandlesForSelectedInstruments(selectedInterval, 5);
  const firstInstrument = React.useMemo(() => {
    if (!livePrices?.prices) return undefined;
    const entries = Object.entries(livePrices.prices);
    if (entries.length === 0) return undefined;
    const [instrumentKey, price] = entries[0] as any;
    return { instrumentKey, symbol: price.symbol } as { instrumentKey: string; symbol: string };
  }, [livePrices]);
  
  const startCollectionMutation = useStartMarketDataCollection();
  const stopCollectionMutation = useStopMarketDataCollection();

  const handleStartCollection = () => {
    startCollectionMutation.mutate();
  };

  const handleStopCollection = () => {
    stopCollectionMutation.mutate();
  };

  const formatPrice = (price: number) => {
    return price?.toFixed(2) || '0.00';
  };

  const formatChange = (change: number, changePercent: number) => {
    const sign = change >= 0 ? '+' : '';
    const color = change >= 0 ? 'text-green-600' : 'text-red-600';
    return (
      <span className={color}>
        {sign}{formatPrice(change)} ({sign}{changePercent?.toFixed(2)}%)
      </span>
    );
  };

  if (statusLoading) {
    return (
      <div className="p-4">
        <div className="animate-pulse">
          <div className="h-8 bg-gray-200 rounded mb-4"></div>
          <div className="h-32 bg-gray-200 rounded"></div>
        </div>
      </div>
    );
  }

  return (
    <div className="p-4 space-y-6">
      {/* Header and Controls */}
      <div className="flex justify-between items-center">
        <h2 className="text-2xl font-semibold">Market Data</h2>
        
        <div className="flex items-center space-x-4">
          {/* Connection Status */}
          <div className={`px-3 py-1 rounded-full text-sm font-medium ${
            collectionStatus?.is_collecting 
              ? 'bg-green-100 text-green-800' 
              : 'bg-gray-100 text-gray-800'
          }`}>
            {collectionStatus?.is_collecting ? 'Collecting' : 'Stopped'}
          </div>
          
          {/* Start/Stop Button */}
          {collectionStatus?.is_collecting ? (
            <button
              onClick={handleStopCollection}
              disabled={stopCollectionMutation.isPending}
              className="px-4 py-2 bg-red-500 text-white rounded-lg hover:bg-red-600 disabled:opacity-50"
            >
              {stopCollectionMutation.isPending ? 'Stopping...' : 'Stop Collection'}
            </button>
          ) : (
            <button
              onClick={handleStartCollection}
              disabled={startCollectionMutation.isPending}
              className="px-4 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600 disabled:opacity-50"
            >
              {startCollectionMutation.isPending ? 'Starting...' : 'Start Collection'}
            </button>
          )}
        </div>
      </div>

      {/* Connection Details */}
      {collectionStatus && (
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <div className="bg-white p-4 rounded-lg border">
            <div className="text-sm text-gray-500">Connection Status</div>
            <div className={`font-medium ${
              collectionStatus.is_connected ? 'text-green-600' : 'text-red-600'
            }`}>
              {collectionStatus.is_connected ? 'Connected' : 'Disconnected'}
            </div>
          </div>
          
          <div className="bg-white p-4 rounded-lg border">
            <div className="text-sm text-gray-500">Subscribed Instruments</div>
            <div className="font-medium">{collectionStatus.subscribed_instruments_count}</div>
          </div>
          
          <div className="bg-white p-4 rounded-lg border">
            <div className="text-sm text-gray-500">Ticks Received</div>
            <div className="font-medium">{collectionStatus.total_ticks_received?.toLocaleString()}</div>
          </div>
          
          <div className="bg-white p-4 rounded-lg border">
            <div className="text-sm text-gray-500">Last Heartbeat</div>
            <div className="font-medium text-xs">
              {collectionStatus.last_heartbeat 
                ? new Date(collectionStatus.last_heartbeat).toLocaleTimeString()
                : 'N/A'
              }
            </div>
          </div>
        </div>
      )}

      {/* Live Prices */}
      <div className="bg-white rounded-lg border">
        <div className="px-4 py-3 border-b">
          <h3 className="text-lg font-medium">Live Prices</h3>
        </div>
        
        <div className="p-4">
          {pricesLoading ? (
            <div className="text-center text-gray-500">Loading prices...</div>
          ) : livePrices?.prices && Object.keys(livePrices.prices).length > 0 ? (
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b">
                    <th className="text-left py-2">Symbol</th>
                    <th className="text-right py-2">LTP</th>
                    <th className="text-right py-2">Open</th>
                    <th className="text-right py-2">High</th>
                    <th className="text-right py-2">Low</th>
                    <th className="text-right py-2">Volume</th>
                    <th className="text-right py-2">Change</th>
                  </tr>
                </thead>
                <tbody>
                  {Object.entries(livePrices.prices).map(([instrumentKey, priceData]: [string, any]) => (
                    <tr key={instrumentKey} className="border-b hover:bg-gray-50">
                      <td className="py-2 font-medium">{priceData.symbol}</td>
                      <td className="py-2 text-right">{formatPrice(priceData.ltp)}</td>
                      <td className="py-2 text-right">{formatPrice(priceData.open)}</td>
                      <td className="py-2 text-right">{formatPrice(priceData.high)}</td>
                      <td className="py-2 text-right">{formatPrice(priceData.low)}</td>
                      <td className="py-2 text-right">{priceData.volume?.toLocaleString()}</td>
                      <td className="py-2 text-right">
                        {formatChange(priceData.change, priceData.change_percent)}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          ) : (
            <div className="text-center text-gray-500">
              No live price data available. Start data collection to see live prices.
            </div>
          )}
        </div>
      </div>

      {/* Candle Data */}
      {firstInstrument && (
        <div className="bg-white rounded-lg border">
          <div className="px-4 py-3 border-b flex justify-between items-center">
            <h3 className="text-lg font-medium">Chart - {firstInstrument.symbol}</h3>
          </div>
          <div className="p-2">
            <div style={{ height: 480 }}>
              <TVChart symbol={firstInstrument.symbol} instrumentKey={firstInstrument.instrumentKey} height={480} />
            </div>
          </div>
        </div>
      )}
      <div className="bg-white rounded-lg border">
        <div className="px-4 py-3 border-b flex justify-between items-center">
          <h3 className="text-lg font-medium">Recent Candles</h3>
          
          <select
            value={selectedInterval}
            onChange={(e) => setSelectedInterval(e.target.value)}
            className="px-3 py-1 border rounded-md text-sm"
          >
            <option value="1m">1 Minute</option>
            <option value="5m">5 Minutes</option>
            <option value="15m">15 Minutes</option>
          </select>
        </div>
        
        <div className="p-4">
          {candlesData?.instruments && Object.keys(candlesData.instruments).length > 0 ? (
            <div className="space-y-4">
              {Object.entries(candlesData.instruments).map(([instrumentKey, data]: [string, any]) => (
                <div key={instrumentKey} className="border rounded-lg p-3">
                  <h4 className="font-medium mb-2">{data.symbol}</h4>
                  
                  {data.candles && data.candles.length > 0 ? (
                    <div className="overflow-x-auto">
                      <table className="w-full text-xs">
                        <thead>
                          <tr className="border-b">
                            <th className="text-left py-1">Time</th>
                            <th className="text-right py-1">Open</th>
                            <th className="text-right py-1">High</th>
                            <th className="text-right py-1">Low</th>
                            <th className="text-right py-1">Close</th>
                            <th className="text-right py-1">Volume</th>
                            <th className="text-right py-1">Ticks</th>
                          </tr>
                        </thead>
                        <tbody>
                          {data.candles.slice(0, 3).map((candle: any, idx: number) => (
                            <tr key={idx} className="border-b">
                              <td className="py-1">{new Date(candle.timestamp).toLocaleTimeString()}</td>
                              <td className="py-1 text-right">{formatPrice(candle.open_price)}</td>
                              <td className="py-1 text-right">{formatPrice(candle.high_price)}</td>
                              <td className="py-1 text-right">{formatPrice(candle.low_price)}</td>
                              <td className="py-1 text-right">{formatPrice(candle.close_price)}</td>
                              <td className="py-1 text-right">{candle.volume?.toLocaleString()}</td>
                              <td className="py-1 text-right">{candle.tick_count}</td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  ) : (
                    <div className="text-sm text-gray-500">No candle data available</div>
                  )}
                </div>
              ))}
            </div>
          ) : (
            <div className="text-center text-gray-500">
              No candle data available. Select instruments and start data collection.
            </div>
          )}
        </div>
      </div>

      {/* Error Display */}
      {collectionStatus?.recent_errors && collectionStatus.recent_errors.length > 0 && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-4">
          <h3 className="text-red-800 font-medium mb-2">Recent Errors</h3>
          <div className="space-y-1">
            {collectionStatus.recent_errors.map((error, idx) => (
              <div key={idx} className="text-sm text-red-700">{error}</div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};