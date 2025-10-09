import React from 'react';
import { useLivePrices, useLivePriceStream } from '../queries/useMarketData';

interface Instrument {
  instrumentKey: string;
  symbol: string;
  name: string;
}

interface WatchlistProps {
  instruments: Instrument[];
  selectedInstrument: Instrument | null;
  onSelectInstrument: (instrument: Instrument) => void;
  onRemoveInstrument: (instrumentKey: string) => void;
}

export const Watchlist: React.FC<WatchlistProps> = ({
  instruments,
  selectedInstrument,
  onSelectInstrument,
  onRemoveInstrument,
}) => {
  // Start live price stream merging into cache
  useLivePriceStream();
  const { data: livePrices, isLoading } = useLivePrices();

  const formatPrice = (price: number) => {
    return price?.toFixed(2) || '0.00';
  };

  const getChangeColor = (change: number) => {
    if (change > 0) return 'text-green-600';
    if (change < 0) return 'text-red-600';
    return 'text-gray-600';
  };

  const getChangeIcon = (change: number) => {
    if (change > 0) return '▲';
    if (change < 0) return '▼';
    return '●';
  };

  return (
    <div className="flex flex-col h-full">
      {/* Header */}
      <div className="px-3 py-2 bg-gray-50 border-b border-gray-200">
        <div className="grid grid-cols-12 text-xs font-medium text-gray-600 uppercase tracking-wide">
          <div className="col-span-4">Symbol</div>
          <div className="col-span-3 text-right">LTP</div>
          <div className="col-span-4 text-right">Change</div>
          <div className="col-span-1"></div>
        </div>
      </div>

      {/* Instruments List */}
      <div className="flex-1 overflow-y-auto">
        {instruments.map((instrument) => {
          const priceData = livePrices?.prices?.[instrument.instrumentKey];
          const isSelected = selectedInstrument?.instrumentKey === instrument.instrumentKey;
          const change = priceData?.change || 0;
          const changePercent = priceData?.change_percent || 0;

          return (
            <div
              key={instrument.instrumentKey}
              className={`px-3 py-3 border-b border-gray-100 cursor-pointer hover:bg-gray-50 transition-colors ${
                isSelected ? 'bg-blue-50 border-blue-200' : ''
              }`}
              onClick={() => onSelectInstrument(instrument)}
            >
              <div className="grid grid-cols-12 items-center">
                {/* Symbol */}
                <div className="col-span-4">
                  <div className="font-medium text-gray-900">{instrument.symbol}</div>
                  <div className="text-xs text-gray-500 truncate">{instrument.name}</div>
                </div>

                {/* LTP */}
                <div className="col-span-3 text-right">
                  <div className="font-medium">
                    {isLoading ? (
                      <div className="h-4 bg-gray-200 rounded animate-pulse"></div>
                    ) : (
                      `₹${formatPrice(priceData?.ltp)}`
                    )}
                  </div>
                </div>

                {/* Change */}
                <div className="col-span-4 text-right">
                  {isLoading ? (
                    <div className="space-y-1">
                      <div className="h-3 bg-gray-200 rounded animate-pulse"></div>
                      <div className="h-3 bg-gray-200 rounded animate-pulse"></div>
                    </div>
                  ) : (
                    <div className={`text-sm ${getChangeColor(change)}`}>
                      <div className="flex items-center justify-end">
                        <span className="mr-1">{getChangeIcon(change)}</span>
                        <span>{Math.abs(change).toFixed(2)}</span>
                      </div>
                      <div className="text-xs">
                        ({changePercent > 0 ? '+' : ''}{changePercent.toFixed(2)}%)
                      </div>
                    </div>
                  )}
                </div>

                {/* Remove Button */}
                <div className="col-span-1 text-right">
                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      onRemoveInstrument(instrument.instrumentKey);
                    }}
                    className="text-gray-400 hover:text-red-500 text-xs p-1"
                    title="Remove from watchlist"
                  >
                    ✕
                  </button>
                </div>
              </div>

              {/* Additional Info Row */}
              {priceData && (
                <div className="mt-2 grid grid-cols-4 text-xs text-gray-500">
                  <div>O: {formatPrice(priceData.open)}</div>
                  <div>H: {formatPrice(priceData.high)}</div>
                  <div>L: {formatPrice(priceData.low)}</div>
                  <div>Vol: {(priceData.volume || 0).toLocaleString()}</div>
                </div>
              )}
            </div>
          );
        })}
      </div>

      {/* Footer */}
      {instruments.length === 0 && (
        <div className="p-4 text-center text-gray-500">
          <div className="text-2xl mb-2">📋</div>
          <div className="text-sm">Your watchlist is empty</div>
          <div className="text-xs mt-1">Search and add instruments to track them</div>
        </div>
      )}
    </div>
  );
};