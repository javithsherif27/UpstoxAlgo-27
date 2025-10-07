import React from 'react';
import { useHoldings, usePositions } from '../queries/usePortfolio';

export const PortfolioPage: React.FC = () => {
  const { data: holdings = [], isLoading: loadingHoldings } = useHoldings();
  const { data: positions = [], isLoading: loadingPositions } = usePositions();

  return (
    <div className="p-4">
      <h1 className="text-xl font-bold mb-4">Portfolio</h1>
      
      <section className="mb-8">
        <h2 className="text-lg font-semibold mb-2">Holdings ({holdings.length})</h2>
        {loadingHoldings ? (
          <p>Loading holdings...</p>
        ) : holdings.length === 0 ? (
          <p className="text-gray-500">No holdings found. Check your Upstox token.</p>
        ) : (
          <div className="grid gap-2">
            {holdings.map((h: any, i: number) => (
              <div key={i} className="border rounded p-3 bg-gray-50">
                <div className="font-semibold">{h.trading_symbol || h.tradingsymbol}</div>
                <div className="text-sm text-gray-600">{h.company_name}</div>
                <div className="text-sm">
                  Qty: {h.quantity} | Avg: ₹{h.average_price} | LTP: ₹{h.last_price} | P&L: ₹{h.pnl}
                </div>
              </div>
            ))}
          </div>
        )}
      </section>

      <section>
        <h2 className="text-lg font-semibold mb-2">Positions ({positions.length})</h2>
        {loadingPositions ? (
          <p>Loading positions...</p>
        ) : positions.length === 0 ? (
          <div className="text-gray-500">
            <p>No positions found.</p>
            <p className="text-sm mt-1">
              Positions will appear here when you have:
            </p>
            <ul className="text-sm mt-2 ml-4 list-disc">
              <li>Open intraday trades</li>
              <li>Derivative positions (F&O)</li>  
              <li>Currency or commodity trades</li>
              <li>Any short-term positions not yet settled</li>
            </ul>
          </div>
        ) : (
          <div className="grid gap-2">
            {positions.map((p: any, i: number) => (
              <div key={i} className="border rounded p-3 bg-gray-50">
                <div className="flex justify-between items-start mb-2">
                  <div>
                    <div className="font-semibold">{p.trading_symbol || p.tradingsymbol}</div>
                    <div className="text-xs text-gray-500">{p.exchange} • {p.product}</div>
                  </div>
                  <div className="text-right">
                    <div className="text-sm font-medium">₹{p.last_price || 'N/A'}</div>
                    <div className="text-xs text-gray-500">LTP</div>
                  </div>
                </div>
                <div className="grid grid-cols-2 gap-2 text-sm">
                  <div>Qty: <span className="font-medium">{p.quantity || 0}</span></div>
                  <div>Avg: <span className="font-medium">₹{p.average_price || p.buy_price || 'N/A'}</span></div>
                </div>
                <div className="mt-2 pt-2 border-t border-gray-200">
                  <div className="flex justify-between text-sm">
                    <span>Day P&L:</span>
                    <span className={`font-medium ${
                      (p.unrealised !== null && p.unrealised !== undefined) 
                        ? (Number(p.unrealised) >= 0 ? 'text-green-600' : 'text-red-600')
                        : (p.pnl !== null && p.pnl !== undefined)
                        ? (Number(p.pnl) >= 0 ? 'text-green-600' : 'text-red-600')
                        : 'text-gray-500'
                    }`}>
                      ₹{p.unrealised !== null && p.unrealised !== undefined 
                        ? Number(p.unrealised).toFixed(2) 
                        : p.pnl !== null && p.pnl !== undefined 
                        ? Number(p.pnl).toFixed(2)
                        : 'N/A'}
                    </span>
                  </div>
                  {p.realised !== null && p.realised !== undefined && Number(p.realised) !== 0 && (
                    <div className="flex justify-between text-sm mt-1">
                      <span>Realised:</span>
                      <span className={`font-medium ${Number(p.realised) >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                        ₹{Number(p.realised).toFixed(2)}
                      </span>
                    </div>
                  )}
                </div>
              </div>
            ))}
          </div>
        )}
      </section>
    </div>
  );
};
