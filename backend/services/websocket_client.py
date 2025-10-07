import asyncio
import json
import uuid
import websockets
import httpx
from typing import Dict, List, Optional, Callable
from datetime import datetime, timezone
import threading
from ..models.market_data_dto import (
    MarketTickDTO, WebSocketStatusDTO, MarketDataFeedRequest, 
    SubscriptionRequest, CandleInterval
)
from ..utils.logging import get_logger

# Import protobuf classes
try:
    from ..proto.MarketDataFeed_pb2 import FeedResponse, Feed, LTPC
except ImportError:
    logger = get_logger(__name__)
    logger.warning("Protobuf classes not found. Market data decoding may not work properly.")

logger = get_logger(__name__)

class UpstoxWebSocketClient:
    def __init__(self):
        self.ws_connection = None
        self.is_connected = False
        self.subscribed_instruments: Dict[str, str] = {}  # instrument_key -> symbol
        self.connection_time: Optional[datetime] = None
        self.last_heartbeat: Optional[datetime] = None
        self.total_ticks_received = 0
        self.errors: List[str] = []
        self._access_token: Optional[str] = None
        self._ws_url: Optional[str] = None
        self._tick_callback: Optional[Callable] = None
        self._connection_task: Optional[asyncio.Task] = None
        self._running = False
        self._on_connected = None
        self._on_disconnected = None

    def set_connection_callbacks(self, on_connected, on_disconnected):
        self._on_connected = on_connected
        self._on_disconnected = on_disconnected
    
    async def get_websocket_url(self, access_token: str) -> str:
        """Get WebSocket URL from Upstox API v2"""
        try:
            headers = {
                "Authorization": f"Bearer {access_token}",
                "Accept": "*/*",
                "Content-Type": "application/json"
            }
            
            async with httpx.AsyncClient(timeout=httpx.Timeout(30.0)) as client:
                # Use the current v3 API endpoint for WebSocket URL (v2 was discontinued)
                logger.info("Requesting WebSocket URL from Upstox API v3...")
                response = await client.get(
                    "https://api.upstox.com/v3/feed/market-data-feed",
                    headers=headers,
                    follow_redirects=False
                )
                
                logger.info(f"WebSocket URL response status: {response.status_code}")
                
                if response.status_code == 200:
                    # API v3 returns JSON response with WebSocket URL
                    data = response.json()
                    if data.get("status") == "success" and "data" in data:
                        ws_url = data["data"].get("authorizedRedirectUri")
                        if ws_url and ws_url.startswith("wss://"):
                            logger.info(f"Got WebSocket URL: {ws_url}")
                            return ws_url
                elif response.status_code == 302:
                    # Fallback: Extract WebSocket URL from redirect
                    ws_url = response.headers.get("location")
                    if ws_url and ws_url.startswith("wss://"):
                        logger.info(f"Got WebSocket URL from redirect: {ws_url}")
                        return ws_url
                
                logger.error(f"Unexpected response: {response.status_code}, body: {response.text}")
                raise Exception(f"Failed to get WebSocket URL: {response.status_code}")
                
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error getting WebSocket URL: {e.response.status_code} - {e.response.text}")
            raise Exception(f"HTTP {e.response.status_code}: {e.response.text}")
        except Exception as e:
            logger.error(f"Error getting WebSocket URL: {e}")
            raise
    
    def set_tick_callback(self, callback: Callable):
        """Set callback function for processing incoming ticks"""
        self._tick_callback = callback
    
    async def connect(self, access_token: str):
        """Connect to Upstox WebSocket"""
        try:
            if self.is_connected:
                logger.warning("Already connected to WebSocket")
                return
            
            self._access_token = access_token
            self._ws_url = await self.get_websocket_url(access_token)
            self._running = True
            
            # Start connection in background task
            self._connection_task = asyncio.create_task(self._maintain_connection())
            
        except Exception as e:
            logger.error(f"Error connecting to WebSocket: {e}")
            self.errors.append(str(e))
            raise
    
    async def _maintain_connection(self):
        """Maintain WebSocket connection with automatic reconnection"""
        reconnect_attempts = 0
        max_reconnect_attempts = 5
        
        while self._running and reconnect_attempts < max_reconnect_attempts:
            try:
                logger.info(f"Connecting to WebSocket (attempt {reconnect_attempts + 1}): {self._ws_url}")
                
                # Convert headers to list of tuples format for websockets library
                headers_list = [
                    ("Authorization", f"Bearer {self._access_token}"),
                    ("User-Agent", "UpstoxAlgoTrading/1.0")
                ]
                
                async with websockets.connect(
                    self._ws_url,
                    additional_headers=headers_list,
                    ping_interval=20,
                    ping_timeout=10,
                    max_size=10 * 1024 * 1024  # 10MB max message size
                ) as websocket:
                    
                    self.ws_connection = websocket
                    self.is_connected = True
                    self.connection_time = datetime.now(timezone.utc)
                    logger.info("WebSocket connected successfully")
                    if self._on_connected:
                        try:
                            await self._on_connected()
                        except Exception as _e:
                            logger.error(f"on_connected hook error: {_e}")
                    
                    # Listen for messages
                    async for message in websocket:
                        try:
                            await self._handle_message(message)
                            self.last_heartbeat = datetime.now(timezone.utc)
                            
                        except Exception as e:
                            logger.error(f"Error handling message: {e}")
                            self.errors.append(f"Message error: {str(e)}")
                            
            except websockets.exceptions.ConnectionClosed:
                logger.warning("WebSocket connection closed")
                self.is_connected = False
                self.ws_connection = None
                if self._on_disconnected:
                    try:
                        await self._on_disconnected()
                    except Exception as _e:
                        logger.error(f"on_disconnected hook error: {_e}")
                
                if self._running:
                    logger.info("Attempting to reconnect in 5 seconds...")
                    await asyncio.sleep(5)
                    
            except Exception as e:
                logger.error(f"WebSocket error: {e}")
                self.errors.append(str(e))
                self.is_connected = False
                self.ws_connection = None
                if self._on_disconnected:
                    try:
                        await self._on_disconnected()
                    except Exception as _e:
                        logger.error(f"on_disconnected hook error: {_e}")
                
                if self._running:
                    await asyncio.sleep(5)
        
        logger.info("WebSocket connection task ended")
    
    async def _handle_message(self, message):
        """Handle incoming WebSocket messages"""
        try:
            if isinstance(message, bytes):
                # Binary message - likely protobuf, decode it
                await self._handle_protobuf_message(message)
            else:
                # Text message - parse JSON
                data = json.loads(message)
                await self._handle_json_message(data)
                
        except Exception as e:
            logger.error(f"Error processing message: {e}")
            # For now, just log the raw message for debugging
            logger.debug(f"Raw message: {message[:200] if isinstance(message, (str, bytes)) else message}")
    
    async def _handle_protobuf_message(self, message: bytes):
        """Handle protobuf encoded messages"""
        try:
            # Try to decode the protobuf message
            try:
                from ..proto.MarketDataFeed_pb2 import FeedResponse
                
                # Parse the protobuf message
                feed_response = FeedResponse()
                feed_response.ParseFromString(message)
                
                logger.debug(f"Decoded protobuf message: type={feed_response.type}, feeds={len(feed_response.feeds)}")
                
                # Process feeds
                for instrument_key, feed in feed_response.feeds.items():
                    await self._process_feed(instrument_key, feed, feed_response.currentTs)
                
                # Handle market info if present
                if feed_response.HasField('marketInfo'):
                    logger.info(f"Market info: {feed_response.marketInfo}")
                
            except ImportError:
                logger.warning("Protobuf classes not available, falling back to hex analysis")
                await self._analyze_binary_message(message)
                
            except Exception as parse_error:
                logger.error(f"Protobuf parsing failed: {parse_error}")
                # Fallback: try as JSON
                try:
                    text_data = message.decode('utf-8')
                    json_data = json.loads(text_data)
                    await self._handle_json_message(json_data)
                except:
                    logger.debug(f"Binary message analysis: {len(message)} bytes, hex: {message[:20].hex()}")
            
        except Exception as e:
            logger.error(f"Error handling protobuf message: {e}")
    
    async def _process_feed(self, instrument_key: str, feed: 'Feed', timestamp_ms: int):
        """Process individual feed data and convert to MarketTickDTO"""
        try:
            # Convert timestamp from milliseconds to datetime
            timestamp = datetime.fromtimestamp(timestamp_ms / 1000.0, tz=timezone.utc)
            
            # Extract symbol from instrument key (format: EXCHANGE_SEGMENT|SYMBOL-SERIES)
            symbol = instrument_key.split('|')[-1].split('-')[0] if '|' in instrument_key else instrument_key
            
            # Process based on feed type
            tick_data = None
            
            if feed.HasField('ltpc'):
                ltpc = feed.ltpc
                tick_data = MarketTickDTO(
                    instrument_key=instrument_key,
                    symbol=symbol,
                    timestamp=timestamp,
                    ltp=ltpc.ltp,
                    ltq=ltpc.ltq,
                    ltt=ltpc.ltt,
                    cp=ltpc.cp
                )
                
            elif feed.HasField('fullFeed'):
                full_feed = feed.fullFeed
                if full_feed.HasField('marketFF'):
                    market_ff = full_feed.marketFF
                    if market_ff.HasField('ltpc'):
                        ltpc = market_ff.ltpc
                        tick_data = MarketTickDTO(
                            instrument_key=instrument_key,
                            symbol=symbol,
                            timestamp=timestamp,
                            ltp=ltpc.ltp,
                            ltq=ltpc.ltq,
                            ltt=ltpc.ltt,
                            cp=ltpc.cp,
                            volume=market_ff.vtt,
                            oi=market_ff.oi
                        )
                elif full_feed.HasField('indexFF'):
                    index_ff = full_feed.indexFF
                    if index_ff.HasField('ltpc'):
                        ltpc = index_ff.ltpc
                        tick_data = MarketTickDTO(
                            instrument_key=instrument_key,
                            symbol=symbol,
                            timestamp=timestamp,
                            ltp=ltpc.ltp,
                            ltq=ltpc.ltq,
                            ltt=ltpc.ltt,
                            cp=ltpc.cp
                        )
            
            # Send tick to callback if we have data
            if tick_data and self._tick_callback:
                try:
                    if asyncio.iscoroutinefunction(self._tick_callback):
                        await self._tick_callback(tick_data)
                    else:
                        self._tick_callback(tick_data)
                    logger.debug(f"Processed tick for {symbol}: LTP={tick_data.ltp}")
                except Exception as callback_error:
                    logger.error(f"Error in tick callback: {callback_error}")
            
        except Exception as e:
            logger.error(f"Error processing feed for {instrument_key}: {e}")
    
    async def _analyze_binary_message(self, message: bytes):
        """Fallback analysis for binary messages when protobuf parsing fails"""
        logger.debug(f"Analyzing binary message: {len(message)} bytes")
        
        # Log first few bytes as hex for debugging
        hex_preview = message[:50].hex()
        logger.debug(f"Message hex preview: {hex_preview}")
        
        # Try to find patterns that might indicate successful subscription
        if len(message) > 10:
            # Look for instrument key patterns in the binary data
            try:
                # Try to decode parts as UTF-8 to find instrument names
                for i in range(0, len(message) - 10, 1):
                    try:
                        substr = message[i:i+20].decode('utf-8', errors='ignore')
                        if any(name in substr for name in ['INFY', 'GOLDBEES', 'NSE']):
                            logger.info(f"Found instrument reference at offset {i}: {substr}")
                    except:
                        continue
            except Exception as e:
                logger.debug(f"Binary analysis error: {e}")
    
    async def _handle_json_message(self, data: Dict):
        """Handle JSON messages (market info, feed data, etc.)"""
        try:
            msg_type = data.get("type")
            
            if msg_type == "market_info":
                logger.info("Received market info")
                logger.debug(f"Market info: {data}")
                
            elif msg_type == "live_feed":
                await self._process_live_feed(data)
                
            elif msg_type == "initial_feed":
                await self._process_initial_feed(data)
                
            else:
                logger.debug(f"Unknown message type: {msg_type}")
                
        except Exception as e:
            logger.error(f"Error handling JSON message: {e}")
    
    async def _process_live_feed(self, data: Dict):
        """Process live feed data and create ticks"""
        try:
            feeds = data.get("feeds", {})
            current_ts = data.get("currentTs")
            
            for instrument_key, feed_data in feeds.items():
                ltpc_data = feed_data.get("ltpc")
                if ltpc_data and self._tick_callback:
                    
                    # Create tick from LTPC data
                    tick = MarketTickDTO(
                        instrument_key=instrument_key,
                        symbol=self.subscribed_instruments.get(instrument_key, instrument_key),
                        ltp=float(ltpc_data.get("ltp", 0)),
                        ltt=int(ltpc_data.get("ltt", current_ts or 0)),
                        ltq=int(ltpc_data.get("ltq", 0)),
                        cp=float(ltpc_data.get("cp", 0)),
                        timestamp=datetime.now(timezone.utc),
                        raw_data=feed_data
                    )
                    
                    self.total_ticks_received += 1
                    await self._tick_callback(tick)
                    
        except Exception as e:
            logger.error(f"Error processing live feed: {e}")
    
    async def _process_initial_feed(self, data: Dict):
        """Process initial feed (snapshot) data"""
        logger.info("Received initial feed (snapshot)")
        # Process similar to live feed
        await self._process_live_feed(data)
    
    async def subscribe(self, subscription_request: SubscriptionRequest):
        """Subscribe to instruments for market data"""
        try:
            if not self.is_connected or not self.ws_connection:
                raise Exception("WebSocket not connected")
            
            # Create subscription message
            request = MarketDataFeedRequest(
                guid=str(uuid.uuid4()),
                method="sub",
                data={
                    "mode": subscription_request.mode,
                    "instrumentKeys": subscription_request.instrument_keys
                }
            )
            
            # Send binary message (as required by Upstox V3)
            message = json.dumps(request.dict()).encode('utf-8')
            await self.ws_connection.send(message)
            
            # Update subscribed instruments
            for instrument_key in subscription_request.instrument_keys:
                # Extract symbol from instrument key (e.g., "NSE_EQ|INE002A01018" -> "RELIANCE")
                symbol = instrument_key.split('|')[-1] if '|' in instrument_key else instrument_key
                self.subscribed_instruments[instrument_key] = symbol
            
            logger.info(f"Subscribed to {len(subscription_request.instrument_keys)} instruments")
            
        except Exception as e:
            logger.error(f"Error subscribing to instruments: {e}")
            self.errors.append(f"Subscription error: {str(e)}")
            raise
    
    async def unsubscribe(self, instrument_keys: List[str]):
        """Unsubscribe from instruments"""
        try:
            if not self.is_connected or not self.ws_connection:
                raise Exception("WebSocket not connected")
            
            request = MarketDataFeedRequest(
                guid=str(uuid.uuid4()),
                method="unsub",
                data={
                    "instrumentKeys": instrument_keys
                }
            )
            
            message = json.dumps(request.dict()).encode('utf-8')
            await self.ws_connection.send(message)
            
            # Remove from subscribed instruments
            for instrument_key in instrument_keys:
                self.subscribed_instruments.pop(instrument_key, None)
            
            logger.info(f"Unsubscribed from {len(instrument_keys)} instruments")
            
        except Exception as e:
            logger.error(f"Error unsubscribing: {e}")
            self.errors.append(f"Unsubscription error: {str(e)}")
            raise
    
    async def disconnect(self):
        """Disconnect from WebSocket"""
        try:
            self._running = False
            
            if self.ws_connection:
                await self.ws_connection.close()
                
            if self._connection_task:
                self._connection_task.cancel()
                try:
                    await self._connection_task
                except asyncio.CancelledError:
                    pass
            
            self.is_connected = False
            self.ws_connection = None
            self.subscribed_instruments.clear()
            
            logger.info("WebSocket disconnected")
            
        except Exception as e:
            logger.error(f"Error disconnecting: {e}")
    
    def get_status(self) -> WebSocketStatusDTO:
        """Get current WebSocket status"""
        return WebSocketStatusDTO(
            is_connected=self.is_connected,
            subscribed_instruments=list(self.subscribed_instruments.keys()),
            last_heartbeat=self.last_heartbeat,
            connection_time=self.connection_time,
            total_ticks_received=self.total_ticks_received,
            errors=self.errors[-10:]  # Last 10 errors only
        )

# Global WebSocket client instance
upstox_ws_client = UpstoxWebSocketClient()