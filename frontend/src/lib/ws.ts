export type StreamEvent =
  | { type: 'tick'; instrument_key: string; symbol: string; ltp: number; ltq?: number; ltt?: number; timestamp: string }
  | { type: 'candle'; event: 'update' | 'closed'; instrument_key: string; symbol: string; interval: string; timestamp: string; open: number; high: number; low: number; close: number; volume: number; tick_count?: number };

export class UIStreamClient {
  private socket?: WebSocket;
  private listeners: Set<(e: StreamEvent) => void> = new Set();

  constructor(private base = (import.meta as any)?.env?.VITE_API_BASE || 'http://localhost:8000') {}

  connect() {
    if (this.socket && (this.socket.readyState === WebSocket.OPEN || this.socket.readyState === WebSocket.CONNECTING)) return;
    const wsUrl = this.base.replace('http', 'ws') + '/ws/stream';
    this.socket = new WebSocket(wsUrl);

    this.socket.onmessage = (msg) => {
      try {
        const data = JSON.parse(msg.data) as StreamEvent;
        this.listeners.forEach((cb) => cb(data));
      } catch {}
    };
    this.socket.onclose = () => {
      // simple retry
      setTimeout(() => this.connect(), 3000);
    };
  }

  on(cb: (e: StreamEvent) => void) {
    this.listeners.add(cb);
    return () => this.listeners.delete(cb);
  }
}

export const uiStream = new UIStreamClient();
