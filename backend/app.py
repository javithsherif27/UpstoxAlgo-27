from fastapi import FastAPI, Request, Response
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
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
    expose_headers=["*"],
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

handler = Mangum(app)
