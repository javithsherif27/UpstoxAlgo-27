import { apiClient } from './api';
import { getUpstoxToken } from './auth';

type Resolution = '1'|'5'|'15'|'60'|'1D';

function mapResolutionToTf(res: string): string {
  if (res === '1') return '1m';
  if (res === '5') return '5m';
  if (res === '15') return '15m';
  if (res === '60') return '1h';
  return '1d';
}

function candleToBar(c: any) {
  // aggregator candle
  if (c && c.start && c.o != null) {
    return {
      time: new Date(c.start).getTime(),
      open: c.o,
      high: c.h,
      low: c.l,
      close: c.c,
      volume: c.v ?? 0,
    };
  }
  // legacy storage candle
  if (c && c.timestamp && c.open_price != null) {
    return {
      time: new Date(c.timestamp).getTime(),
      open: c.open_price,
      high: c.high_price,
      low: c.low_price,
      close: c.close_price,
      volume: c.volume ?? 0,
    };
  }
  return null;
}

export function createDatafeed(symbolToInstrumentKey?: (symbol: string)=>string|undefined) {
  return {
    onReady: (cb: any) => {
      setTimeout(() => cb({
        supported_resolutions: ['1','5','15','60','1D'],
        supports_marks: false,
        supports_timescale_marks: false,
        supports_time: false,
      }), 0);
    },
    resolveSymbol: (symbolName: string, onResolve: any, onError: any) => {
      const symbolInfo = {
        name: symbolName,
        ticker: symbolName,
        description: symbolName,
        type: 'stock',
        session: '0930-1530',
        timezone: 'Asia/Kolkata',
        exchange: 'NSE',
        minmov: 1,
        pricescale: 100,
        has_intraday: true,
        supported_resolutions: ['1','5','15','60','1D'],
        volume_precision: 0,
        data_status: 'streaming',
      } as any;
      onResolve(symbolInfo);
    },
    getBars: async (symbolInfo: any, resolution: Resolution, periodParams: any, onResult: any, onError: any) => {
      const tf = mapResolutionToTf(resolution);
      try {
        // Try aggregator first
        const { data } = await apiClient.get(`/api/candles`, {
          params: { symbol: symbolInfo.ticker, timeframe: tf, limit: 1000 },
        });
        let candles = (data?.candles ?? []) as any[];
        if ((!candles || candles.length === 0) && (tf === '1m' || tf === '5m' || tf === '15m')) {
          // fallback to legacy storage using instrument_key
          if (symbolToInstrumentKey) {
            const ik = symbolToInstrumentKey(symbolInfo.ticker);
            if (ik) {
              const { data: data2 } = await apiClient.get(`/api/market-data/candles/${encodeURIComponent(ik)}`, {
                params: { interval: tf, limit: 1000 },
              });
              candles = data2 as any[];
            }
          }
        }
        const bars = (candles || []).map(candleToBar).filter(Boolean);
        onResult(bars, { noData: bars.length === 0 });
      } catch (e) {
        onError(e);
      }
    },
    subscribeBars: (symbolInfo: any, resolution: Resolution, onRealtimeCallback: any, subscriberUID: string, onResetCacheNeededCallback: any) => {
      const tf = mapResolutionToTf(resolution);
      const interval = setInterval(async () => {
        try {
          const { data } = await apiClient.get(`/api/candles`, { params: { symbol: symbolInfo.ticker, timeframe: tf, limit: 1 } });
          const candles = data?.candles ?? [];
          if (candles.length > 0) {
            const bar = candleToBar(candles[candles.length - 1]);
            if (bar) onRealtimeCallback(bar);
          }
        } catch {}
      }, 2000);
      (window as any).__tvSubs = (window as any).__tvSubs || {};
      (window as any).__tvSubs[subscriberUID] = interval;
    },
    unsubscribeBars: (subscriberUID: string) => {
      const subs = (window as any).__tvSubs || {};
      const intv = subs[subscriberUID];
      if (intv) clearInterval(intv);
      delete subs[subscriberUID];
    },
  };
}
