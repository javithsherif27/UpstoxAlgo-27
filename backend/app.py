from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from mangum import Mangum
from .routers import session, upstox, instruments, market_data
from .utils.logging import configure_logging, get_logger
import os

configure_logging()
logger = get_logger(__name__)

app = FastAPI(title="Algo Trading App API")

ALLOWED_ORIGIN = os.getenv("ALLOWED_ORIGIN", "http://localhost:5173")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[ALLOWED_ORIGIN],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.middleware("http")
async def add_correlation_id(request: Request, call_next):
    import uuid
    cid = request.headers.get("X-Correlation-ID", str(uuid.uuid4()))
    request.state.correlation_id = cid
    response: Response = await call_next(request)
    response.headers["X-Correlation-ID"] = cid
    return response

app.include_router(session.router, prefix="/api/session", tags=["session"])
app.include_router(upstox.router, prefix="/api/upstox", tags=["upstox"])
app.include_router(instruments.router, prefix="/api", tags=["instruments"])
app.include_router(market_data.router, prefix="/api", tags=["market-data"])

handler = Mangum(app)
