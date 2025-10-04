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
    
    async def get_websocket_url(self, access_token: str) -> str:
        """Get WebSocket URL from Upstox API"""
        try:
            headers = {
                "Authorization": f"Bearer {access_token}",
                "Accept": "*/*"
            }
            
            async with httpx.AsyncClient() as client:
                # The API redirects to WebSocket URL
                response = await client.get(
                    "https://api.upstox.com/v3/feed/market-data-feed",
                    headers=headers,
                    follow_redirects=False
                )
                
                if response.status_code == 302:
                    # Extract WebSocket URL from redirect
                    ws_url = response.headers.get("location")
                    if ws_url and ws_url.startswith("wss://"):
                        logger.info(f"Got WebSocket URL: {ws_url}")
                        return ws_url
                    
                logger.error(f"Unexpected response: {response.status_code}")
                raise Exception(f"Failed to get WebSocket URL: {response.status_code}")
                
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
        while self._running:
            try:
                logger.info(f"Connecting to WebSocket: {self._ws_url}")
                
                headers = {
                    "Authorization": f"Bearer {self._access_token}"
                }
                
                async with websockets.connect(
                    self._ws_url,
                    extra_headers=headers,
                    ping_interval=20,
                    ping_timeout=10,
                    max_size=10 * 1024 * 1024  # 10MB max message size
                ) as websocket:
                    
                    self.ws_connection = websocket
                    self.is_connected = True
                    self.connection_time = datetime.now(timezone.utc)
                    logger.info("WebSocket connected successfully")
                    
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
                
                if self._running:
                    logger.info("Attempting to reconnect in 5 seconds...")
                    await asyncio.sleep(5)
                    
            except Exception as e:
                logger.error(f"WebSocket error: {e}")
                self.errors.append(str(e))
                self.is_connected = False
                self.ws_connection = None
                
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
            # TODO: Implement protobuf decoding
            # For now, we'll try to extract basic tick data
            # This is a simplified approach - in production, use proper protobuf decoding
            
            # Parse as JSON for debugging (if it's actually JSON)
            try:
                text_data = message.decode('utf-8')
                json_data = json.loads(text_data)
                await self._handle_json_message(json_data)
                return
            except:
                pass
            
            logger.debug(f"Received protobuf message of {len(message)} bytes")
            # TODO: Implement proper protobuf parsing using the MarketDataFeed.proto
            
        except Exception as e:
            logger.error(f"Error handling protobuf message: {e}")
    
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