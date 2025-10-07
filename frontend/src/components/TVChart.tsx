import React from 'react';
import { createDatafeed } from '../lib/tvDatafeed';

declare global {
  interface Window { TradingView?: any }
}

type Props = {
  symbol: string;
  instrumentKey?: string;
  height?: number;
};

export const TVChart: React.FC<Props> = ({ symbol, instrumentKey, height = 480 }) => {
  const containerRef = React.useRef<HTMLDivElement>(null);
  const [isLoading, setIsLoading] = React.useState(true);
  const [error, setError] = React.useState<string | null>(null);
  const widgetRef = React.useRef<any>(null);

  React.useEffect(() => {
    let mounted = true;
    setIsLoading(true);
    setError(null);

    const scriptId = 'tv-script';
    if (!document.getElementById(scriptId)) {
      const s = document.createElement('script');
      s.id = scriptId;
      s.src = '/assets/charting_library/charting_library.min.js';
      s.type = 'text/javascript';
      s.onload = () => {
        if (mounted) {
          setTimeout(() => init(), 100); // Small delay for DOM readiness
        }
      };
      s.onerror = () => {
        if (mounted) {
          setError('Failed to load TradingView charting library');
          setIsLoading(false);
        }
      };
      document.body.appendChild(s);
    } else {
      setTimeout(() => init(), 100);
    }

    function init() {
      if (!mounted) return;
      
      try {
        if (!window.TradingView) {
          setError('TradingView library not available');
          setIsLoading(false);
          return;
        }

        if (!containerRef.current) {
          // Retry after short delay if container not ready
          setTimeout(() => {
            if (mounted) init();
          }, 100);
          return;
        }

        // Generate unique container ID for TradingView
        const containerId = `tv-chart-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
        containerRef.current.id = containerId;

        const datafeed = createDatafeed((sym) => instrumentKey);
        
        const widget = new window.TradingView.widget({
          symbol: symbol || 'NIFTY',
          interval: '1',
          container: containerId, // Use string ID instead of DOM element
          library_path: '/assets/charting_library/',
          datafeed,
          locale: 'en',
          disabled_features: [
            'use_localstorage_for_settings', 
            'symbol_search_hot_key',
            'header_symbol_search',
            'popup_hints'
          ],
          enabled_features: ['move_logo_to_main_pane'],
          autosize: true,
          timezone: 'Asia/Kolkata',
          theme: 'light',
          fullscreen: false,
          toolbar_bg: '#f1f3f6',
          loading_screen: { backgroundColor: '#ffffff' },
          overrides: {
            'paneProperties.background': '#ffffff',
            'paneProperties.vertGridProperties.color': '#f1f3f6',
            'paneProperties.horzGridProperties.color': '#f1f3f6',
          },
        });
        
        widgetRef.current = widget;
        
        widget.onChartReady(() => {
          if (mounted) {
            setIsLoading(false);
            setError(null);
          }
        });
        
      } catch (err) {
        console.error('Chart initialization error:', err);
        if (mounted) {
          setError(`Chart initialization failed: ${err instanceof Error ? err.message : 'Unknown error'}`);
          setIsLoading(false);
        }
      }
    }

    return () => {
      mounted = false;
      if (widgetRef.current && typeof widgetRef.current.remove === 'function') {
        try {
          widgetRef.current.remove();
        } catch (e) {
          console.warn('Error removing chart widget:', e);
        }
      }
    };
  }, [symbol, instrumentKey]);

  if (error) {
    return (
      <div className="flex items-center justify-center h-full bg-gray-50 border-2 border-dashed border-gray-300 rounded-lg">
        <div className="text-center p-4">
          <div className="text-red-500 mb-2">Chart Unavailable</div>
          <div className="text-sm text-gray-600 mb-3">
            TradingView library not loaded. Using placeholder chart.
          </div>
          <div className="w-full h-64 bg-white border rounded-lg flex items-center justify-center">
            <div className="text-center">
              <div className="text-2xl font-bold text-gray-600 mb-2">📈</div>
              <div className="text-lg font-semibold text-gray-700">{symbol}</div>
              <div className="text-sm text-gray-500 mt-2">Chart will load when TradingView library is available</div>
              <button 
                onClick={() => window.location.reload()} 
                className="mt-3 px-4 py-2 bg-blue-500 text-white rounded text-sm hover:bg-blue-600 transition-colors"
              >
                Retry Loading Chart
              </button>
            </div>
          </div>
        </div>
      </div>
    );
  }

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-full bg-gray-50 rounded-lg">
        <div className="text-center">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500 mx-auto mb-2"></div>
          <div className="text-sm text-gray-600">Loading Chart...</div>
        </div>
      </div>
    );
  }

  return <div ref={containerRef} style={{ width: '100%', height }} />;
};
