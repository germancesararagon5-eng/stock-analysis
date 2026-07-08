import logging
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, WebSocket
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.config import settings
from app.core.broker_manager import BrokerManager
from app.core.debug import DebugMiddleware
from app.database import init_db
from app.routers import alerts_router, analysis_router, auth_router, config_router, debug_router, options_router
from app.services.ws_manager import ws_manager

logging.basicConfig(
    level=getattr(logging, settings.log_level.upper(), logging.INFO),
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)

broker_manager = BrokerManager()


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Inicializando base de datos...")
    init_db()
    logger.info("Cargando configuración de bróker desde DB...")
    from app.database import SessionLocal

    db = SessionLocal()
    try:
        broker_manager.load_from_db(db)
    finally:
        db.close()
    yield


app = FastAPI(
    title="Stock Analysis Multi-Broker API",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins.split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(DebugMiddleware)

app.include_router(auth_router.router)
app.include_router(config_router.router)
app.include_router(analysis_router.router)
app.include_router(alerts_router.router)
app.include_router(debug_router.router)
app.include_router(options_router.router)

app.mount("/static", StaticFiles(directory=Path(__file__).parent / "static"), name="static")


@app.get("/")
def index():
    return FileResponse(Path(__file__).parent / "static" / "index.html")


@app.websocket("/api/ws")
async def websocket_endpoint(ws: WebSocket):
    await ws_manager.connect(ws)
    try:
        while True:
            await ws.receive_text()
    except Exception:
        pass
    finally:
        ws_manager.disconnect(ws)


@app.get("/health")
def health():
    active = broker_manager.active_name
    connected = False
    if active:
        try:
            connected = broker_manager.get_broker().is_connected
        except RuntimeError:
            pass
    return {
        "status": "ok",
        "active_broker": active,
        "broker_connected": connected,
    }
