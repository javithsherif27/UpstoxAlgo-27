import React, { useState, useRef, useEffect } from 'react';
import { useInstruments } from '../queries/useInstruments';

interface Instrument {
  instrumentKey: string;
  symbol: string;
  name: string;
}

interface InstrumentSearchProps {
  onAddToWatchlist: (instrument: Instrument) => void;
}

export const InstrumentSearch: React.FC<InstrumentSearchProps> = ({ onAddToWatchlist }) => {
  const [query, setQuery] = useState('');
  const [isOpen, setIsOpen] = useState(false);
  const [selectedIndex, setSelectedIndex] = useState(-1);
  const inputRef = useRef<HTMLInputElement>(null);
  const dropdownRef = useRef<HTMLDivElement>(null);

  const { data: instruments, isLoading } = useInstruments();

  // Filter instruments based on search query
  const filteredInstruments = React.useMemo(() => {
    if (!query.trim() || !instruments) return [];
    
    const searchTerm = query.toLowerCase();
    return instruments
      .filter(instrument => 
        instrument.symbol?.toLowerCase().includes(searchTerm) ||
        instrument.name?.toLowerCase().includes(searchTerm)
      )
      .slice(0, 10) // Limit to 10 results for performance
      .map(instrument => ({
        instrumentKey: instrument.instrument_key,
        symbol: instrument.symbol || '',
        name: instrument.name || ''
      }));
  }, [query, instruments]);

  // Handle keyboard navigation
  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (!isOpen || filteredInstruments.length === 0) return;

    switch (e.key) {
      case 'ArrowDown':
        e.preventDefault();
        setSelectedIndex(prev => 
          prev < filteredInstruments.length - 1 ? prev + 1 : prev
        );
        break;
      case 'ArrowUp':
        e.preventDefault();
        setSelectedIndex(prev => prev > 0 ? prev - 1 : -1);
        break;
      case 'Enter':
        e.preventDefault();
        if (selectedIndex >= 0 && selectedIndex < filteredInstruments.length) {
          handleSelectInstrument(filteredInstruments[selectedIndex]);
        }
        break;
      case 'Escape':
        setIsOpen(false);
        setSelectedIndex(-1);
        inputRef.current?.blur();
        break;
    }
  };

  // Handle instrument selection
  const handleSelectInstrument = (instrument: Instrument) => {
    onAddToWatchlist(instrument);
    setQuery('');
    setIsOpen(false);
    setSelectedIndex(-1);
    inputRef.current?.blur();
  };

  // Close dropdown when clicking outside
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (
        dropdownRef.current &&
        !dropdownRef.current.contains(event.target as Node) &&
        !inputRef.current?.contains(event.target as Node)
      ) {
        setIsOpen(false);
        setSelectedIndex(-1);
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  // Reset selected index when filtered results change
  useEffect(() => {
    setSelectedIndex(-1);
  }, [filteredInstruments]);

  return (
    <div className="relative">
      {/* Search Input */}
      <div className="relative">
        <input
          ref={inputRef}
          type="text"
          value={query}
          onChange={(e) => {
            setQuery(e.target.value);
            setIsOpen(true);
          }}
          onFocus={() => setIsOpen(true)}
          onKeyDown={handleKeyDown}
          placeholder="Search instruments (e.g., INFY, GOLDBEES...)"
          className="w-full px-4 py-2 pl-10 pr-4 text-sm border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none"
        />
        <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
          <svg className="w-4 h-4 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
          </svg>
        </div>
      </div>

      {/* Search Dropdown */}
      {isOpen && (
        <div
          ref={dropdownRef}
          className="absolute top-full left-0 right-0 mt-1 bg-white border border-gray-200 rounded-lg shadow-lg max-h-80 overflow-y-auto z-50"
        >
          {isLoading && query.trim() && (
            <div className="p-4 text-center text-gray-500">
              <div className="animate-spin w-5 h-5 border-2 border-blue-500 border-t-transparent rounded-full mx-auto mb-2"></div>
              Searching instruments...
            </div>
          )}

          {!isLoading && query.trim() && filteredInstruments.length === 0 && (
            <div className="p-4 text-center text-gray-500">
              <div className="text-sm">No instruments found for "{query}"</div>
              <div className="text-xs mt-1">Try searching with different keywords</div>
            </div>
          )}

          {filteredInstruments.length > 0 && (
            <div className="py-1">
              {filteredInstruments.map((instrument, index) => (
                <button
                  key={instrument.instrumentKey}
                  onClick={() => handleSelectInstrument(instrument)}
                  className={`w-full px-4 py-3 text-left hover:bg-gray-50 focus:bg-gray-50 focus:outline-none transition-colors ${
                    index === selectedIndex ? 'bg-blue-50' : ''
                  }`}
                >
                  <div className="flex items-center justify-between">
                    <div>
                      <div className="font-medium text-gray-900">{instrument.symbol}</div>
                      <div className="text-sm text-gray-600 truncate">{instrument.name}</div>
                    </div>
                    <div className="text-xs text-blue-600 font-medium">Add</div>
                  </div>
                </button>
              ))}
            </div>
          )}

          {!query.trim() && (
            <div className="p-4 text-center text-gray-500">
              <div className="text-sm">Start typing to search instruments</div>
              <div className="text-xs mt-1">Search by symbol or company name</div>
            </div>
          )}
        </div>
      )}
    </div>
  );
};