import React, { useMemo } from 'react';
import { useMarketDataCollectionStatus } from '../queries/useMarketData';

function timeAgo(iso?: string) {
  if (!iso) return '—';
  const diff = Date.now() - new Date(iso).getTime();
  const s = Math.max(0, Math.floor(diff / 1000));
  if (s < 60) return `${s}s`;
  const m = Math.floor(s / 60);
  if (m < 60) return `${m}m`;
  const h = Math.floor(m / 60);
  return `${h}h`;
}

export const StreamingStatus: React.FC = () => {
  const { data, isLoading } = useMarketDataCollectionStatus();

  const status = useMemo(() => {
    return {
      connected: !!data?.is_connected,
      collecting: !!data?.is_collecting,
      subs: data?.subscribed_instruments_count ?? 0,
      ticks: data?.total_ticks_received ?? 0,
      heartbeat: data?.last_heartbeat,
    };
  }, [data]);

  const dot = status.connected ? 'bg-green-500' : 'bg-gray-400';
  const text = status.connected ? 'Connected' : 'Idle';

  return (
    <div className="flex items-center gap-2 text-xs px-2 py-1 rounded-md border border-gray-200 bg-white shadow-sm">
      <span className={`inline-block w-2 h-2 rounded-full ${dot}`} />
      {isLoading ? (
        <span className="text-gray-500">Checking…</span>
      ) : (
        <>
          <span className="text-gray-800 font-medium">{text}</span>
          <span className="text-gray-400">•</span>
          <span className="text-gray-700">Subs: {status.subs}</span>
          <span className="text-gray-400">•</span>
          <span className="text-gray-700">Ticks: {status.ticks}</span>
          <span className="text-gray-400">•</span>
          <span className="text-gray-500">Hb: {timeAgo(status.heartbeat)}</span>
        </>
      )}
    </div>
  );
};
