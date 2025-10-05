from __future__ import annotations

import asyncio
from datetime import datetime, timezone
from typing import Any, Callable, Dict, Optional

import httpx
import websockets

from ..utils.logging import get_logger


logger = get_logger(__name__)


class PortfolioWSClient:
    def __init__(self):
        self._access_token: Optional[str] = None
        self._ws_url: Optional[str] = None
        self._running = False
        self._conn_task: Optional[asyncio.Task] = None
        self._on_update: Optional[Callable[[Dict[str, Any]], None]] = None
        self.is_connected = False

    def set_update_callback(self, cb: Callable[[Dict[str, Any]], None]):
        self._on_update = cb

    async def _get_ws_url(self, token: str) -> str:
        async with httpx.AsyncClient() as client:
            r = await client.get(
                "https://api.upstox.com/v3/feed/portfolio-stream-feed",
                headers={"Authorization": f"Bearer {token}"},
                follow_redirects=False,
            )
            if r.status_code != 302:
                raise RuntimeError(f"Unexpected status {r.status_code} for portfolio stream url")
            url = r.headers.get("location")
            if not url or not url.startswith("wss://"):
                raise RuntimeError("Portfolio stream URL missing")
            return url

    async def connect(self, token: str):
        if self._running:
            return
        self._access_token = token
        self._ws_url = await self._get_ws_url(token)
        self._running = True
        self._conn_task = asyncio.create_task(self._run())

    async def disconnect(self):
        self._running = False
        if self._conn_task:
            self._conn_task.cancel()
            try:
                await self._conn_task
            except asyncio.CancelledError:
                pass
        self.is_connected = False

    async def _run(self):
        while self._running:
            try:
                async with websockets.connect(
                    self._ws_url,
                    extra_headers={"Authorization": f"Bearer {self._access_token}"},
                    ping_interval=20,
                    ping_timeout=10,
                ) as ws:
                    self.is_connected = True
                    async for msg in ws:
                        await self._handle(msg)
            except Exception as e:
                logger.error(f"Portfolio WS error: {e}")
                self.is_connected = False
                if self._running:
                    await asyncio.sleep(5)

    async def _handle(self, message):
        try:
            # Upstox sends JSON text frames with portfolio updates
            import json
            data = json.loads(message) if isinstance(message, (str, bytes)) else message
            if self._on_update:
                self._on_update(data)
        except Exception as e:
            logger.error(f"Portfolio WS handle error: {e}")


portfolio_ws_client = PortfolioWSClient()
