from __future__ import annotations

import asyncio
from typing import Any, Dict, List

import httpx

BASE_URL = "https://api.upstox.com/v3"


def _headers(token: str) -> Dict[str, str]:
    return {
        "Authorization": f"Bearer {token}",
        "Accept": "application/json",
    }


async def _get(client: httpx.AsyncClient, url: str, token: str) -> Any:
    for attempt in range(4):
        try:
            r = await client.get(url, headers=_headers(token))
            r.raise_for_status()
            data = r.json()
            # Upstox often wraps in {data: ...} and sometimes nests keys under holdings/positions
            if isinstance(data, dict):
                inner = data.get("data", data)
                # If inner is a dict that contains the list under holdings/positions, return that list
                if isinstance(inner, dict):
                    if "holdings" in inner and isinstance(inner["holdings"], list):
                        return inner["holdings"]
                    if "positions" in inner and isinstance(inner["positions"], list):
                        return inner["positions"]
                return inner
            return data
        except httpx.HTTPError:
            if attempt == 3:
                raise
            await asyncio.sleep(0.5 * (2 ** attempt))


async def get_holdings(token: str) -> List[Dict[str, Any]]:
    async with httpx.AsyncClient(timeout=httpx.Timeout(20.0)) as client:
        data = await _get(client, f"{BASE_URL}/portfolio/holdings", token)
        return data if isinstance(data, list) else (data.get("holdings", []) if isinstance(data, dict) else [])


async def get_positions(token: str) -> List[Dict[str, Any]]:
    async with httpx.AsyncClient(timeout=httpx.Timeout(20.0)) as client:
        data = await _get(client, f"{BASE_URL}/portfolio/positions", token)
        return data if isinstance(data, list) else (data.get("positions", []) if isinstance(data, dict) else [])
