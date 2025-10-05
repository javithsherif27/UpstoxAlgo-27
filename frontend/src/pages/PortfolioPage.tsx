import React from 'react';
import { useHoldings, usePositions, usePortfolioStreamStatus, startPortfolioStream, stopPortfolioStream } from '../queries/usePortfolio';

export const PortfolioPage: React.FC = () => {
  const { data: holdings = [], isLoading: loadingH } = useHoldings();
  const { data: positions = [], isLoading: loadingP } = usePositions();
  const { data: streamStatus } = usePortfolioStreamStatus();

  return (
    <div className="p-4 space-y-8">
      <div className="flex items-center justify-between">
        <h1 className="text-xl font-semibold">Portfolio</h1>
        <div className="flex items-center gap-2">
          <span className="text-sm text-gray-600">{streamStatus?.isConnected ? 'Stream: Connected' : 'Stream: Disconnected'}</span>
          <button onClick={() => startPortfolioStream()} className="px-3 py-1 text-sm rounded bg-green-600 text-white hover:bg-green-700">Start Stream</button>
          <button onClick={() => stopPortfolioStream()} className="px-3 py-1 text-sm rounded bg-gray-600 text-white hover:bg-gray-700">Stop Stream</button>
        </div>
      </div>

      <section>
        <h2 className="text-lg font-medium mb-2">Holdings</h2>
        {loadingH ? (
          <div>Loading holdings…</div>
        ) : holdings.length === 0 ? (
          <div className="text-gray-500">No holdings</div>
        ) : (
          <div className="overflow-auto border rounded">
            <table className="min-w-full text-sm">
              <thead className="bg-gray-100">
                <tr>
                  <th className="px-3 py-2 text-left">Symbol</th>
                  <th className="px-3 py-2 text-right">Qty</th>
                  <th className="px-3 py-2 text-right">Avg Price</th>
                  <th className="px-3 py-2 text-right">LTP</th>
                  <th className="px-3 py-2 text-right">P&L</th>
                </tr>
              </thead>
              <tbody>
                {holdings.map((h: any, idx: number) => (
                  <tr key={idx} className="odd:bg-white even:bg-gray-50">
                    <td className="px-3 py-2">{h.trading_symbol || h.symbol || h.instrument_name}</td>
                    <td className="px-3 py-2 text-right">{h.quantity ?? '-'}</td>
                    <td className="px-3 py-2 text-right">{h.average_price ?? '-'}</td>
                    <td className="px-3 py-2 text-right">{h.ltp ?? '-'}</td>
                    <td className="px-3 py-2 text-right">{h.unrealized_pnl ?? h.pnl ?? '-'}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </section>

      <section>
        <h2 className="text-lg font-medium mb-2">Positions</h2>
        {loadingP ? (
          <div>Loading positions…</div>
        ) : positions.length === 0 ? (
          <div className="text-gray-500">No positions</div>
        ) : (
          <div className="overflow-auto border rounded">
            <table className="min-w-full text-sm">
              <thead className="bg-gray-100">
                <tr>
                  <th className="px-3 py-2 text-left">Symbol</th>
                  <th className="px-3 py-2 text-right">Qty</th>
                  <th className="px-3 py-2 text-right">Avg Price</th>
                  <th className="px-3 py-2 text-right">LTP</th>
                  <th className="px-3 py-2 text-right">P&L</th>
                </tr>
              </thead>
              <tbody>
                {positions.map((p: any, idx: number) => (
                  <tr key={idx} className="odd:bg-white even:bg-gray-50">
                    <td className="px-3 py-2">{p.trading_symbol || p.symbol || p.instrument_name}</td>
                    <td className="px-3 py-2 text-right">{p.quantity ?? '-'}</td>
                    <td className="px-3 py-2 text-right">{p.average_price ?? '-'}</td>
                    <td className="px-3 py-2 text-right">{p.ltp ?? '-'}</td>
                    <td className="px-3 py-2 text-right">{p.unrealized_pnl ?? p.pnl ?? '-'}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </section>
    </div>
  );
};
