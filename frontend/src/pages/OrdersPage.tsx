import React from 'react';
import OrderManagement from '../components/OrderManagement';
import { useSelectedInstruments } from '../queries/useInstruments';

export const OrdersPage: React.FC = () => {
  const { data: selectedInstruments = [] } = useSelectedInstruments();
  
  // Get the first selected instrument as default for order form
  const selectedInstrument = selectedInstruments.length > 0 
    ? {
        instrument_key: selectedInstruments[0].instrument_key,
        symbol: selectedInstruments[0].symbol
      }
    : undefined;

  return (
    <div className="p-6">
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-gray-900">Orders & Trades</h1>
        <p className="text-gray-600 mt-1">
          Place orders, track executions, and manage your trading activity
        </p>
      </div>

      <OrderManagement selectedInstrument={selectedInstrument} />
    </div>
  );
};