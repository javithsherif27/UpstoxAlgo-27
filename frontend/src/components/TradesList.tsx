import React, { useState } from 'react';
import { useQuery } from '@tanstack/react-query';

interface Trade {
  trade_id: string;
  order_id: string;
  exchange_order_id?: string;
  instrument_key: string;
  symbol: string;
  trade_price: number;
  trade_quantity: number;
  trade_timestamp: string;
  exchange: string;
  order_side: string;
}

interface TradesListProps {
  refreshInterval?: number;
}

const TradesList: React.FC<TradesListProps> = ({ refreshInterval = 5000 }) => {
  const [filter, setFilter] = useState<{
    symbol: string;
    side: string;
    days: number;
  }>({
    symbol: '',
    side: '',
    days: 7
  });

  const { data: trades, isLoading, error, refetch } = useQuery<Trade[]>({
    queryKey: ['trades', filter],
    queryFn: async () => {
      const params = new URLSearchParams();
      if (filter.symbol) params.append('symbol', filter.symbol);
      if (filter.days) params.append('days', filter.days.toString());
      
      const backendUrl = import.meta.env.VITE_API_URL || 'http://localhost:8000';
      const response = await fetch(`${backendUrl}/api/orders/trades?${params.toString()}`, {
        method: 'GET',
        credentials: 'include', // Include cookies for authentication
        headers: {
          'Content-Type': 'application/json',
        },
      });
      if (!response.ok) {
        let errorMessage = 'Failed to fetch trades';
        try {
          const errorText = await response.text();
          if (errorText) {
            const errorData = JSON.parse(errorText);
            errorMessage = errorData.detail || errorMessage;
          }
        } catch {
          errorMessage = `HTTP ${response.status}: ${response.statusText}`;
        }
        throw new Error(errorMessage);
      }
      return response.json();
    },
    refetchInterval: refreshInterval,
    refetchOnWindowFocus: false,
  });

  const getSideColor = (side: string) => {
    return side === 'BUY' ? 'text-green-600' : 'text-red-600';
  };

  const formatDateTime = (dateString: string) => {
    return new Date(dateString).toLocaleString('en-IN', {
      day: '2-digit',
      month: 'short',
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit'
    });
  };

  const calculateTotals = () => {
    if (!trades?.length) return { totalValue: 0, totalQuantity: 0, avgPrice: 0 };
    
    const totalValue = trades.reduce((sum, trade) => sum + (trade.trade_price * trade.trade_quantity), 0);
    const totalQuantity = trades.reduce((sum, trade) => sum + trade.trade_quantity, 0);
    const avgPrice = totalQuantity > 0 ? totalValue / totalQuantity : 0;
    
    return { totalValue, totalQuantity, avgPrice };
  };

  const totals = calculateTotals();

  if (isLoading) {
    return (
      <div className="flex items-center justify-center p-8">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
        <span className="ml-2">Loading trades...</span>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-red-50 p-4 rounded-md">
        <p className="text-red-700">Failed to load trades. Please try again.</p>
        <button 
          onClick={() => refetch()}
          className="mt-2 px-3 py-1 bg-red-600 text-white rounded hover:bg-red-700"
        >
          Retry
        </button>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Trade Summary */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div className="bg-blue-50 p-3 rounded-lg">
          <div className="text-2xl font-bold text-blue-600">{trades?.length || 0}</div>
          <div className="text-sm text-blue-600">Total Trades</div>
        </div>
        <div className="bg-green-50 p-3 rounded-lg">
          <div className="text-2xl font-bold text-green-600">₹{totals.totalValue.toFixed(0)}</div>
          <div className="text-sm text-green-600">Total Value</div>
        </div>
        <div className="bg-purple-50 p-3 rounded-lg">
          <div className="text-2xl font-bold text-purple-600">{totals.totalQuantity}</div>
          <div className="text-sm text-purple-600">Total Quantity</div>
        </div>
        <div className="bg-orange-50 p-3 rounded-lg">
          <div className="text-2xl font-bold text-orange-600">₹{totals.avgPrice.toFixed(2)}</div>
          <div className="text-sm text-orange-600">Avg Price</div>
        </div>
      </div>

      {/* Filters */}
      <div className="bg-white p-4 rounded-lg shadow-sm border">
        <h3 className="text-lg font-medium mb-3">Filters</h3>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Symbol</label>
            <input
              type="text"
              value={filter.symbol}
              onChange={(e) => setFilter(prev => ({ ...prev, symbol: e.target.value }))}
              placeholder="Enter symbol"
              className="w-full p-2 border border-gray-300 rounded-md"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Side</label>
            <select
              value={filter.side}
              onChange={(e) => setFilter(prev => ({ ...prev, side: e.target.value }))}
              className="w-full p-2 border border-gray-300 rounded-md"
            >
              <option value="">All Sides</option>
              <option value="BUY">Buy</option>
              <option value="SELL">Sell</option>
            </select>
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Period</label>
            <select
              value={filter.days}
              onChange={(e) => setFilter(prev => ({ ...prev, days: parseInt(e.target.value) }))}
              className="w-full p-2 border border-gray-300 rounded-md"
            >
              <option value={1}>Today</option>
              <option value={7}>Last 7 days</option>
              <option value={30}>Last 30 days</option>
              <option value={90}>Last 3 months</option>
            </select>
          </div>
        </div>
        <div className="mt-3 flex gap-2">
          <button
            onClick={() => setFilter({ symbol: '', side: '', days: 7 })}
            className="px-3 py-1 text-sm bg-gray-500 text-white rounded hover:bg-gray-600"
          >
            Clear Filters
          </button>
          <button
            onClick={() => refetch()}
            className="px-3 py-1 text-sm bg-blue-500 text-white rounded hover:bg-blue-600"
          >
            Refresh
          </button>
        </div>
      </div>

      {/* Trades List */}
      <div className="bg-white rounded-lg shadow-sm border">
        <div className="px-4 py-3 border-b">
          <h3 className="text-lg font-medium">Executed Trades</h3>
        </div>
        
        {!trades?.length ? (
          <div className="p-8 text-center text-gray-500">
            <svg className="w-12 h-12 mx-auto mb-4 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 7h8m0 0v8m0-8l-8 8-4-4-6 6" />
            </svg>
            <p>No trades found</p>
            <p className="text-sm">Your executed trades will appear here</p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Trade ID</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Symbol</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Side</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Quantity</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Price</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Value</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Exchange</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Time</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-200">
                {trades.map((trade) => (
                  <tr key={trade.trade_id} className="hover:bg-gray-50">
                    <td className="px-4 py-3">
                      <div className="text-sm font-mono text-gray-900">
                        {trade.trade_id.slice(-8)}
                      </div>
                    </td>
                    <td className="px-4 py-3">
                      <div className="font-medium text-gray-900">{trade.symbol}</div>
                    </td>
                    <td className="px-4 py-3">
                      <span className={`font-medium ${getSideColor(trade.order_side)}`}>
                        {trade.order_side}
                      </span>
                    </td>
                    <td className="px-4 py-3 text-sm text-gray-900">
                      {trade.trade_quantity.toLocaleString()}
                    </td>
                    <td className="px-4 py-3 text-sm text-gray-900">
                      ₹{trade.trade_price.toFixed(2)}
                    </td>
                    <td className="px-4 py-3 text-sm text-gray-900 font-medium">
                      ₹{(trade.trade_price * trade.trade_quantity).toFixed(2)}
                    </td>
                    <td className="px-4 py-3 text-sm text-gray-900">
                      {trade.exchange}
                    </td>
                    <td className="px-4 py-3 text-sm text-gray-900">
                      {formatDateTime(trade.trade_timestamp)}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
};

export default TradesList;