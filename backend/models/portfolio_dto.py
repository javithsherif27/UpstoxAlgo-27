from __future__ import annotations
from typing import Optional
from pydantic import BaseModel


class Holding(BaseModel):
    """Holding model based on Upstox API v2 response format."""
    isin: Optional[str] = None
    cnc_used_quantity: Optional[int] = None
    collateral_type: Optional[str] = None
    company_name: Optional[str] = None
    haircut: Optional[float] = None
    product: Optional[str] = None  # I, D, CO, MTF
    quantity: Optional[int] = None
    trading_symbol: Optional[str] = None
    tradingsymbol: Optional[str] = None  # Alternative field name
    last_price: Optional[float] = None
    close_price: Optional[float] = None
    pnl: Optional[float] = None
    day_change: Optional[float] = None
    day_change_percentage: Optional[float] = None
    instrument_token: Optional[str] = None
    average_price: Optional[float] = None
    collateral_quantity: Optional[int] = None
    collateral_update_quantity: Optional[int] = None
    t1_quantity: Optional[int] = None
    exchange: Optional[str] = None


class Position(BaseModel):
    """Position model for Upstox API v2 short-term-positions response."""
    # Core position data
    exchange: Optional[str] = None
    multiplier: Optional[float] = None
    value: Optional[float] = None
    pnl: Optional[float] = None
    product: Optional[str] = None  # I, D, CO
    instrument_token: Optional[str] = None
    
    # Pricing information
    average_price: Optional[float] = None
    last_price: Optional[float] = None
    close_price: Optional[float] = None
    buy_price: Optional[float] = None
    sell_price: Optional[float] = None
    
    # Quantity breakdown
    quantity: Optional[int] = None  # Net position quantity
    overnight_quantity: Optional[int] = None
    day_buy_quantity: Optional[int] = None
    day_sell_quantity: Optional[int] = None
    overnight_buy_quantity: Optional[int] = None
    overnight_sell_quantity: Optional[int] = None
    
    # Value breakdown  
    buy_value: Optional[float] = None
    sell_value: Optional[float] = None
    day_buy_value: Optional[float] = None
    day_sell_value: Optional[float] = None
    day_buy_price: Optional[float] = None
    day_sell_price: Optional[float] = None
    overnight_buy_amount: Optional[float] = None
    overnight_sell_amount: Optional[float] = None
    
    # P&L breakdown
    unrealised: Optional[float] = None  # Day P&L against open positions
    realised: Optional[float] = None    # Day P&L against closed positions
    
    # Symbol information (API returns both formats)
    trading_symbol: Optional[str] = None
    tradingsymbol: Optional[str] = None