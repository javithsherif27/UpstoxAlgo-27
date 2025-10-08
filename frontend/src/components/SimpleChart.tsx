import React, { useEffect, useState } from 'react';
import { useCandles } from '../queries/useMarketData';

interface Instrument {
  instrumentKey: string;
  symbol: string;
  name: string;
}

interface SimpleChartProps {
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

export const SimpleChart: React.FC<SimpleChartProps> = ({ instrument, interval = '1d', height = 400 }) => {
  console.log(`SimpleChart: Rendering for ${instrument.symbol} with interval: ${interval}`);
  const { data: candlesData, isLoading, error } = useCandles(instrument.instrumentKey, interval, undefined, undefined, 100);
  const [chartData, setChartData] = useState<CandleData[]>([]);

  useEffect(() => {
    console.log(`SimpleChart: useEffect triggered for ${instrument.symbol} ${interval}:`, {
      candlesData: candlesData?.length || 0,
      isLoading,
      error: error?.message
    });
    
    if (candlesData && candlesData.length > 0) {
      // Sort by timestamp to ensure proper chronological order
      const sortedData = [...candlesData].sort((a, b) => 
        new Date(a.timestamp).getTime() - new Date(b.timestamp).getTime()
      );
      setChartData(sortedData);
      console.log(`SimpleChart: Set chart data with ${sortedData.length} candles for ${interval}`);
    } else {
      setChartData([]);
    }
  }, [candlesData, isLoading, error, instrument.symbol, interval]);

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-full bg-gray-50 rounded-lg">
        <div className="text-center">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500 mx-auto mb-2"></div>
          <div className="text-sm text-gray-600">Loading Chart Data...</div>
        </div>
      </div>
    );
  }

  if (error || !chartData.length) {
    return (
      <div className="flex items-center justify-center h-full bg-gray-50 border-2 border-dashed border-gray-300 rounded-lg">
        <div className="text-center p-4">
          <div className="text-gray-500 mb-2">📊</div>
          <div className="text-sm text-gray-600 mb-3">
            {error ? 'Failed to load chart data' : `No ${interval} chart data available`}
          </div>
          <div className="text-lg font-semibold text-gray-700">{instrument.symbol}</div>
          <div className="text-xs text-gray-500 mt-2">
            {error 
              ? 'Please try refreshing the page' 
              : `Use "Historical Data Fetch" component to get ${interval} candle data`}
          </div>
          <div className="text-xs text-blue-500 mt-1">
            Available intervals: 1m, 5m, 15m, 1d
          </div>
        </div>
      </div>
    );
  }

  // Calculate chart dimensions and scaling
  const prices = chartData.map(candle => [candle.high_price, candle.low_price, candle.open_price, candle.close_price]).flat();
  const maxPrice = Math.max(...prices);
  const minPrice = Math.min(...prices);
  const priceRange = maxPrice - minPrice;
  const padding = priceRange * 0.1; // 10% padding
  const chartMax = maxPrice + padding;
  const chartMin = minPrice - padding;
  const chartRange = chartMax - chartMin;

  const chartWidth = 800;
  const chartHeight = height - 60; // Reserve space for labels
  const candleWidth = Math.max(2, chartWidth / chartData.length - 2);

  // Generate SVG candlestick chart
  const candlesticks = chartData.map((candle, index) => {
    const x = (index * chartWidth) / chartData.length + candleWidth / 2;
    const openY = chartHeight - ((candle.open_price - chartMin) / chartRange) * chartHeight;
    const closeY = chartHeight - ((candle.close_price - chartMin) / chartRange) * chartHeight;
    const highY = chartHeight - ((candle.high_price - chartMin) / chartRange) * chartHeight;
    const lowY = chartHeight - ((candle.low_price - chartMin) / chartRange) * chartHeight;
    
    const isGreen = candle.close_price >= candle.open_price;
    const bodyTop = Math.min(openY, closeY);
    const bodyBottom = Math.max(openY, closeY);
    const bodyHeight = Math.max(1, Math.abs(closeY - openY));
    
    return (
      <g key={index}>
        {/* High-Low line */}
        <line
          x1={x}
          y1={highY}
          x2={x}
          y2={lowY}
          stroke={isGreen ? '#10b981' : '#ef4444'}
          strokeWidth="1"
        />
        {/* Body rectangle */}
        <rect
          x={x - candleWidth / 2}
          y={bodyTop}
          width={candleWidth}
          height={bodyHeight}
          fill={isGreen ? '#10b981' : '#ef4444'}
          stroke={isGreen ? '#10b981' : '#ef4444'}
          strokeWidth="1"
        />
      </g>
    );
  });

  // Generate price labels
  const priceLabels = [];
  const labelCount = 5;
  for (let i = 0; i <= labelCount; i++) {
    const price = chartMin + (chartRange * i) / labelCount;
    const y = chartHeight - (i * chartHeight) / labelCount;
    priceLabels.push(
      <text
        key={i}
        x={chartWidth + 5}
        y={y + 3}
        fontSize="10"
        fill="#6b7280"
        textAnchor="start"
      >
        ₹{price.toFixed(2)}
      </text>
    );
  }

  // Generate date labels
  const dateLabels = chartData
    .filter((_, index) => index % Math.ceil(chartData.length / 6) === 0)
    .map((candle, labelIndex) => {
      const dataIndex = labelIndex * Math.ceil(chartData.length / 6);
      const x = (dataIndex * chartWidth) / chartData.length;
      const date = new Date(candle.timestamp);
      const dateStr = date.toLocaleDateString('en-IN', { 
        month: 'short', 
        day: 'numeric' 
      });
      
      return (
        <text
          key={labelIndex}
          x={x}
          y={chartHeight + 20}
          fontSize="10"
          fill="#6b7280"
          textAnchor="middle"
        >
          {dateStr}
        </text>
      );
    });

  const latestCandle = chartData[chartData.length - 1];
  const firstCandle = chartData[0];
  const priceChange = latestCandle.close_price - firstCandle.open_price;
  const priceChangePercent = (priceChange / firstCandle.open_price) * 100;

  return (
    <div className="w-full h-full bg-white rounded-lg border">
      {/* Chart Header */}
      <div className="p-4 border-b bg-gray-50">
        <div className="flex items-center justify-between">
          <div>
            <h3 className="font-semibold text-gray-900">{instrument.symbol} - {interval.toUpperCase()} Chart</h3>
            <div className="flex items-center space-x-4 mt-1 text-sm">
              <span>₹{latestCandle.close_price.toFixed(2)}</span>
              <span className={priceChange >= 0 ? 'text-green-600' : 'text-red-600'}>
                {priceChange >= 0 ? '+' : ''}₹{priceChange.toFixed(2)} ({priceChangePercent.toFixed(2)}%)
              </span>
            </div>
          </div>
          <div className="text-xs text-gray-500">
            {chartData.length} candles • Last updated: {new Date(latestCandle.timestamp).toLocaleString()}
          </div>
        </div>
      </div>
      
      {/* Chart Area */}
      <div className="p-4" style={{ height: height - 80 }}>
        <svg
          width="100%"
          height="100%"
          viewBox={`0 0 ${chartWidth + 60} ${chartHeight + 40}`}
          className="border rounded"
        >
          {/* Grid lines */}
          {Array.from({ length: 6 }, (_, i) => (
            <line
              key={i}
              x1="0"
              y1={(i * chartHeight) / 5}
              x2={chartWidth}
              y2={(i * chartHeight) / 5}
              stroke="#f3f4f6"
              strokeWidth="1"
            />
          ))}
          
          {/* Candlesticks */}
          {candlesticks}
          
          {/* Price labels */}
          {priceLabels}
          
          {/* Date labels */}
          {dateLabels}
        </svg>
      </div>

      {/* Chart Legend */}
      <div className="px-4 pb-3 border-t bg-gray-50">
        <div className="flex items-center justify-center space-x-6 text-xs text-gray-600">
          <div className="flex items-center space-x-1">
            <div className="w-3 h-2 bg-green-500 rounded"></div>
            <span>Bullish</span>
          </div>
          <div className="flex items-center space-x-1">
            <div className="w-3 h-2 bg-red-500 rounded"></div>
            <span>Bearish</span>
          </div>
          <span>•</span>
          <span>Daily candles showing OHLC data</span>
        </div>
      </div>
    </div>
  );
};