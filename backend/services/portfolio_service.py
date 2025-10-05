from __future__ import annotations

import asyncio
from typing import Any, Dict, List, Optional

from .upstox_portfolio_client import get_holdings, get_positions
from .portfolio_ws_client import portfolio_ws_client


class PortfolioService:
    def __init__(self):
        self._token: Optional[str] = None
        self._holdings: List[Dict[str, Any]] = []
        self._positions: List[Dict[str, Any]] = []

        def _on_update(data: Dict[str, Any]):
            # naive merge; real impl can be refined per Upstox schema
            if isinstance(data, dict):
                if "holdings" in data and isinstance(data["holdings"], list):
                    self._holdings = data["holdings"]
                if "positions" in data and isinstance(data["positions"], list):
                    self._positions = data["positions"]

        portfolio_ws_client.set_update_callback(_on_update)

    async def refresh_rest(self, token: str):
        self._holdings = await get_holdings(token)
        self._positions = await get_positions(token)

    async def start_stream(self, token: str):
        self._token = token
        await self.refresh_rest(token)
        await portfolio_ws_client.connect(token)

    async def stop_stream(self):
        await portfolio_ws_client.disconnect()
        self._token = None

    def get_status(self) -> Dict[str, Any]:
        return {
            "isConnected": portfolio_ws_client.is_connected,
            "holdingsCount": len(self._holdings),
            "positionsCount": len(self._positions),
        }

    def get_holdings(self) -> List[Dict[str, Any]]:
        return self._holdings

    def get_positions(self) -> List[Dict[str, Any]]:
        return self._positions


portfolio_service = PortfolioService()
