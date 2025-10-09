import asyncio
import json
from typing import Set, Dict, Any
from fastapi import WebSocket
from ..utils.logging import get_logger

logger = get_logger(__name__)


class WebSocketBroker:
    """Simple WebSocket broadcast hub for streaming ticks and candles to UI clients."""

    def __init__(self) -> None:
        self._clients: Set[WebSocket] = set()
        self._lock = asyncio.Lock()

    async def add(self, ws: WebSocket):
        async with self._lock:
            self._clients.add(ws)
            logger.info(f"WS client connected. Total: {len(self._clients)}")

    async def remove(self, ws: WebSocket):
        async with self._lock:
            if ws in self._clients:
                self._clients.remove(ws)
                logger.info(f"WS client disconnected. Total: {len(self._clients)}")

    async def broadcast(self, message: Dict[str, Any]):
        if not self._clients:
            return
        data = json.dumps(message, default=str)
        # Copy to avoid iteration issues if modified
        clients = list(self._clients)
        for ws in clients:
            try:
                await ws.send_text(data)
            except Exception as e:
                logger.warning(f"WS send failed: {e}. Removing client")
                await self.remove(ws)


ws_broker = WebSocketBroker()
