import React from 'react';
import { useSelectedInstruments, useDeselectInstrument } from '../queries/useInstruments';
import { SelectedInstrumentDTO } from '../lib/types';

interface Props {
  isOpen: boolean;
  onClose: () => void;
}

export const SelectedInstrumentsSidebar: React.FC<Props> = ({ isOpen, onClose }) => {
  const { data: selectedInstruments = [], isLoading } = useSelectedInstruments();
  const deselectMutation = useDeselectInstrument();

  const handleRemove = (instrumentKey: string) => {
    deselectMutation.mutate(instrumentKey);
  };

  if (!isOpen) return null;

  return (
    <>
      {/* Overlay */}
      <div className="fixed inset-0 bg-black bg-opacity-50 z-40" onClick={onClose} />
      
      {/* Sidebar */}
      <div className="fixed left-0 top-0 h-full w-80 bg-white shadow-lg z-50 flex flex-col">
        {/* Header */}
        <div className="flex justify-between items-center p-4 border-b">
          <h2 className="text-lg font-semibold">Selected Instruments</h2>
          <button
            onClick={onClose}
            className="p-2 hover:bg-gray-100 rounded-lg"
          >
            ✕
          </button>
        </div>

        {/* Content */}
        <div className="flex-1 overflow-auto p-4">
          {isLoading ? (
            <div className="flex justify-center items-center h-32">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500"></div>
            </div>
          ) : selectedInstruments.length === 0 ? (
            <div className="text-gray-500 text-center py-8">
              No instruments selected
            </div>
          ) : (
            <div className="space-y-3">
              {selectedInstruments.map((instrument: SelectedInstrumentDTO) => (
                <div
                  key={instrument.instrument_key}
                  className="p-3 border border-gray-200 rounded-lg bg-green-50"
                >
                  <div className="flex justify-between items-start">
                    <div className="flex-1">
                      <div className="font-medium text-sm">{instrument.symbol}</div>
                      <div className="text-xs text-gray-600 mt-1 truncate">
                        {instrument.name}
                      </div>
                    </div>
                    <button
                      onClick={() => handleRemove(instrument.instrument_key)}
                      disabled={deselectMutation.isPending}
                      className="ml-2 p-1 text-red-500 hover:bg-red-100 rounded text-xs"
                      title="Remove"
                    >
                      ✕
                    </button>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="p-4 border-t bg-gray-50">
          <div className="text-sm text-gray-600 text-center">
            {selectedInstruments.length} instrument{selectedInstruments.length !== 1 ? 's' : ''} ready for trading
          </div>
        </div>
      </div>
    </>
  );
};