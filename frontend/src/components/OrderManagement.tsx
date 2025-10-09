import React, { useState } from 'react';
import OrderForm from './OrderForm';
import OrderList from './OrderList';
import TradesList from './TradesList';

interface OrderManagementProps {
  selectedInstrument?: {
    instrument_key: string;
    symbol: string;
    last_price?: number;
  };
}

type TabType = 'place-order' | 'orders' | 'trades';

const OrderManagement: React.FC<OrderManagementProps> = ({ selectedInstrument }) => {
  const [activeTab, setActiveTab] = useState<TabType>('place-order');
  const [showOrderForm, setShowOrderForm] = useState(false);

  const tabs = [
    {
      id: 'place-order' as TabType,
      label: 'Place Order',
      icon: (
        <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6v6m0 0v6m0-6h6m-6 0H6" />
        </svg>
      )
    },
    {
      id: 'orders' as TabType,
      label: 'Order Book',
      icon: (
        <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5H7a2 2 0 00-2 2v10a2 2 0 002 2h8a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2" />
        </svg>
      )
    },
    {
      id: 'trades' as TabType,
      label: 'Executed Trades',
      icon: (
        <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 7h8m0 0v8m0-8l-8 8-4-4-6 6" />
        </svg>
      )
    }
  ];

  const handleTabChange = (tabId: TabType) => {
    setActiveTab(tabId);
  };

  const renderTabContent = () => {
    switch (activeTab) {
      case 'place-order':
        return (
          <div className="flex justify-center">
            <OrderForm 
              selectedInstrument={selectedInstrument}
              onClose={() => setShowOrderForm(false)}
            />
          </div>
        );
      case 'orders':
        return <OrderList />;
      case 'trades':
        return <TradesList />;
      default:
        return null;
    }
  };

  return (
    <div className="bg-white rounded-lg shadow-lg">
      {/* Header */}
      <div className="px-6 py-4 border-b border-gray-200">
        <div className="flex items-center justify-between">
          <h2 className="text-xl font-bold text-gray-900">Order Management</h2>
          {selectedInstrument && (
            <div className="text-sm text-gray-600">
              Selected: <span className="font-medium">{selectedInstrument.symbol}</span>
              {selectedInstrument.last_price && (
                <span className="ml-2">₹{selectedInstrument.last_price.toFixed(2)}</span>
              )}
            </div>
          )}
        </div>
      </div>

      {/* Tabs */}
      <div className="border-b border-gray-200">
        <nav className="-mb-px flex space-x-8 px-6">
          {tabs.map((tab) => (
            <button
              key={tab.id}
              onClick={() => handleTabChange(tab.id)}
              className={`group inline-flex items-center space-x-2 py-4 px-1 border-b-2 font-medium text-sm ${
                activeTab === tab.id
                  ? 'border-blue-500 text-blue-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              }`}
            >
              <span className={activeTab === tab.id ? 'text-blue-500' : 'text-gray-400 group-hover:text-gray-500'}>
                {tab.icon}
              </span>
              <span>{tab.label}</span>
            </button>
          ))}
        </nav>
      </div>

      {/* Tab Content */}
      <div className="p-6">
        {renderTabContent()}
      </div>

      {/* Quick Actions Floating Button */}
      {activeTab !== 'place-order' && (
        <div className="fixed bottom-6 right-6">
          <button
            onClick={() => handleTabChange('place-order')}
            className="bg-blue-600 hover:bg-blue-700 text-white rounded-full p-3 shadow-lg transition-colors duration-200 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2"
            title="Place New Order"
          >
            <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6v6m0 0v6m0-6h6m-6 0H6" />
            </svg>
          </button>
        </div>
      )}

      {/* Order Form Modal for mobile/smaller screens */}
      {showOrderForm && activeTab !== 'place-order' && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
          <div className="bg-white rounded-lg max-w-md w-full max-h-[90vh] overflow-y-auto">
            <OrderForm 
              selectedInstrument={selectedInstrument}
              onClose={() => setShowOrderForm(false)}
            />
          </div>
        </div>
      )}
    </div>
  );
};

export default OrderManagement;