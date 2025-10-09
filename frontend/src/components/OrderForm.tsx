import React, { useState, useEffect } from 'react';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { useSelectedInstruments } from '../hooks/useSelectedInstruments';
import { toast } from '../utils/toast';
import InstrumentDebug from './InstrumentDebug';

interface OrderFormData {
  instrument_key: string;
  symbol: string;
  quantity: number;
  price?: number;
  order_type: 'MARKET' | 'LIMIT' | 'SL' | 'SL-M';
  order_side: 'BUY' | 'SELL';
  product_type: 'D' | 'I' | 'CNC' | 'M';
  validity: 'DAY' | 'IOC' | 'GTT';
  trigger_price?: number;
  disclosed_quantity?: number;
  tag?: string;
}

interface OrderFormProps {
  selectedInstrument?: {
    instrument_key: string;
    symbol: string;
    last_price?: number;
  };
  onClose?: () => void;
}

const OrderForm: React.FC<OrderFormProps> = ({ selectedInstrument, onClose }) => {
  const queryClient = useQueryClient();
  const { data: selectedInstruments = [], isLoading: loadingInstruments, error: instrumentsError } = useSelectedInstruments();
  
  const [formData, setFormData] = useState<OrderFormData>({
    instrument_key: selectedInstrument?.instrument_key || (selectedInstruments.length > 0 ? selectedInstruments[0].instrument_key : ''),
    symbol: selectedInstrument?.symbol || (selectedInstruments.length > 0 ? selectedInstruments[0].symbol : ''),
    quantity: 1,
    price: selectedInstrument?.last_price || 0,
    order_type: 'MARKET',
    order_side: 'BUY',
    product_type: 'D',
    validity: 'DAY'
  });

  const [errors, setErrors] = useState<Partial<OrderFormData>>({});

  // Update form when selected instruments change
  useEffect(() => {
    if (!formData.instrument_key && selectedInstruments.length > 0) {
      setFormData(prev => ({
        ...prev,
        instrument_key: selectedInstruments[0].instrument_key,
        symbol: selectedInstruments[0].symbol
      }));
    }
  }, [selectedInstruments, formData.instrument_key]);

  const placeOrderMutation = useMutation({
    mutationFn: async (orderData: OrderFormData) => {
      // Use the correct backend URL
      const backendUrl = import.meta.env.VITE_API_URL || 'http://localhost:8000';
      const response = await fetch(`${backendUrl}/api/orders/place`, {
        method: 'POST',
        credentials: 'include', // Include cookies for authentication
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(orderData),
      });
      
      if (!response.ok) {
        let errorMessage = 'Failed to place order';
        try {
          const errorData = await response.json();
          errorMessage = errorData.detail || errorMessage;
        } catch {
          errorMessage = `HTTP ${response.status}: ${response.statusText}`;
        }
        throw new Error(errorMessage);
      }
      
      const result = await response.json();
      return result;
    },
    onSuccess: (data) => {
      toast.success(`Order placed successfully! Order ID: ${data.order_id}`);
      queryClient.invalidateQueries({ queryKey: ['orderBook'] });
      queryClient.invalidateQueries({ queryKey: ['orders'] });
      setFormData({
        ...formData,
        quantity: 1,
        tag: ''
      });
      onClose?.();
    },
    onError: (error: Error) => {
      toast.error(`Failed to place order: ${error.message}`);
    }
  });

  const validateForm = (): boolean => {
    const newErrors: Partial<OrderFormData> = {};

    if (!formData.instrument_key) {
      newErrors.instrument_key = 'Instrument is required';
    }
    if (!formData.symbol) {
      newErrors.symbol = 'Symbol is required';
    }
    if (formData.quantity <= 0) {
      newErrors.quantity = 'Quantity must be greater than 0';
    }
    if (formData.order_type === 'LIMIT' && (!formData.price || formData.price <= 0)) {
      newErrors.price = 'Price is required for limit orders';
    }
    if ((formData.order_type === 'SL' || formData.order_type === 'SL-M') && 
        (!formData.trigger_price || formData.trigger_price <= 0)) {
      newErrors.trigger_price = 'Trigger price is required for stop loss orders';
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (validateForm()) {
      placeOrderMutation.mutate(formData);
    }
  };

  const handleInputChange = (field: keyof OrderFormData, value: any) => {
    setFormData(prev => ({ ...prev, [field]: value }));
    // Clear related errors
    if (errors[field]) {
      setErrors(prev => ({ ...prev, [field]: undefined }));
    }
    // Clear symbol error when instrument_key is selected
    if (field === 'instrument_key' && errors.symbol) {
      setErrors(prev => ({ ...prev, symbol: undefined }));
    }
  };

  const getOrderValue = () => {
    const price = formData.order_type === 'MARKET' ? (selectedInstrument?.last_price || 0) : (formData.price || 0);
    return formData.quantity * price;
  };

  return (
    <>
      <InstrumentDebug />
      <div className="bg-white rounded-lg shadow-lg p-6 w-full max-w-md">
        <div className="flex justify-between items-center mb-6">
          <h2 className="text-xl font-bold text-gray-900">Place Order</h2>
        {onClose && (
          <button
            onClick={onClose}
            className="text-gray-500 hover:text-gray-700"
          >
            <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        )}
      </div>

      <form onSubmit={handleSubmit} className="space-y-4">
        {/* Instrument Selection */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Select Instrument
          </label>
          {loadingInstruments ? (
            <div className="w-full p-2 border rounded-md border-gray-300 bg-gray-50 text-gray-500 text-center">
              Loading instruments...
            </div>
          ) : instrumentsError ? (
            <div className="w-full p-2 border rounded-md border-red-300 bg-red-50 text-red-600 text-center text-sm">
              Error loading instruments: {instrumentsError.message}
            </div>
          ) : selectedInstruments.length > 0 ? (
            <select
              value={formData.instrument_key}
              onChange={(e) => {
                const selectedInst = selectedInstruments.find(inst => inst.instrument_key === e.target.value);
                if (selectedInst) {
                  handleInputChange('instrument_key', selectedInst.instrument_key);
                  handleInputChange('symbol', selectedInst.symbol);
                }
              }}
              className={`w-full p-2 border rounded-md ${errors.instrument_key ? 'border-red-500' : 'border-gray-300'}`}
            >
              <option value="">Select an instrument</option>
              {selectedInstruments.map((instrument) => (
                <option key={instrument.instrument_key} value={instrument.instrument_key}>
                  {instrument.symbol} - {instrument.name} ({instrument.exchange})
                </option>
              ))}
            </select>
          ) : (
            <div className="w-full p-2 border rounded-md border-gray-300 bg-gray-50 text-gray-500 text-center">
              No instruments selected. Please select instruments from the Instruments page first.
            </div>
          )}
          {errors.instrument_key && <p className="text-red-500 text-sm mt-1">{errors.instrument_key}</p>}
        </div>

        {/* Order Side */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Order Side
          </label>
          <div className="grid grid-cols-2 gap-2">
            <button
              type="button"
              onClick={() => handleInputChange('order_side', 'BUY')}
              className={`p-2 rounded-md font-medium ${
                formData.order_side === 'BUY'
                  ? 'bg-green-600 text-white'
                  : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
              }`}
            >
              BUY
            </button>
            <button
              type="button"
              onClick={() => handleInputChange('order_side', 'SELL')}
              className={`p-2 rounded-md font-medium ${
                formData.order_side === 'SELL'
                  ? 'bg-red-600 text-white'
                  : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
              }`}
            >
              SELL
            </button>
          </div>
        </div>

        {/* Quantity */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Quantity
          </label>
          <input
            type="number"
            min="1"
            value={formData.quantity}
            onChange={(e) => handleInputChange('quantity', parseInt(e.target.value))}
            className={`w-full p-2 border rounded-md ${errors.quantity ? 'border-red-500' : 'border-gray-300'}`}
          />
          {errors.quantity && <p className="text-red-500 text-sm mt-1">{errors.quantity}</p>}
        </div>

        {/* Order Type */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Order Type
          </label>
          <select
            value={formData.order_type}
            onChange={(e) => handleInputChange('order_type', e.target.value)}
            className="w-full p-2 border border-gray-300 rounded-md"
          >
            <option value="MARKET">Market</option>
            <option value="LIMIT">Limit</option>
            <option value="SL">Stop Loss</option>
            <option value="SL-M">Stop Loss Market</option>
          </select>
        </div>

        {/* Price (for LIMIT orders) */}
        {formData.order_type === 'LIMIT' && (
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Price
            </label>
            <input
              type="number"
              step="0.01"
              min="0"
              value={formData.price || ''}
              onChange={(e) => handleInputChange('price', parseFloat(e.target.value))}
              className={`w-full p-2 border rounded-md ${errors.price ? 'border-red-500' : 'border-gray-300'}`}
            />
            {errors.price && <p className="text-red-500 text-sm mt-1">{errors.price}</p>}
          </div>
        )}

        {/* Trigger Price (for SL orders) */}
        {(formData.order_type === 'SL' || formData.order_type === 'SL-M') && (
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Trigger Price
            </label>
            <input
              type="number"
              step="0.01"
              min="0"
              value={formData.trigger_price || ''}
              onChange={(e) => handleInputChange('trigger_price', parseFloat(e.target.value))}
              className={`w-full p-2 border rounded-md ${errors.trigger_price ? 'border-red-500' : 'border-gray-300'}`}
            />
            {errors.trigger_price && <p className="text-red-500 text-sm mt-1">{errors.trigger_price}</p>}
          </div>
        )}

        {/* Product Type */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Product Type
          </label>
          <select
            value={formData.product_type}
            onChange={(e) => handleInputChange('product_type', e.target.value)}
            className="w-full p-2 border border-gray-300 rounded-md"
          >
            <option value="D">Delivery</option>
            <option value="I">Intraday</option>
            <option value="CNC">Cash & Carry</option>
            <option value="M">Margin</option>
          </select>
        </div>

        {/* Validity */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Validity
          </label>
          <select
            value={formData.validity}
            onChange={(e) => handleInputChange('validity', e.target.value)}
            className="w-full p-2 border border-gray-300 rounded-md"
          >
            <option value="DAY">Day</option>
            <option value="IOC">IOC</option>
            <option value="GTT">GTT</option>
          </select>
        </div>

        {/* Order Value */}
        <div className="bg-gray-50 p-3 rounded-md">
          <div className="flex justify-between items-center">
            <span className="font-medium text-gray-700">Order Value:</span>
            <span className="font-bold text-lg">
              ₹{getOrderValue().toFixed(2)}
            </span>
          </div>
        </div>

        {/* Submit Button */}
        <button
          type="submit"
          disabled={placeOrderMutation.isPending}
          className={`w-full p-3 rounded-md font-medium ${
            formData.order_side === 'BUY'
              ? 'bg-green-600 hover:bg-green-700 text-white'
              : 'bg-red-600 hover:bg-red-700 text-white'
          } disabled:opacity-50 disabled:cursor-not-allowed`}
        >
          {placeOrderMutation.isPending 
            ? 'Placing Order...' 
            : `${formData.order_side} ${formData.symbol}`
          }
        </button>
      </form>
    </div>
    </>
  );
};

export default OrderForm;