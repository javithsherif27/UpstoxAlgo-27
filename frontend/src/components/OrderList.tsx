import React, { useState, useEffect } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { toast } from '../utils/toast';

interface Order {
  order_id: string;
  exchange_order_id?: string;
  instrument_key: string;
  symbol: string;
  product_type: string;
  order_type: string;
  order_side: string;
  validity: string;
  quantity: number;
  filled_quantity: number;
  pending_quantity: number;
  price?: number;
  trigger_price?: number;
  average_price?: number;
  status: string;
  status_message?: string;
  order_timestamp: string;
  exchange_timestamp?: string;
  tag?: string;
}

interface OrderBook {
  orders: Order[];
  total_orders: number;
  pending_orders: number;
  completed_orders: number;
  cancelled_orders: number;
  total_buy_value: number;
  total_sell_value: number;
}

interface OrderListProps {
  refreshInterval?: number;
}

const OrderList: React.FC<OrderListProps> = ({ refreshInterval = 5000 }) => {
  const [filter, setFilter] = useState<{
    status: string;
    symbol: string;
    side: string;
  }>({
    status: '',
    symbol: '',
    side: ''
  });

  const queryClient = useQueryClient();

  const { data: orderBook, isLoading, error, refetch } = useQuery<OrderBook>({
    queryKey: ['orderBook', filter],
    queryFn: async () => {
      const params = new URLSearchParams();
      if (filter.status) params.append('status', filter.status);
      if (filter.symbol) params.append('symbol', filter.symbol);
      
      const backendUrl = import.meta.env.VITE_API_URL || 'http://localhost:8000';
      const response = await fetch(`${backendUrl}/api/orders/book?${params.toString()}`, {
        method: 'GET',
        credentials: 'include', // Include cookies for authentication
        headers: {
          'Content-Type': 'application/json',
        },
      });
      if (!response.ok) {
        throw new Error('Failed to fetch order book');
      }
      return response.json();
    },
    refetchInterval: refreshInterval,
    refetchOnWindowFocus: false,
  });

  const cancelOrderMutation = useMutation({
    mutationFn: async (orderId: string) => {
      const backendUrl = import.meta.env.VITE_API_URL || 'http://localhost:8000';
      const response = await fetch(`${backendUrl}/api/orders/cancel`, {
        method: 'DELETE',
        credentials: 'include', // Include cookies for authentication
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ order_id: orderId }),
      });
      
      if (!response.ok) {
        let errorMessage = 'Failed to cancel order';
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
    onSuccess: (data, orderId) => {
      toast.success(`Order ${orderId} cancelled successfully`);
      queryClient.invalidateQueries({ queryKey: ['orderBook'] });
    },
    onError: (error: Error) => {
      toast.error(`Failed to cancel order: ${error.message}`);
    }
  });

  const getStatusColor = (status: string) => {
    switch (status.toUpperCase()) {
      case 'COMPLETE':
        return 'bg-green-100 text-green-800';
      case 'PENDING':
      case 'OPEN':
        return 'bg-yellow-100 text-yellow-800';
      case 'CANCELLED':
        return 'bg-red-100 text-red-800';
      case 'REJECTED':
        return 'bg-red-100 text-red-800';
      default:
        return 'bg-gray-100 text-gray-800';
    }
  };

  const getSideColor = (side: string) => {
    return side === 'BUY' ? 'text-green-600' : 'text-red-600';
  };

  const formatDateTime = (dateString: string) => {
    return new Date(dateString).toLocaleString('en-IN', {
      day: '2-digit',
      month: 'short',
      hour: '2-digit',
      minute: '2-digit',
    });
  };

  const canCancelOrder = (order: Order) => {
    return ['PENDING', 'OPEN'].includes(order.status.toUpperCase()) && order.pending_quantity > 0;
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center p-8">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
        <span className="ml-2">Loading orders...</span>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-red-50 p-4 rounded-md">
        <p className="text-red-700">Failed to load orders. Please try again.</p>
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
      {/* Order Summary */}
      {orderBook && (
        <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
          <div className="bg-blue-50 p-3 rounded-lg">
            <div className="text-2xl font-bold text-blue-600">{orderBook.total_orders}</div>
            <div className="text-sm text-blue-600">Total Orders</div>
          </div>
          <div className="bg-yellow-50 p-3 rounded-lg">
            <div className="text-2xl font-bold text-yellow-600">{orderBook.pending_orders}</div>
            <div className="text-sm text-yellow-600">Pending</div>
          </div>
          <div className="bg-green-50 p-3 rounded-lg">
            <div className="text-2xl font-bold text-green-600">{orderBook.completed_orders}</div>
            <div className="text-sm text-green-600">Completed</div>
          </div>
          <div className="bg-red-50 p-3 rounded-lg">
            <div className="text-2xl font-bold text-red-600">{orderBook.cancelled_orders}</div>
            <div className="text-sm text-red-600">Cancelled</div>
          </div>
          <div className="bg-purple-50 p-3 rounded-lg">
            <div className="text-2xl font-bold text-purple-600">
              ₹{(orderBook.total_buy_value + orderBook.total_sell_value).toFixed(0)}
            </div>
            <div className="text-sm text-purple-600">Total Value</div>
          </div>
        </div>
      )}

      {/* Filters */}
      <div className="bg-white p-4 rounded-lg shadow-sm border">
        <h3 className="text-lg font-medium mb-3">Filters</h3>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Status</label>
            <select
              value={filter.status}
              onChange={(e) => setFilter(prev => ({ ...prev, status: e.target.value }))}
              className="w-full p-2 border border-gray-300 rounded-md"
            >
              <option value="">All Status</option>
              <option value="PENDING">Pending</option>
              <option value="OPEN">Open</option>
              <option value="COMPLETE">Complete</option>
              <option value="CANCELLED">Cancelled</option>
              <option value="REJECTED">Rejected</option>
            </select>
          </div>
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
        </div>
        <div className="mt-3 flex gap-2">
          <button
            onClick={() => setFilter({ status: '', symbol: '', side: '' })}
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

      {/* Orders List */}
      <div className="bg-white rounded-lg shadow-sm border">
        <div className="px-4 py-3 border-b">
          <h3 className="text-lg font-medium">Orders</h3>
        </div>
        
        {!orderBook?.orders?.length ? (
          <div className="p-8 text-center text-gray-500">
            <svg className="w-12 h-12 mx-auto mb-4 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5H7a2 2 0 00-2 2v10a2 2 0 002 2h8a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2" />
            </svg>
            <p>No orders found</p>
            <p className="text-sm">Your orders will appear here once placed</p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Symbol</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Side</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Type</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Quantity</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Price</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Status</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Time</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-200">
                {orderBook.orders.map((order) => (
                  <tr key={order.order_id} className="hover:bg-gray-50">
                    <td className="px-4 py-3">
                      <div>
                        <div className="font-medium text-gray-900">{order.symbol}</div>
                        <div className="text-sm text-gray-500">{order.product_type}</div>
                      </div>
                    </td>
                    <td className="px-4 py-3">
                      <span className={`font-medium ${getSideColor(order.order_side)}`}>
                        {order.order_side}
                      </span>
                    </td>
                    <td className="px-4 py-3 text-sm text-gray-900">{order.order_type}</td>
                    <td className="px-4 py-3">
                      <div className="text-sm">
                        <div>{order.filled_quantity}/{order.quantity}</div>
                        {order.pending_quantity > 0 && (
                          <div className="text-xs text-gray-500">
                            {order.pending_quantity} pending
                          </div>
                        )}
                      </div>
                    </td>
                    <td className="px-4 py-3">
                      <div className="text-sm">
                        {order.price && <div>₹{order.price.toFixed(2)}</div>}
                        {order.average_price && (
                          <div className="text-xs text-gray-500">
                            Avg: ₹{order.average_price.toFixed(2)}
                          </div>
                        )}
                        {order.trigger_price && (
                          <div className="text-xs text-gray-500">
                            Trigger: ₹{order.trigger_price.toFixed(2)}
                          </div>
                        )}
                      </div>
                    </td>
                    <td className="px-4 py-3">
                      <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${getStatusColor(order.status)}`}>
                        {order.status}
                      </span>
                    </td>
                    <td className="px-4 py-3 text-sm text-gray-900">
                      {formatDateTime(order.order_timestamp)}
                    </td>
                    <td className="px-4 py-3">
                      <div className="flex space-x-2">
                        {canCancelOrder(order) && (
                          <button
                            onClick={() => cancelOrderMutation.mutate(order.order_id)}
                            disabled={cancelOrderMutation.isPending}
                            className="text-red-600 hover:text-red-800 disabled:opacity-50 text-sm"
                          >
                            Cancel
                          </button>
                        )}
                        <button className="text-blue-600 hover:text-blue-800 text-sm">
                          Details
                        </button>
                      </div>
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

export default OrderList;