import React, { useEffect, useRef, useState } from 'react';
import { createChart, ColorType, IChartApi, ISeriesApi, CandlestickData } from 'lightweight-charts';
import { useCandles } from '../queries/useMarketData';

interface Instrument {
  instrumentKey: string;
  symbol: string;
  name: string;
}

interface TradingViewChartProps {
  instrument: Instrument;
  interval?: string;
  height?: number;
}

interface CandleData {
  timestamp: string;
  open_price: number;
  high_price: number;
  low_price: number;
  close_price: number;
  volume: number;
}

export const TradingViewChart: React.FC<TradingViewChartProps> = ({ 
  instrument, 
  interval = '1d', 
  height = 500 
}) => {
  console.log('🔧 TradingViewChart: Rendering with props:', { 
    instrument: instrument.symbol, 
    interval, 
    height 
  });

  const chartContainerRef = useRef<HTMLDivElement>(null);
  const chartRef = useRef<IChartApi | null>(null);
  const candlestickSeriesRef = useRef<ISeriesApi<'Candlestick'> | null>(null);
  const volumeSeriesRef = useRef<ISeriesApi<'Histogram'> | null>(null);
  
  // Ensure a sensible minimum height to avoid 0/negative heights in hidden/flex parents
  const effectiveHeight = Math.max(240, height || 0);

  const { data: candlesData, isLoading, error } = useCandles(
    instrument.instrumentKey, 
    interval, 
    undefined, 
    undefined, 
    200
  );

  console.log('📊 TradingViewChart: Data state:', { 
    candlesCount: candlesData?.length || 0,
    isLoading, 
    error: error?.message,
    instrumentKey: instrument.instrumentKey
  });

  // Convert candle data to TradingView format
  const convertToTradingViewData = (candles: CandleData[]): CandlestickData[] => {
    return candles
      .map(candle => {
        const timestamp = new Date(candle.timestamp).getTime() / 1000; // Convert to seconds
        return {
          time: timestamp as any,
          open: candle.open_price,
          high: candle.high_price,
          low: candle.low_price,
          close: candle.close_price
        };
      })
      .sort((a, b) => a.time - b.time); // Ensure chronological order
  };

  const convertVolumeData = (candles: CandleData[]) => {
    return candles
      .map(candle => {
        const timestamp = new Date(candle.timestamp).getTime() / 1000;
        return {
          time: timestamp as any,
          value: candle.volume,
          color: candle.close_price >= candle.open_price ? '#26a69a' : '#ef5350'
        };
      })
      .sort((a, b) => a.time - b.time);
  };

  // Initialize chart (only when container exists and chart not yet created)
  useEffect(() => {
    // Avoid re-initializing if chart already created
    if (chartRef.current) return;

    // Wait until the container is actually mounted in the DOM
    if (!chartContainerRef.current) {
      // Container not ready yet (e.g., first render) — skip without logging noise
      return;
    }

    // If container has no width yet (e.g., hidden tab), wait for next frame
    if (chartContainerRef.current.clientWidth === 0) {
      requestAnimationFrame(() => {
        // Trigger another run by setting a micro state toggle if still not initialized
        if (!chartRef.current) {
          // Force a synchronous re-run of this effect by updating width via applyOptions later
          try {
            // If the container is now available with width, create chart
            if (chartContainerRef.current && chartContainerRef.current.clientWidth > 0) {
              // Manually invoke chart creation by setting a temporary height change
              // The actual creation happens below when this effect re-runs on the same tick
            }
          } catch {}
        }
      });
    }

    console.log('✅ TradingViewChart: Creating chart instance...');

    // Create chart with professional styling
  const chart = createChart(chartContainerRef.current, {
      layout: {
        background: { type: ColorType.Solid, color: '#ffffff' },
        textColor: '#333',
        fontSize: 12,
      },
      grid: {
        vertLines: { color: '#f0f0f0' },
        horzLines: { color: '#f0f0f0' },
      },
      crosshair: {
        mode: 1,
        vertLine: {
          color: '#758696',
          width: 1,
          style: 2,
        },
        horzLine: {
          color: '#758696',
          width: 1,
          style: 2,
        },
      },
      rightPriceScale: {
        borderColor: '#D1D4DC',
        scaleMargins: {
          top: 0.1,
          bottom: 0.2,
        },
      },
      timeScale: {
        borderColor: '#D1D4DC',
        timeVisible: true,
        secondsVisible: false,
      },
      width: chartContainerRef.current.clientWidth,
      height: effectiveHeight,
    });

    // Add candlestick series
    const candlestickSeries = chart.addCandlestickSeries({
      upColor: '#26a69a',
      downColor: '#ef5350',
      borderDownColor: '#ef5350',
      borderUpColor: '#26a69a',
      wickDownColor: '#ef5350',
      wickUpColor: '#26a69a',
    });

    // Add volume series
    const volumeSeries = chart.addHistogramSeries({
      color: '#26a69a',
      priceFormat: {
        type: 'volume',
      },
      priceScaleId: 'volume',
    });

    chart.priceScale('volume').applyOptions({
      scaleMargins: {
        top: 0.8,
        bottom: 0,
      },
    });

  chartRef.current = chart;
  candlestickSeriesRef.current = candlestickSeries;
  volumeSeriesRef.current = volumeSeries;

    // Handle resize
    const resizeObserver = new ResizeObserver(() => {
      if (chartContainerRef.current) {
        chart.applyOptions({ 
          width: chartContainerRef.current.clientWidth 
        });
      }
    });

    resizeObserver.observe(chartContainerRef.current);

    return () => {
      resizeObserver.disconnect();
      chart.remove();
      chartRef.current = null;
      candlestickSeriesRef.current = null;
      volumeSeriesRef.current = null;
    };
  }, [effectiveHeight]);

  // React to height changes without recreating chart
  useEffect(() => {
    if (chartRef.current) {
      chartRef.current.applyOptions({ height: effectiveHeight });
      // Also ensure width is synced (in case parent changed)
      if (chartContainerRef.current) {
        chartRef.current.applyOptions({ width: chartContainerRef.current.clientWidth });
      }
    }
  }, [effectiveHeight]);

  // Update data when candles change
  useEffect(() => {
    if (!candlesData || !chartRef.current || !candlestickSeriesRef.current || !volumeSeriesRef.current) return;

    try {
      const tradingViewData = convertToTradingViewData(candlesData);
      const volumeData = convertVolumeData(candlesData);

      if (tradingViewData.length > 0) {
        candlestickSeriesRef.current.setData(tradingViewData);
        volumeSeriesRef.current.setData(volumeData);
        
        // Fit content to show all data
        chartRef.current.timeScale().fitContent();
      }
    } catch (error) {
      console.error('Error updating TradingView chart data:', error);
    }
  }, [candlesData]);

  return (
  <div className="relative bg-white rounded-lg shadow-sm border overflow-hidden" style={{ height: effectiveHeight }}>
      {/* Chart Container (always rendered to ensure ref is available) */}
      <div ref={chartContainerRef} className="w-full h-full" />

      {/* Info Bar */}
      <div className="absolute top-2 left-2 z-10 bg-white/90 backdrop-blur-sm rounded px-2 py-1 text-xs text-gray-700 shadow-sm">
        <span className="font-medium">{instrument.symbol}</span>
        <span className="mx-1">•</span>
        <span>{interval.toUpperCase()}</span>
        <span className="mx-1">•</span>
        <span>{candlesData?.length || 0} candles</span>
      </div>

      {/* Loading overlay */}
      {isLoading && (
        <div className="absolute inset-0 flex items-center justify-center bg-white/70">
          <div className="text-center">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500 mx-auto mb-2"></div>
            <div className="text-sm text-gray-700">Loading TradingView Chart…</div>
          </div>
        </div>
      )}

      {/* Error / Empty overlay (only if not loading) */}
      {!isLoading && (error || !candlesData || candlesData.length === 0) && (
        <div className="absolute inset-0 flex items-center justify-center bg-white/80">
          <div className="text-center p-6">
            <div className="text-4xl text-gray-400 mb-4">📊</div>
            <div className="text-lg font-semibold text-gray-700 mb-2">{instrument.symbol}</div>
            <div className="text-sm text-gray-600 mb-3">
              {error ? 'Failed to load chart data' : `No ${interval} chart data available`}
            </div>
            <div className="text-xs text-gray-500 mt-2">
              {error ? 'Please try refreshing the page' : `Use "Historical Data Fetch" to get ${interval} candles`}
            </div>
            <div className="text-xs text-blue-500 mt-1">Available intervals: 1m, 5m, 15m, 1d</div>
          </div>
        </div>
      )}

      {/* Professional Chart Watermark */}
      <div className="absolute bottom-2 right-2 text-xs text-gray-400 bg-white/90 backdrop-blur-sm rounded px-2 py-1">
        TradingView Style Chart
      </div>
    </div>
  );
};