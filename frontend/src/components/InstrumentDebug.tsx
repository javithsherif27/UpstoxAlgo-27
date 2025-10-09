import React from 'react';
import { useSelectedInstruments } from '../hooks/useSelectedInstruments';

const InstrumentDebug: React.FC = () => {
  const { data: selectedInstruments = [], isLoading, error, isError } = useSelectedInstruments();

  return (
    <div className="bg-white p-4 rounded-lg shadow-md m-4">
      <h3 className="text-lg font-semibold mb-4">Selected Instruments Debug</h3>
      
      <div className="space-y-2">
        <div>
          <strong>Loading:</strong> {isLoading ? 'Yes' : 'No'}
        </div>
        
        <div>
          <strong>Error:</strong> {isError ? error?.message || 'Unknown error' : 'None'}
        </div>
        
        <div>
          <strong>Instruments Count:</strong> {selectedInstruments.length}
        </div>
        
        {selectedInstruments.length > 0 && (
          <div>
            <strong>Instruments:</strong>
            <ul className="list-disc list-inside ml-4 mt-2">
              {selectedInstruments.map((instrument, index) => (
                <li key={instrument.id || index} className="text-sm">
                  {instrument.symbol} - {instrument.name} ({instrument.exchange})
                </li>
              ))}
            </ul>
          </div>
        )}
      </div>
      
      {/* Raw data for debugging */}
      <details className="mt-4">
        <summary className="cursor-pointer font-medium">Raw Data</summary>
        <pre className="mt-2 p-2 bg-gray-100 rounded text-xs overflow-auto">
          {JSON.stringify({ 
            selectedInstruments, 
            isLoading, 
            isError, 
            error: error?.message 
          }, null, 2)}
        </pre>
      </details>
    </div>
  );
};

export default InstrumentDebug;