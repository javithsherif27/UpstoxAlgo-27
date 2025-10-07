from __future__ import annotations

import asyncio
from typing import Any, Dict, List

import httpx
from ..utils.logging import get_logger

logger = get_logger(__name__)

# Use correct Upstox API v2 base URL
BASE_URL = "https://api.upstox.com/v2"


def _headers(token: str) -> Dict[str, str]:
    return {
        "Authorization": f"Bearer {token}",
        "Accept": "application/json",
        "Content-Type": "application/json",
    }


async def _get(client: httpx.AsyncClient, url: str, token: str) -> Any:
    for attempt in range(4):
        try:
            logger.info(f"Making API request to: {url}")
            r = await client.get(url, headers=_headers(token))
            r.raise_for_status()
            
            response_data = r.json()
            logger.info(f"API Response status: {response_data.get('status', 'unknown')}")
            
            # Upstox API v2 response format: {"status": "success", "data": [...]}
            if isinstance(response_data, dict):
                if response_data.get("status") == "success" and "data" in response_data:
                    data = response_data["data"]
                    logger.info(f"Successfully retrieved {len(data) if isinstance(data, list) else 'non-list'} items")
                    return data if isinstance(data, list) else [data] if data else []
                else:
                    logger.warning(f"Unexpected response format: {response_data}")
                    return []
            return response_data
            
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error {e.response.status_code}: {e.response.text}")
            if attempt == 3:
                raise
            await asyncio.sleep(0.5 * (2 ** attempt))
        except httpx.HTTPError as e:
            logger.error(f"HTTP error on attempt {attempt + 1}: {e}")
            if attempt == 3:
                raise
            await asyncio.sleep(0.5 * (2 ** attempt))


async def get_holdings(token: str) -> List[Dict[str, Any]]:
    """Get long-term holdings using correct Upstox API v2 endpoint."""
    async with httpx.AsyncClient(timeout=httpx.Timeout(30.0)) as client:
        # Use the correct endpoint for holdings
        holdings = await _get(client, f"{BASE_URL}/portfolio/long-term-holdings", token)
        logger.info(f"Retrieved {len(holdings)} holdings")
        return holdings


async def get_positions(token: str) -> List[Dict[str, Any]]:
    """Get short-term positions using correct Upstox API v2 endpoint."""
    async with httpx.AsyncClient(timeout=httpx.Timeout(30.0)) as client:
        # Use the correct endpoint for positions - short-term-positions
        positions = await _get(client, f"{BASE_URL}/portfolio/short-term-positions", token)
        logger.info(f"Retrieved {len(positions)} positions")
        return positions
