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

  React.useEffect(() => {
    const scriptId = 'tv-script';
    if (!document.getElementById(scriptId)) {
      const s = document.createElement('script');
      s.id = scriptId;
      s.src = '/assets/charting_library/charting_library.min.js';
      s.type = 'text/javascript';
      s.onload = () => init();
      document.body.appendChild(s);
    } else {
      init();
    }

    function init() {
      if (!window.TradingView || !containerRef.current) return;
      const datafeed = createDatafeed((sym) => instrumentKey);
      const widget = new window.TradingView.widget({
        symbol,
        interval: '1',
        container: containerRef.current,
        library_path: '/assets/charting_library/',
        datafeed,
        locale: 'en',
        disabled_features: ['use_localstorage_for_settings'],
        enabled_features: [],
        autosize: true,
        timezone: 'Asia/Kolkata',
        theme: 'light',
      });
      (window as any).__tvWidget = widget;
    }

    return () => {
      // cleanup handled by library when container removed
    };
  }, [symbol, instrumentKey]);

  return <div ref={containerRef} style={{ width: '100%', height }} />;
};
