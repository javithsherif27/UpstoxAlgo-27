import React from 'react';
import { TVChart } from './TVChart';
import { useLivePrices } from '../queries/useMarketData';

interface Instrument {
  instrumentKey: string;
  symbol: string;
  name: string;
}

interface TradingChartProps {
  instrument: Instrument;
}

export const TradingChart: React.FC<TradingChartProps> = ({ instrument }) => {
  const { data: livePrices } = useLivePrices();
  const priceData = livePrices?.prices?.[instrument.instrumentKey];

  const formatPrice = (price: number) => {
    return price?.toFixed(2) || '0.00';
  };

  const getChangeColor = (change: number) => {
    if (change > 0) return 'text-green-600';
    if (change < 0) return 'text-red-600';
    return 'text-gray-600';
  };

  return (
    <div className="flex flex-col h-full bg-white">
      {/* Chart Header */}
      <div className="px-4 py-3 border-b border-gray-200 bg-white">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-4">
            <div>
              <h3 className="text-lg font-semibold text-gray-900">{instrument.symbol}</h3>
              <p className="text-sm text-gray-600">{instrument.name}</p>
            </div>
            
            {priceData && (
              <div className="flex items-center space-x-6 text-sm">
                <div className="flex items-center space-x-2">
                  <span className="text-gray-500">LTP:</span>
                  <span className="font-semibold text-lg">₹{formatPrice(priceData.ltp)}</span>
                </div>
                
                <div className={`flex items-center space-x-1 ${getChangeColor(priceData.change || 0)}`}>
                  <span>{priceData.change > 0 ? '▲' : priceData.change < 0 ? '▼' : '●'}</span>
                  <span className="font-medium">
                    {Math.abs(priceData.change || 0).toFixed(2)} ({priceData.change_percent?.toFixed(2)}%)
                  </span>
                </div>
              </div>
            )}
          </div>

          {/* Chart Controls */}
          <div className="flex items-center space-x-2">
            <div className="flex bg-gray-100 rounded-md p-1">
              <button className="px-3 py-1 text-sm bg-white rounded shadow-sm font-medium">1D</button>
              <button className="px-3 py-1 text-sm text-gray-600 hover:bg-gray-50 rounded font-medium">5D</button>
              <button className="px-3 py-1 text-sm text-gray-600 hover:bg-gray-50 rounded font-medium">1M</button>
              <button className="px-3 py-1 text-sm text-gray-600 hover:bg-gray-50 rounded font-medium">3M</button>
            </div>
          </div>
        </div>

        {/* Market Info Bar */}
        {priceData && (
          <div className="mt-3 grid grid-cols-6 gap-4 text-sm">
            <div>
              <span className="text-gray-500">Open:</span>
              <span className="ml-1 font-medium">₹{formatPrice(priceData.open)}</span>
            </div>
            <div>
              <span className="text-gray-500">High:</span>
              <span className="ml-1 font-medium text-green-600">₹{formatPrice(priceData.high)}</span>
            </div>
            <div>
              <span className="text-gray-500">Low:</span>
              <span className="ml-1 font-medium text-red-600">₹{formatPrice(priceData.low)}</span>
            </div>
            <div>
              <span className="text-gray-500">Volume:</span>
              <span className="ml-1 font-medium">{(priceData.volume || 0).toLocaleString()}</span>
            </div>
            <div>
              <span className="text-gray-500">Prev Close:</span>
              <span className="ml-1 font-medium">₹{formatPrice((priceData.ltp || 0) - (priceData.change || 0))}</span>
            </div>
            <div>
              <span className="text-gray-500">Market Cap:</span>
              <span className="ml-1 font-medium">N/A</span>
            </div>
          </div>
        )}
      </div>

      {/* Chart Area */}
      <div className="flex-1 p-4">
        <div className="h-full w-full">
          <TVChart 
            symbol={instrument.symbol}
            instrumentKey={instrument.instrumentKey}
            height={window.innerHeight - 200} // Adjust height based on header
          />
        </div>
      </div>

      {/* Bottom Panel - Order Entry (Optional) */}
      <div className="border-t border-gray-200 bg-gray-50 p-4">
        <div className="grid grid-cols-2 gap-4">
          {/* Buy Panel */}
          <div className="bg-white border border-gray-200 rounded-lg p-4">
            <h4 className="text-sm font-semibold text-gray-700 mb-3">Buy Order</h4>
            <div className="space-y-3">
              <div className="flex space-x-2">
                <input
                  type="number"
                  placeholder="Quantity"
                  onChange={() => {}} // Empty handler for demo purposes
                  className="flex-1 px-3 py-2 text-sm border border-gray-300 rounded focus:ring-2 focus:ring-green-500 focus:border-green-500"
                />
                <input
                  type="number"
                  placeholder="Price"
                  value={priceData?.ltp || ''}
                  onChange={() => {}} // Empty handler for demo purposes
                  className="flex-1 px-3 py-2 text-sm border border-gray-300 rounded focus:ring-2 focus:ring-green-500 focus:border-green-500"
                />
              </div>
              <button className="w-full bg-green-500 text-white py-2 px-4 rounded font-medium hover:bg-green-600 transition-colors">
                Buy
              </button>
            </div>
          </div>

          {/* Sell Panel */}
          <div className="bg-white border border-gray-200 rounded-lg p-4">
            <h4 className="text-sm font-semibold text-gray-700 mb-3">Sell Order</h4>
            <div className="space-y-3">
              <div className="flex space-x-2">
                <input
                  type="number"
                  placeholder="Quantity"
                  onChange={() => {}} // Empty handler for demo purposes
                  className="flex-1 px-3 py-2 text-sm border border-gray-300 rounded focus:ring-2 focus:ring-red-500 focus:border-red-500"
                />
                <input
                  type="number"
                  placeholder="Price"
                  value={priceData?.ltp || ''}
                  onChange={() => {}} // Empty handler for demo purposes
                  className="flex-1 px-3 py-2 text-sm border border-gray-300 rounded focus:ring-2 focus:ring-red-500 focus:border-red-500"
                />
              </div>
              <button className="w-full bg-red-500 text-white py-2 px-4 rounded font-medium hover:bg-red-600 transition-colors">
                Sell
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};