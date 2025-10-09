from fastapi import FastAPI, Request, Response, WebSocket, WebSocketDisconnect
import asyncio
from fastapi.middleware.cors import CORSMiddleware
from mangum import Mangum
from .routers import session, upstox, instruments, market_data
from .routers import market as stream_market
from .routers import portfolio as portfolio_router
from .utils.logging import configure_logging, get_logger
import os
from dotenv import load_dotenv

# Load environment variables from .env.local if it exists
if os.path.exists(".env.local"):
    load_dotenv(".env.local")
    logger = get_logger(__name__)
    logger.info("Loaded LocalStack environment configuration")
elif os.path.exists(".env.production"):
    load_dotenv(".env.production")
    logger = get_logger(__name__)
    logger.info("Loaded production environment configuration")

configure_logging()
logger = get_logger(__name__)

app = FastAPI(title="Algo Trading App API")

# Database startup and shutdown handlers
@app.on_event("startup")
async def startup_event():
    """Initialize database on startup"""
    try:
        from .lib.database import init_database
        await init_database()
        logger.info("Database initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")
        raise

@app.on_event("shutdown") 
async def shutdown_event():
    """Clean up database connections on shutdown"""
    try:
        from .lib.database import close_database
        await close_database()
        logger.info("Database connections closed")
    except Exception as e:
        logger.error(f"Error closing database connections: {e}")

# More permissive CORS for development
ALLOWED_ORIGINS = [
    "http://localhost:5173",
    "http://localhost:5174", 
    "http://127.0.0.1:5173",
    "http://127.0.0.1:5174",
    "http://localhost:3000",
    "http://127.0.0.1:3000"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],
    allow_headers=["*"],
    expose_headers=["*"],
    max_age=3600,  # Cache preflight requests for 1 hour
)

# @app.middleware("http")
# async def add_correlation_id(request: Request, call_next):
#     import uuid
#     cid = request.headers.get("X-Correlation-ID", str(uuid.uuid4()))
#     request.state.correlation_id = cid
#     response: Response = await call_next(request)
#     response.headers["X-Correlation-ID"] = cid
#     return response

@app.get("/health")
async def health_check():
    """Health check endpoint - works without authentication"""
    return {"status": "healthy", "message": "Backend is running successfully"}

app.include_router(session.router, prefix="/api/session", tags=["session"])
app.include_router(upstox.router, prefix="/api/upstox", tags=["upstox"])
app.include_router(instruments.router, prefix="/api", tags=["instruments"])
app.include_router(market_data.router, prefix="/api", tags=["market-data"])
app.include_router(stream_market.router, tags=["stream"])
app.include_router(portfolio_router.router, tags=["portfolio"])

# Orders management
from .routers import orders
app.include_router(orders.router)

# Trading-grade data management
from .routers import trading_data
app.include_router(trading_data.router, tags=["trading"])

handler = Mangum(app)

# Real-time WebSocket endpoint for UI
from .services.ws_broker import ws_broker

@app.websocket("/ws/stream")
async def ws_stream(websocket: WebSocket):
    await websocket.accept()
    await ws_broker.add(websocket)
    try:
        # Basic echo/ping loop; break cleanly on disconnect
        while True:
            msg = await websocket.receive_text()
            if msg == "ping":
                await websocket.send_text("pong")
    except WebSocketDisconnect:
        pass
    except Exception:
        pass
    finally:
        await ws_broker.remove(websocket)
