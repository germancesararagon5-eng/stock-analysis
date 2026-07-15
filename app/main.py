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
from app.routers import admin_router, alerts_router, analysis_router, config_router, debug_router, ml_router, options_router
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
    if broker_manager.active_broker is None:
        logger.info("Sin broker en DB — usando yahoo_finance por defecto")
        broker_manager.switch(name="yahoo_finance")
    yield


app = FastAPI(
    title="Stock Analysis Multi-Broker API",
    description="API de análisis técnico multi-broker con soporte para Yahoo Finance, Binance (cripto) e Interactive Brokers. "
    "Estrategias: Scalping, Swing, Momentum, Mean Reversion, Breakout, Market Structure. "
    "Incluye alertas programadas, predictor automático, simulación de trading, dataset ML y gateway WhatsApp.",
    summary="API de análisis técnico de acciones y cripto con múltiples estrategias",
    version="2.4.0",
    contact={"name": "Stock Analysis", "url": "https://github.com/anomalyco/stock-analysis"},
    license_info={"name": "MIT", "identifier": "MIT"},
    openapi_tags=[
        {"name": "config", "description": "Configuración y cambio de broker activo"},
        {"name": "analysis", "description": "Análisis técnico, charts, top-ranking y órdenes simuladas"},
        {"name": "alerts", "description": "Alertas programadas con notificación WhatsApp"},
        {"name": "debug", "description": "Depuración en vivo: requests, errores, eventos de broker y estrategia"},
        {"name": "options", "description": "Configuración del background analyzer, predicciones, trading simulator y WhatsApp"},
        {"name": "ml", "description": "Exportación de dataset ML y estadísticas de entrenamiento"},
        {"name": "admin", "description": "Administración de servicios de infraestructura: estado de API, DB, Redis, WhatsApp, BG Analyzer, ML y Broker"},
    ],
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

app.include_router(config_router.router)
app.include_router(analysis_router.router)
app.include_router(alerts_router.router)
app.include_router(debug_router.router)
app.include_router(options_router.router)
app.include_router(ml_router.router)
app.include_router(admin_router.router)

app.mount("/static", StaticFiles(directory=Path(__file__).parent / "static"), name="static")


@app.get("/", include_in_schema=False)
def index():
    return FileResponse(Path(__file__).parent / "static" / "index.html")


@app.websocket("/api/ws")
async def websocket_endpoint(ws: WebSocket):
    """Conexión WebSocket para notificaciones en vivo del background analyzer."""
    await ws_manager.connect(ws)
    try:
        while True:
            await ws.receive_text()
    except Exception:
        pass
    finally:
        ws_manager.disconnect(ws)


@app.get("/health", summary="Health check del sistema", tags=["config"])
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
