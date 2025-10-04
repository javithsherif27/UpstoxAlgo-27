import React, { useState } from 'react';
import { useInstruments, useInstrumentCacheStatus, useRefreshInstruments, useSelectedInstruments, useSelectedInstrumentKeys, useSelectInstrument, useDeselectInstrument } from '../queries/useInstruments';
import { InstrumentDTO } from '../lib/types';

type TabType = 'master' | 'selected';

export const InstrumentsPage: React.FC = () => {
  const [activeTab, setActiveTab] = useState<TabType>('master');
  const [searchTerm, setSearchTerm] = useState('');
  const [debouncedSearch, setDebouncedSearch] = useState('');

  // Debounce search input
  React.useEffect(() => {
    const timer = setTimeout(() => {
      setDebouncedSearch(searchTerm);
    }, 300);
    return () => clearTimeout(timer);
  }, [searchTerm]);

  // Queries and mutations
  const { data: instruments = [], isLoading: instrumentsLoading, error: instrumentsError } = useInstruments(debouncedSearch || undefined, 100);
  const { data: cacheStatus } = useInstrumentCacheStatus();
  const { data: selectedInstruments = [], isLoading: selectedLoading } = useSelectedInstruments();
  const { data: selectedKeys = [] } = useSelectedInstrumentKeys();
  const refreshMutation = useRefreshInstruments();
  const selectMutation = useSelectInstrument();
  const deselectMutation = useDeselectInstrument();

  const handleRefresh = () => {
    refreshMutation.mutate();
  };

  const handleSelectInstrument = (instrument: InstrumentDTO) => {
    selectMutation.mutate(instrument);
  };

  const handleDeselectInstrument = (instrumentKey: string) => {
    deselectMutation.mutate(instrumentKey);
  };

  const isSelected = (instrumentKey: string) => {
    return selectedKeys.includes(instrumentKey);
  };

  const TabButton = ({ tab, label, isActive, onClick }: {
    tab: TabType;
    label: string;
    isActive: boolean;
    onClick: () => void;
  }) => (
    <button
      onClick={onClick}
      className={`px-4 py-2 font-medium text-sm rounded-lg transition-colors ${
        isActive
          ? 'bg-blue-100 text-blue-700 border-b-2 border-blue-500'
          : 'text-gray-500 hover:text-gray-700 hover:bg-gray-50'
      }`}
    >
      {label}
      {tab === 'selected' && selectedInstruments.length > 0 && (
        <span className="ml-1 bg-blue-500 text-white text-xs rounded-full px-2 py-0.5">
          {selectedInstruments.length}
        </span>
      )}
    </button>
  );

  return (
    <div className="p-4 h-full flex flex-col">
      {/* Header */}
      <div className="flex justify-between items-center mb-4">
        <h1 className="text-2xl font-semibold">Instruments</h1>
        
        {/* Cache Status & Refresh */}
        <div className="flex items-center space-x-4">
          {cacheStatus && (
            <div className="text-sm text-gray-600">
              <span>NSE Equity: {cacheStatus.nse_equity_count}</span>
              {cacheStatus.last_updated && (
                <span className="ml-2">
                  Updated: {new Date(cacheStatus.last_updated).toLocaleString()}
                </span>
              )}
            </div>
          )}
          <button
            onClick={handleRefresh}
            disabled={refreshMutation.isPending || cacheStatus?.is_refreshing}
            className="px-3 py-2 bg-blue-500 text-white text-sm rounded-lg hover:bg-blue-600 disabled:bg-gray-300 disabled:cursor-not-allowed flex items-center"
          >
            {refreshMutation.isPending || cacheStatus?.is_refreshing ? (
              <>
                <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
                Refreshing...
              </>
            ) : (
              'Refresh Cache'
            )}
          </button>
        </div>
      </div>

      {/* Tabs */}
      <div className="flex space-x-1 mb-4 border-b">
        <TabButton
          tab="master"
          label="Master Instruments"
          isActive={activeTab === 'master'}
          onClick={() => setActiveTab('master')}
        />
        <TabButton
          tab="selected"
          label="Selected Instruments"
          isActive={activeTab === 'selected'}
          onClick={() => setActiveTab('selected')}
        />
      </div>

      {/* Tab Content */}
      <div className="flex-1 overflow-hidden">
        {activeTab === 'master' && (
          <div className="h-full flex flex-col">
            {/* Search */}
            <div className="mb-4">
              <input
                type="text"
                placeholder="Search instruments by symbol or name..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>

            {/* Instruments List */}
            <div className="flex-1 overflow-auto">
              {instrumentsLoading ? (
                <div className="flex justify-center items-center h-32">
                  <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500"></div>
                </div>
              ) : instrumentsError ? (
                <div className="text-red-600 text-center py-8">
                  Error loading instruments. Please refresh the cache.
                </div>
              ) : instruments.length === 0 ? (
                <div className="text-gray-500 text-center py-8">
                  {debouncedSearch ? 'No instruments found matching your search.' : 'No cached instruments. Please refresh the cache to load data.'}
                </div>
              ) : (
                <div className="space-y-2">
                  {instruments.map((instrument) => (
                    <div
                      key={instrument.instrument_key}
                      className="flex justify-between items-center p-3 border border-gray-200 rounded-lg hover:bg-gray-50"
                    >
                      <div className="flex-1">
                        <div className="font-medium">{instrument.symbol}</div>
                        <div className="text-sm text-gray-600">{instrument.name}</div>
                        <div className="text-xs text-gray-500">
                          {instrument.exchange} • {instrument.segment}
                        </div>
                      </div>
                      <label className="flex items-center cursor-pointer">
                        <input
                          type="checkbox"
                          checked={isSelected(instrument.instrument_key)}
                          onChange={() => 
                            isSelected(instrument.instrument_key)
                              ? handleDeselectInstrument(instrument.instrument_key)
                              : handleSelectInstrument(instrument)
                          }
                          disabled={selectMutation.isPending || deselectMutation.isPending}
                          className="w-5 h-5 text-blue-600 bg-gray-100 border-gray-300 rounded focus:ring-blue-500 focus:ring-2"
                        />
                        <span className="ml-2 text-sm text-gray-700">
                          {isSelected(instrument.instrument_key) ? 'Selected' : 'Select'}
                        </span>
                      </label>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        )}

        {activeTab === 'selected' && (
          <div className="h-full">
            {selectedLoading ? (
              <div className="flex justify-center items-center h-32">
                <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500"></div>
              </div>
            ) : selectedInstruments.length === 0 ? (
              <div className="text-gray-500 text-center py-8">
                No instruments selected yet. Go to Master Instruments to select some.
              </div>
            ) : (
              <div className="space-y-2 overflow-auto h-full">
                {selectedInstruments.map((instrument) => (
                  <div
                    key={instrument.instrument_key}
                    className="flex justify-between items-center p-3 border border-gray-200 rounded-lg bg-green-50"
                  >
                    <div className="flex-1">
                      <div className="font-medium">{instrument.symbol}</div>
                      <div className="text-sm text-gray-600">{instrument.name}</div>
                      <div className="text-xs text-gray-500">
                        Selected: {new Date(instrument.selected_at).toLocaleString()}
                      </div>
                    </div>
                    <label className="flex items-center cursor-pointer">
                      <input
                        type="checkbox"
                        checked={true}
                        onChange={() => handleDeselectInstrument(instrument.instrument_key)}
                        disabled={deselectMutation.isPending}
                        className="w-5 h-5 text-blue-600 bg-gray-100 border-gray-300 rounded focus:ring-blue-500 focus:ring-2"
                      />
                      <span className="ml-2 text-sm text-gray-700">Selected</span>
                    </label>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
};
