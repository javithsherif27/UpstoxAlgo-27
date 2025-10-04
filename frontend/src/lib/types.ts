export interface ProfileDTO {
  name: string;
  client_id: string;
  kyc_status: string;
}

export interface InstrumentDTO {
  instrument_key: string;
  symbol: string;
  name: string;
  exchange: string;
  segment?: string;
  instrument_type?: string;
  lot_size?: number;
}

export interface SelectedInstrumentDTO {
  instrument_key: string;
  symbol: string;
  name: string;
  exchange: string;
  selected_at: string;
}

export interface InstrumentCacheStatusDTO {
  total_instruments: number;
  nse_equity_count: number;
  last_updated?: string;
  is_refreshing: boolean;
}

export interface CandleDataDTO {
  instrument_key: string;
  symbol: string;
  interval: string;
  timestamp: string;
  open_price: number;
  high_price: number;
  low_price: number;
  close_price: number;
  volume: number;
  open_interest?: number;
  tick_count: number;
}

export interface WebSocketStatusDTO {
  is_connected: boolean;
  subscribed_instruments: string[];
  last_heartbeat?: string;
  connection_time?: string;
  total_ticks_received: number;
  errors: string[];
}

export interface LivePriceDTO {
  symbol: string;
  ltp: number;
  open: number;
  high: number;
  low: number;
  volume: number;
  timestamp: string;
  change: number;
  change_percent: number;
}

export interface MarketDataCollectionStatusDTO {
  is_collecting: boolean;
  is_connected: boolean;
  subscribed_instruments_count: number;
  total_ticks_received: number;
  connection_time?: string;
  last_heartbeat?: string;
  recent_errors: string[];
}
