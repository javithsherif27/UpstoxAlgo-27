"""
Orders API Router
Handles order placement, management, and portfolio tracking
"""
from fastapi import APIRouter, HTTPException, Depends, Query
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta

from ..models.order_dto import (
    PlaceOrderRequest, ModifyOrderRequest, CancelOrderRequest,
    OrderResponseDTO, OrderDetailsDTO, TradeDTO, OrderBookDTO,
    AlgoOrderRequest, OrderExecutionResult, PortfolioPositionDTO
)
from ..services.order_service import order_service, algo_order_service
from ..utils.auth import get_current_user, get_access_token
from ..utils.logging import get_logger

logger = get_logger(__name__)
router = APIRouter(prefix="/api/orders", tags=["Orders"])


@router.post("/place", response_model=OrderResponseDTO)
async def place_order(
    order_request: PlaceOrderRequest,
    access_token: str = Depends(get_access_token)
):
    """Place a new order"""
    try:
        logger.info(f"Placing order: {order_request.order_side.value} {order_request.quantity} {order_request.instrument_key}")
        
        result = await order_service.place_order(order_request, access_token)
        
        if result.status == 'error':
            raise HTTPException(status_code=400, detail=result.message)
            
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error placing order: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.put("/modify", response_model=OrderResponseDTO)
async def modify_order(
    modify_request: ModifyOrderRequest,
    access_token: str = Depends(get_access_token)
):
    """Modify an existing order"""
    try:
        logger.info(f"Modifying order: {modify_request.order_id}")
        
        result = await order_service.modify_order(modify_request, access_token)
        
        if result.status == 'error':
            raise HTTPException(status_code=400, detail=result.message)
            
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error modifying order: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.delete("/cancel", response_model=OrderResponseDTO)
async def cancel_order(
    cancel_request: CancelOrderRequest,
    access_token: str = Depends(get_access_token)
):
    """Cancel an existing order"""
    try:
        logger.info(f"Cancelling order: {cancel_request.order_id}")
        
        result = await order_service.cancel_order(cancel_request, access_token)
        
        if result.status == 'error':
            raise HTTPException(status_code=400, detail=result.message)
            
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error cancelling order: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.get("/book", response_model=OrderBookDTO)
async def get_order_book(
    access_token: str = Depends(get_access_token),
    status: Optional[str] = Query(None, description="Filter by order status"),
    symbol: Optional[str] = Query(None, description="Filter by symbol"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of orders to return")
):
    """Get order book with optional filters"""
    try:
        logger.info(f"Fetching order book with filters - status: {status}, symbol: {symbol}, limit: {limit}")
        
        order_book = await order_service.get_order_book(access_token)
        
        # Apply client-side filters if needed
        if status or symbol:
            filtered_orders = []
            for order in order_book.orders:
                if status and order.status.value.upper() != status.upper():
                    continue
                if symbol and order.symbol.upper() != symbol.upper():
                    continue
                filtered_orders.append(order)
            
            order_book.orders = filtered_orders[:limit]
            order_book.total_orders = len(filtered_orders)
        else:
            order_book.orders = order_book.orders[:limit]
        
        return order_book
        
    except Exception as e:
        logger.error(f"Error fetching order book: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.get("/details/{order_id}", response_model=OrderDetailsDTO)
async def get_order_details(
    order_id: str,
    access_token: str = Depends(get_access_token)
):
    """Get details of a specific order"""
    try:
        logger.info(f"Fetching order details for: {order_id}")
        
        order_details = await order_service.get_order_details(order_id, access_token)
        
        if not order_details:
            raise HTTPException(status_code=404, detail=f"Order {order_id} not found")
            
        return order_details
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching order details: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.get("/trades", response_model=List[TradeDTO])
async def get_trades(
    access_token: str = Depends(get_access_token),
    symbol: Optional[str] = Query(None, description="Filter by symbol"),
    from_date: Optional[datetime] = Query(None, description="Filter trades from this date"),
    to_date: Optional[datetime] = Query(None, description="Filter trades until this date"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of trades to return")
):
    """Get trades with optional filters"""
    try:
        logger.info(f"Fetching trades with filters - symbol: {symbol}, from_date: {from_date}, to_date: {to_date}")
        
        trades = await order_service.get_trades(access_token)
        
        # Apply client-side filters
        if symbol or from_date or to_date:
            filtered_trades = []
            for trade in trades:
                if symbol and trade.symbol.upper() != symbol.upper():
                    continue
                if from_date and trade.trade_timestamp < from_date:
                    continue
                if to_date and trade.trade_timestamp > to_date:
                    continue
                filtered_trades.append(trade)
            
            trades = filtered_trades
        
        return trades[:limit]
        
    except Exception as e:
        logger.error(f"Error fetching trades: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.post("/algo/execute", response_model=OrderExecutionResult)
async def execute_algo_order(
    algo_request: AlgoOrderRequest,
    access_token: str = Depends(get_access_token)
):
    """Execute an algorithmic trading order"""
    try:
        logger.info(f"Executing algo order - strategy: {algo_request.strategy_id}, signal: {algo_request.signal_id}")
        
        result = await algo_order_service.execute_algo_order(algo_request, access_token)
        
        return result
        
    except Exception as e:
        logger.error(f"Error executing algo order: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.get("/portfolio/positions", response_model=List[PortfolioPositionDTO])
async def get_portfolio_positions(
    access_token: str = Depends(get_access_token),
    product_type: Optional[str] = Query(None, description="Filter by product type (D, I, CNC)"),
    exchange: Optional[str] = Query(None, description="Filter by exchange")
):
    """Get current portfolio positions"""
    try:
        logger.info("Fetching portfolio positions")
        
        # This would typically call Upstox portfolio API
        # For now, return empty list as placeholder
        positions = []
        
        return positions
        
    except Exception as e:
        logger.error(f"Error fetching portfolio positions: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.get("/statistics")
async def get_order_statistics(
    access_token: str = Depends(get_access_token),
    days: int = Query(7, ge=1, le=365, description="Number of days to analyze")
):
    """Get order and trading statistics"""
    try:
        logger.info(f"Fetching order statistics for last {days} days")
        
        # Get order book for statistics
        order_book = await order_service.get_order_book(access_token)
        trades = await order_service.get_trades(access_token)
        
        # Calculate basic statistics
        from_date = datetime.now() - timedelta(days=days)
        
        recent_orders = [o for o in order_book.orders if o.order_timestamp >= from_date]
        recent_trades = [t for t in trades if t.trade_timestamp >= from_date]
        
        total_orders = len(recent_orders)
        total_trades = len(recent_trades)
        
        successful_orders = sum(1 for o in recent_orders if o.status.value == 'COMPLETE')
        cancelled_orders = sum(1 for o in recent_orders if o.status.value == 'CANCELLED')
        pending_orders = sum(1 for o in recent_orders if o.status.value in ['PENDING', 'OPEN'])
        
        buy_orders = sum(1 for o in recent_orders if o.order_side.value == 'BUY')
        sell_orders = sum(1 for o in recent_orders if o.order_side.value == 'SELL')
        
        total_trade_value = sum(float(t.trade_price * t.trade_quantity) for t in recent_trades)
        
        # Calculate success rate
        success_rate = (successful_orders / total_orders * 100) if total_orders > 0 else 0
        
        statistics = {
            "period_days": days,
            "from_date": from_date.isoformat(),
            "total_orders": total_orders,
            "successful_orders": successful_orders,
            "cancelled_orders": cancelled_orders,
            "pending_orders": pending_orders,
            "buy_orders": buy_orders,
            "sell_orders": sell_orders,
            "success_rate": round(success_rate, 2),
            "total_trades": total_trades,
            "total_trade_value": round(total_trade_value, 2),
            "avg_trade_value": round(total_trade_value / total_trades, 2) if total_trades > 0 else 0,
            "last_updated": datetime.now().isoformat()
        }
        
        return statistics
        
    except Exception as e:
        logger.error(f"Error calculating order statistics: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.post("/sandbox/toggle")
async def toggle_sandbox_mode(
    enable_sandbox: bool = Query(True, description="Enable or disable sandbox mode")
):
    """Toggle between sandbox and production mode"""
    try:
        logger.info(f"Toggling sandbox mode to: {enable_sandbox}")
        
        order_service.use_sandbox = enable_sandbox
        
        mode = "sandbox" if enable_sandbox else "production"
        base_url = order_service.base_url
        
        return {
            "success": True,
            "mode": mode,
            "base_url": base_url,
            "message": f"Switched to {mode} mode"
        }
        
    except Exception as e:
        logger.error(f"Error toggling sandbox mode: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.get("/health")
async def orders_health_check():
    """Health check for orders service"""
    try:
        # Check service connectivity
        is_healthy = True
        status = "healthy"
        
        # You could add more checks here like:
        # - Database connectivity for orders table
        # - Upstox API connectivity test
        # - WebSocket broker status
        
        return {
            "service": "orders",
            "status": status,
            "healthy": is_healthy,
            "sandbox_mode": order_service.use_sandbox,
            "base_url": order_service.base_url,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Orders health check failed: {e}")
        return {
            "service": "orders",
            "status": "unhealthy",
            "healthy": False,
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }