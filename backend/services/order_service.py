"""
Order Management Service
Handles order placement, modification, cancellation with Upstox V3 API
Supports both manual trading and automated algo trading
"""
import asyncio
from typing import Optional, List, Dict, Any
from datetime import datetime, timezone, timedelta
import httpx
import json
from decimal import Decimal

from ..models.order_dto import (
    PlaceOrderRequest, ModifyOrderRequest, CancelOrderRequest,
    OrderResponseDTO, OrderDetailsDTO, TradeDTO, OrderBookDTO,
    AlgoOrderRequest, OrderExecutionResult, PortfolioPositionDTO,
    OrderStatus, OrderSide, OrderType, ProductType
)
from ..utils.logging import get_logger
from ..lib.database import db_manager
from ..services.ws_broker import ws_broker

logger = get_logger(__name__)


class UpstoxOrderService:
    """Upstox V3 Order Management Service"""
    
    def __init__(self):
        # Upstox V3 API URLs
        self.base_url_sandbox = "https://api-hft.upstox.com"
        self.base_url_production = "https://api.upstox.com"
        self.use_sandbox = True  # Toggle for sandbox/production
        
        # API endpoints
        self.endpoints = {
            'place_order': '/v2/order/place',
            'modify_order': '/v2/order/modify',
            'cancel_order': '/v2/order/cancel',
            'order_book': '/v2/order/retrieve-all',
            'order_details': '/v2/order/details',
            'order_history': '/v2/order/history',
            'trades': '/v2/order/trades/get-trades-for-day',
            'positions': '/v2/portfolio/long-term-positions',
            'holdings': '/v2/portfolio/short-term-positions'
        }
        
        self.http_client = httpx.AsyncClient(timeout=30.0)
    
    @property
    def base_url(self) -> str:
        """Get base URL based on sandbox/production mode"""
        return self.base_url_sandbox if self.use_sandbox else self.base_url_production
    
    def _get_headers(self, access_token: str) -> Dict[str, str]:
        """Get HTTP headers for API requests"""
        return {
            'Authorization': f'Bearer {access_token}',
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        }
    
    async def place_order(self, order_request: PlaceOrderRequest, access_token: str) -> OrderResponseDTO:
        """Place a new order"""
        try:
            url = f"{self.base_url}{self.endpoints['place_order']}"
            headers = self._get_headers(access_token)
            
            # Prepare request payload
            payload = {
                'quantity': str(order_request.quantity),
                'product': order_request.product_type.value,
                'validity': order_request.validity.value,
                'price': str(order_request.price) if order_request.price else "0",
                'tag': order_request.tag or f"manual_{int(datetime.now().timestamp())}",
                'instrument_token': order_request.instrument_key,
                'order_type': order_request.order_type.value,
                'transaction_type': order_request.order_side.value,
                'disclosed_quantity': str(order_request.disclosed_quantity) if order_request.disclosed_quantity else "0",
                'trigger_price': str(order_request.trigger_price) if order_request.trigger_price else "0",
                'is_amo': False  # After Market Order
            }
            
            logger.info(f"Placing order: {order_request.order_side.value} {order_request.quantity} {order_request.instrument_key}")
            
            response = await self.http_client.post(url, json=payload, headers=headers)
            response.raise_for_status()
            
            data = response.json()
            
            if data.get('status') == 'success':
                order_id = data['data']['order_id']
                
                # Store order in database
                await self._store_order_in_db(order_request, order_id, access_token)
                
                # Broadcast order event
                await self._broadcast_order_event('order_placed', {
                    'order_id': order_id,
                    'instrument_key': order_request.instrument_key,
                    'side': order_request.order_side.value,
                    'quantity': order_request.quantity,
                    'type': order_request.order_type.value
                })
                
                return OrderResponseDTO(
                    order_id=order_id,
                    status='success',
                    message='Order placed successfully'
                )
            else:
                error_msg = data.get('message', 'Unknown error')
                logger.error(f"Order placement failed: {error_msg}")
                return OrderResponseDTO(
                    order_id='',
                    status='error',
                    message=error_msg
                )
                
        except httpx.HTTPError as e:
            logger.error(f"HTTP error placing order: {e}")
            return OrderResponseDTO(
                order_id='',
                status='error',
                message=f'Network error: {str(e)}'
            )
        except Exception as e:
            logger.error(f"Error placing order: {e}")
            return OrderResponseDTO(
                order_id='',
                status='error',
                message=f'Internal error: {str(e)}'
            )
    
    async def modify_order(self, modify_request: ModifyOrderRequest, access_token: str) -> OrderResponseDTO:
        """Modify an existing order"""
        try:
            url = f"{self.base_url}{self.endpoints['modify_order']}"
            headers = self._get_headers(access_token)
            
            # Prepare modification payload
            payload = {
                'order_id': modify_request.order_id,
                'quantity': str(modify_request.quantity) if modify_request.quantity else None,
                'order_type': modify_request.order_type.value if modify_request.order_type else None,
                'validity': modify_request.validity.value if modify_request.validity else None,
                'price': str(modify_request.price) if modify_request.price else None,
                'trigger_price': str(modify_request.trigger_price) if modify_request.trigger_price else None,
                'disclosed_quantity': str(modify_request.disclosed_quantity) if modify_request.disclosed_quantity else None
            }
            
            # Remove None values
            payload = {k: v for k, v in payload.items() if v is not None}
            
            logger.info(f"Modifying order {modify_request.order_id}")
            
            response = await self.http_client.put(url, json=payload, headers=headers)
            response.raise_for_status()
            
            data = response.json()
            
            if data.get('status') == 'success':
                await self._broadcast_order_event('order_modified', {
                    'order_id': modify_request.order_id,
                    'changes': payload
                })
                
                return OrderResponseDTO(
                    order_id=modify_request.order_id,
                    status='success',
                    message='Order modified successfully'
                )
            else:
                error_msg = data.get('message', 'Unknown error')
                return OrderResponseDTO(
                    order_id=modify_request.order_id,
                    status='error',
                    message=error_msg
                )
                
        except Exception as e:
            logger.error(f"Error modifying order: {e}")
            return OrderResponseDTO(
                order_id=modify_request.order_id,
                status='error',
                message=str(e)
            )
    
    async def cancel_order(self, cancel_request: CancelOrderRequest, access_token: str) -> OrderResponseDTO:
        """Cancel an existing order"""
        try:
            url = f"{self.base_url}{self.endpoints['cancel_order']}"
            headers = self._get_headers(access_token)
            
            payload = {'order_id': cancel_request.order_id}
            
            logger.info(f"Cancelling order {cancel_request.order_id}")
            
            response = await self.http_client.delete(url, json=payload, headers=headers)
            response.raise_for_status()
            
            data = response.json()
            
            if data.get('status') == 'success':
                await self._broadcast_order_event('order_cancelled', {
                    'order_id': cancel_request.order_id
                })
                
                return OrderResponseDTO(
                    order_id=cancel_request.order_id,
                    status='success',
                    message='Order cancelled successfully'
                )
            else:
                return OrderResponseDTO(
                    order_id=cancel_request.order_id,
                    status='error',
                    message=data.get('message', 'Unknown error')
                )
                
        except Exception as e:
            logger.error(f"Error cancelling order: {e}")
            return OrderResponseDTO(
                order_id=cancel_request.order_id,
                status='error',
                message=str(e)
            )
    
    async def get_order_book(self, access_token: str) -> OrderBookDTO:
        """Get all orders"""
        try:
            url = f"{self.base_url}{self.endpoints['order_book']}"
            headers = self._get_headers(access_token)
            
            response = await self.http_client.get(url, headers=headers)
            response.raise_for_status()
            
            data = response.json()
            
            if data.get('status') == 'success':
                orders = []
                order_data = data.get('data', [])
                
                for order in order_data:
                    try:
                        order_dto = self._convert_to_order_dto(order)
                        orders.append(order_dto)
                    except Exception as e:
                        logger.warning(f"Failed to convert order: {e}")
                        continue
                
                # Calculate summary metrics
                pending_orders = sum(1 for o in orders if o.status in [OrderStatus.PENDING, OrderStatus.OPEN])
                completed_orders = sum(1 for o in orders if o.status == OrderStatus.COMPLETE)
                cancelled_orders = sum(1 for o in orders if o.status == OrderStatus.CANCELLED)
                
                total_buy_value = sum(
                    Decimal(str(o.quantity * (o.price or 0))) 
                    for o in orders if o.order_side == OrderSide.BUY
                )
                total_sell_value = sum(
                    Decimal(str(o.quantity * (o.price or 0))) 
                    for o in orders if o.order_side == OrderSide.SELL
                )
                
                return OrderBookDTO(
                    orders=orders,
                    total_orders=len(orders),
                    pending_orders=pending_orders,
                    completed_orders=completed_orders,
                    cancelled_orders=cancelled_orders,
                    total_buy_value=total_buy_value,
                    total_sell_value=total_sell_value
                )
            else:
                logger.error(f"Failed to fetch order book: {data.get('message')}")
                return OrderBookDTO()
                
        except Exception as e:
            logger.error(f"Error fetching order book: {e}")
            return OrderBookDTO()
    
    async def get_order_details(self, order_id: str, access_token: str) -> Optional[OrderDetailsDTO]:
        """Get details of a specific order"""
        try:
            url = f"{self.base_url}{self.endpoints['order_details']}"
            headers = self._get_headers(access_token)
            
            params = {'order_id': order_id}
            response = await self.http_client.get(url, headers=headers, params=params)
            response.raise_for_status()
            
            data = response.json()
            
            if data.get('status') == 'success' and data.get('data'):
                return self._convert_to_order_dto(data['data'])
            else:
                return None
                
        except Exception as e:
            logger.error(f"Error fetching order details: {e}")
            return None
    
    async def get_trades(self, access_token: str) -> List[TradeDTO]:
        """Get all trades for the day"""
        try:
            url = f"{self.base_url}{self.endpoints['trades']}"
            headers = self._get_headers(access_token)
            
            response = await self.http_client.get(url, headers=headers)
            response.raise_for_status()
            
            data = response.json()
            
            if data.get('status') == 'success':
                trades = []
                for trade in data.get('data', []):
                    try:
                        trade_dto = self._convert_to_trade_dto(trade)
                        trades.append(trade_dto)
                    except Exception as e:
                        logger.warning(f"Failed to convert trade: {e}")
                        continue
                
                return trades
            else:
                return []
                
        except Exception as e:
            logger.error(f"Error fetching trades: {e}")
            return []
    
    def _convert_to_order_dto(self, order_data: Dict[str, Any]) -> OrderDetailsDTO:
        """Convert Upstox order data to OrderDetailsDTO"""
        return OrderDetailsDTO(
            order_id=order_data.get('order_id', ''),
            exchange_order_id=order_data.get('exchange_order_id'),
            parent_order_id=order_data.get('parent_order_id'),
            instrument_key=order_data.get('instrument_token', ''),
            symbol=order_data.get('trading_symbol', ''),
            product_type=ProductType(order_data.get('product', 'D')),
            order_type=OrderType(order_data.get('order_type', 'MARKET')),
            order_side=OrderSide(order_data.get('transaction_type', 'BUY')),
            validity=order_data.get('validity', 'DAY'),
            quantity=int(order_data.get('quantity', 0)),
            filled_quantity=int(order_data.get('filled_quantity', 0)),
            pending_quantity=int(order_data.get('pending_quantity', 0)),
            price=Decimal(str(order_data.get('price', 0))) if order_data.get('price') else None,
            trigger_price=Decimal(str(order_data.get('trigger_price', 0))) if order_data.get('trigger_price') else None,
            average_price=Decimal(str(order_data.get('average_price', 0))) if order_data.get('average_price') else None,
            disclosed_quantity=order_data.get('disclosed_quantity'),
            status=OrderStatus(order_data.get('status', 'PENDING')),
            status_message=order_data.get('status_message'),
            order_timestamp=datetime.fromisoformat(order_data.get('order_timestamp', datetime.now().isoformat())),
            exchange_timestamp=datetime.fromisoformat(order_data.get('exchange_timestamp')) if order_data.get('exchange_timestamp') else None,
            tag=order_data.get('tag')
        )
    
    def _convert_to_trade_dto(self, trade_data: Dict[str, Any]) -> TradeDTO:
        """Convert Upstox trade data to TradeDTO"""
        return TradeDTO(
            trade_id=trade_data.get('trade_id', ''),
            order_id=trade_data.get('order_id', ''),
            exchange_order_id=trade_data.get('exchange_order_id'),
            instrument_key=trade_data.get('instrument_token', ''),
            symbol=trade_data.get('trading_symbol', ''),
            trade_price=Decimal(str(trade_data.get('trade_price', 0))),
            trade_quantity=int(trade_data.get('trade_quantity', 0)),
            trade_timestamp=datetime.fromisoformat(trade_data.get('trade_timestamp', datetime.now().isoformat())),
            exchange=trade_data.get('exchange', ''),
            order_side=OrderSide(trade_data.get('transaction_type', 'BUY'))
        )
    
    async def _store_order_in_db(self, order_request: PlaceOrderRequest, order_id: str, access_token: str):
        """Store order details in database for tracking"""
        try:
            async with db_manager.get_connection() as conn:
                await conn.execute("""
                    INSERT INTO orders 
                    (order_id, instrument_key, symbol, order_side, order_type, product_type, 
                     quantity, price, trigger_price, validity, tag, status, created_at)
                    VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13)
                    ON CONFLICT (order_id) DO UPDATE SET
                        status = EXCLUDED.status,
                        updated_at = CURRENT_TIMESTAMP
                """, 
                order_id, order_request.instrument_key, 
                order_request.instrument_key.split('|')[-1] if '|' in order_request.instrument_key else order_request.instrument_key,
                order_request.order_side.value, order_request.order_type.value, order_request.product_type.value,
                order_request.quantity, float(order_request.price) if order_request.price else None,
                float(order_request.trigger_price) if order_request.trigger_price else None,
                order_request.validity.value, order_request.tag, 'PENDING', datetime.now(timezone.utc)
                )
        except Exception as e:
            logger.error(f"Failed to store order in DB: {e}")
    
    async def _broadcast_order_event(self, event_type: str, data: Dict[str, Any]):
        """Broadcast order events via WebSocket"""
        try:
            message = {
                'type': 'order_event',
                'event': event_type,
                'data': data,
                'timestamp': datetime.now(timezone.utc).isoformat()
            }
            await ws_broker.broadcast(message)
        except Exception as e:
            logger.error(f"Failed to broadcast order event: {e}")


class AlgoTradingOrderService:
    """Service for algorithmic trading order management"""
    
    def __init__(self, order_service: UpstoxOrderService):
        self.order_service = order_service
        self.execution_queue = asyncio.Queue()
        self.running = False
        
    async def execute_algo_order(self, algo_request: AlgoOrderRequest, access_token: str) -> OrderExecutionResult:
        """Execute an order from algorithmic trading system"""
        try:
            # Convert algo request to standard order request
            order_request = PlaceOrderRequest(
                instrument_key=algo_request.instrument_key,
                quantity=algo_request.quantity,
                price=algo_request.price,
                order_type=algo_request.order_type,
                order_side=algo_request.order_side,
                product_type=algo_request.product_type,
                validity=algo_request.validity,
                tag=f"algo_{algo_request.strategy_id}_{algo_request.signal_id}"
            )
            
            # Execute the order
            response = await self.order_service.place_order(order_request, access_token)
            
            # Store algo execution details
            await self._store_algo_execution(algo_request, response)
            
            execution_status = 'SUCCESS' if response.status == 'success' else 'FAILED'
            
            return OrderExecutionResult(
                order_request=algo_request,
                order_response=response,
                execution_status=execution_status,
                error_message=response.message if response.status != 'success' else None
            )
            
        except Exception as e:
            logger.error(f"Error executing algo order: {e}")
            return OrderExecutionResult(
                order_request=algo_request,
                execution_status='FAILED',
                error_message=str(e)
            )
    
    async def _store_algo_execution(self, algo_request: AlgoOrderRequest, response: OrderResponseDTO):
        """Store algorithmic order execution details"""
        try:
            async with db_manager.get_connection() as conn:
                await conn.execute("""
                    INSERT INTO algo_orders 
                    (order_id, strategy_id, signal_id, instrument_key, confidence_score, 
                     risk_level, execution_status, error_message, metadata, created_at)
                    VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10)
                """,
                response.order_id, algo_request.strategy_id, algo_request.signal_id,
                algo_request.instrument_key, algo_request.confidence_score,
                algo_request.risk_level, response.status, response.message,
                json.dumps(algo_request.metadata), algo_request.created_at
                )
        except Exception as e:
            logger.error(f"Failed to store algo execution: {e}")


# Global instances
order_service = UpstoxOrderService()
algo_order_service = AlgoTradingOrderService(order_service)