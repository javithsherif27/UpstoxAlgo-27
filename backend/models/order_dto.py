"""
Order Management Data Transfer Objects and Types
Comprehensive order models for manual and automated trading
"""
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any, Union
from enum import Enum
from pydantic import BaseModel, Field, validator
from decimal import Decimal


class OrderType(str, Enum):
    """Order types supported by Upstox"""
    MARKET = "MARKET"
    LIMIT = "LIMIT"
    SL_MARKET = "SL-M"  # Stop Loss Market
    SL_LIMIT = "SL"     # Stop Loss Limit


class OrderSide(str, Enum):
    """Order side - Buy or Sell"""
    BUY = "BUY"
    SELL = "SELL"


class OrderValidity(str, Enum):
    """Order validity types"""
    DAY = "DAY"         # Valid for current trading day
    IOC = "IOC"         # Immediate or Cancel
    GTD = "GTD"         # Good Till Date


class OrderStatus(str, Enum):
    """Order status from Upstox"""
    PENDING = "PENDING"
    OPEN = "OPEN"
    COMPLETE = "COMPLETE"
    CANCELLED = "CANCELLED"
    REJECTED = "REJECTED"
    AFTER_MARKET_ORDER_REQ_RECEIVED = "AFTER_MARKET_ORDER_REQ_RECEIVED"
    MODIFY_PENDING = "MODIFY_PENDING"
    MODIFY_VALIDATION_PENDING = "MODIFY_VALIDATION_PENDING"
    TRIGGER_PENDING = "TRIGGER_PENDING"


class ProductType(str, Enum):
    """Product types for different trading segments"""
    INTRADAY = "I"      # Intraday/MIS
    DELIVERY = "D"      # Delivery/CNC
    CO = "CO"           # Cover Order
    OCO = "OCO"         # One Cancels Other


class OrderDisclosedQuantity(str, Enum):
    """Disclosed quantity options"""
    MIN = "MIN"         # Minimum disclosed quantity
    PERCENTAGE_10 = "10%"
    PERCENTAGE_25 = "25%"


class PlaceOrderRequest(BaseModel):
    """Request model for placing an order"""
    instrument_key: str = Field(..., description="Instrument key from master data")
    quantity: int = Field(..., gt=0, description="Order quantity")
    price: Optional[Decimal] = Field(None, description="Limit price (required for LIMIT orders)")
    order_type: OrderType = Field(..., description="Order type")
    order_side: OrderSide = Field(..., description="Buy or Sell")
    product_type: ProductType = Field(..., description="Product type")
    validity: OrderValidity = Field(OrderValidity.DAY, description="Order validity")
    
    # Optional fields
    disclosed_quantity: Optional[int] = Field(None, description="Disclosed quantity")
    trigger_price: Optional[Decimal] = Field(None, description="Trigger price for SL orders")
    tag: Optional[str] = Field(None, max_length=20, description="Custom tag for order tracking")
    
    @validator('price')
    def validate_price(cls, v, values):
        """Validate price based on order type"""
        order_type = values.get('order_type')
        if order_type in [OrderType.LIMIT, OrderType.SL_LIMIT] and v is None:
            raise ValueError(f"Price is required for {order_type} orders")
        if order_type == OrderType.MARKET and v is not None:
            raise ValueError("Price should not be provided for MARKET orders")
        return v
    
    @validator('trigger_price')
    def validate_trigger_price(cls, v, values):
        """Validate trigger price for stop loss orders"""
        order_type = values.get('order_type')
        if order_type in [OrderType.SL_MARKET, OrderType.SL_LIMIT] and v is None:
            raise ValueError(f"Trigger price is required for {order_type} orders")
        return v


class ModifyOrderRequest(BaseModel):
    """Request model for modifying an existing order"""
    order_id: str = Field(..., description="Order ID to modify")
    quantity: Optional[int] = Field(None, gt=0, description="New quantity")
    order_type: Optional[OrderType] = Field(None, description="New order type")
    price: Optional[Decimal] = Field(None, description="New price")
    trigger_price: Optional[Decimal] = Field(None, description="New trigger price")
    disclosed_quantity: Optional[int] = Field(None, description="New disclosed quantity")
    validity: Optional[OrderValidity] = Field(None, description="New validity")


class CancelOrderRequest(BaseModel):
    """Request model for cancelling an order"""
    order_id: str = Field(..., description="Order ID to cancel")


class OrderResponseDTO(BaseModel):
    """Response model for order operations"""
    order_id: str = Field(..., description="Unique order identifier")
    status: str = Field(..., description="Order placement status")
    message: Optional[str] = Field(None, description="Response message")
    
    # Additional fields from Upstox response
    exchange_order_id: Optional[str] = Field(None, description="Exchange order ID")
    exchange_timestamp: Optional[datetime] = Field(None, description="Exchange timestamp")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class OrderDetailsDTO(BaseModel):
    """Detailed order information"""
    order_id: str
    exchange_order_id: Optional[str] = None
    parent_order_id: Optional[str] = None
    
    # Order details
    instrument_key: str
    symbol: str
    product_type: ProductType
    order_type: OrderType
    order_side: OrderSide
    validity: OrderValidity
    
    # Quantities and prices
    quantity: int
    filled_quantity: int = 0
    pending_quantity: int = 0
    price: Optional[Decimal] = None
    trigger_price: Optional[Decimal] = None
    average_price: Optional[Decimal] = None
    disclosed_quantity: Optional[int] = None
    
    # Status and timestamps
    status: OrderStatus
    status_message: Optional[str] = None
    order_timestamp: datetime
    exchange_timestamp: Optional[datetime] = None
    
    # Additional info
    tag: Optional[str] = None
    lot_size: int = 1
    tick_size: Decimal = Decimal('0.01')
    
    # P&L for completed orders
    realized_pnl: Optional[Decimal] = None
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat(),
            Decimal: lambda v: float(v)
        }


class TradeDTO(BaseModel):
    """Individual trade/execution details"""
    trade_id: str
    order_id: str
    exchange_order_id: Optional[str] = None
    
    instrument_key: str
    symbol: str
    
    # Trade details
    trade_price: Decimal
    trade_quantity: int
    trade_timestamp: datetime
    
    # Additional info
    exchange: str
    order_side: OrderSide
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat(),
            Decimal: lambda v: float(v)
        }


class PortfolioPositionDTO(BaseModel):
    """Portfolio position from websocket feed"""
    instrument_key: str
    symbol: str
    exchange: str
    
    # Position details
    quantity: int = 0
    average_price: Decimal = Decimal('0')
    last_price: Decimal = Decimal('0')
    
    # P&L calculations
    unrealized_pnl: Decimal = Decimal('0')
    realized_pnl: Decimal = Decimal('0')
    day_change: Decimal = Decimal('0')
    day_change_percentage: Decimal = Decimal('0')
    
    # Additional metrics
    market_value: Decimal = Decimal('0')
    invested_value: Decimal = Decimal('0')
    
    class Config:
        json_encoders = {
            Decimal: lambda v: float(v)
        }


class OrderBookDTO(BaseModel):
    """Order book summary"""
    orders: List[OrderDetailsDTO] = []
    total_orders: int = 0
    pending_orders: int = 0
    completed_orders: int = 0
    cancelled_orders: int = 0
    
    # Summary metrics
    total_buy_value: Decimal = Decimal('0')
    total_sell_value: Decimal = Decimal('0')
    
    class Config:
        json_encoders = {
            Decimal: lambda v: float(v)
        }


class AlgoOrderRequest(BaseModel):
    """Order request from algorithmic trading system"""
    strategy_id: str = Field(..., description="Strategy identifier")
    signal_id: str = Field(..., description="Trading signal identifier")
    
    # Order details (inherits from PlaceOrderRequest)
    instrument_key: str
    quantity: int
    price: Optional[Decimal] = None
    order_type: OrderType
    order_side: OrderSide
    product_type: ProductType = ProductType.INTRADAY
    validity: OrderValidity = OrderValidity.DAY
    
    # Algo-specific fields
    confidence_score: Optional[float] = Field(None, ge=0, le=1, description="Signal confidence 0-1")
    risk_level: Optional[str] = Field(None, description="Risk level: LOW, MEDIUM, HIGH")
    max_loss_percentage: Optional[float] = Field(None, description="Maximum allowed loss %")
    target_profit_percentage: Optional[float] = Field(None, description="Target profit %")
    
    # Metadata
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional strategy data")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat(),
            Decimal: lambda v: float(v)
        }


class OrderExecutionResult(BaseModel):
    """Result of order execution for algo trading"""
    order_request: AlgoOrderRequest
    order_response: Optional[OrderResponseDTO] = None
    execution_status: str  # SUCCESS, FAILED, PENDING
    error_message: Optional[str] = None
    executed_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }