"""
main.py — FastAPI uygulama giriş noktası.
Bu dosya:
  - Uygulamayı oluşturur ve yapılandırır
  - Logging ayarlarını yapar
  - Router'ı bağlar
  - Startup/shutdown event'lerini yönetir
"""
import logging
import sys
from contextlib import asynccontextmanager

# Windows: stdout'u UTF-8'e zorla
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from app.routes import router
from app.config import APP_VERSION, APP_ENV

# ── Logging yapılandırması ─────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(levelname)-8s %(asctime)s | %(name)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    stream=sys.stdout,
)
logger = logging.getLogger("gamepulse")


# ── Lifespan (startup / shutdown) ─────────────────────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    # >>> STARTUP
    logger.info("=" * 50)
    logger.info("  GamePulse v%s starting up  [env: %s]", APP_VERSION, APP_ENV)
    logger.info("  Docs  -> http://127.0.0.1:8000/docs")
    logger.info("  ReDoc -> http://127.0.0.1:8000/redoc")
    logger.info("=" * 50)

    # ── Veritabanı Tablolarını Oluştur ──────────────────────────────────────────
    logger.info("Initializing database tables...")
    try:
        from app.database import Base, engine
        import app.models  # Modelleri Base'e kaydetmek için zorunlu
        Base.metadata.create_all(bind=engine)
        logger.info("Database tables initialized successfully.")
    except Exception as exc:
        logger.critical("Database initialization failed: %s", exc)

    # ── Önbelleği (Cache) Başlat ───────────────────────────────────────────────
    logger.info("Initializing Cache Store...")
    try:
        from app.cache import init_cache
        init_cache()
    except Exception as exc:
        logger.error("Failed to initialize cache: %s", exc)

    yield

    # >>> SHUTDOWN
    logger.info("GamePulse shutting down. Goodbye!")


# ── FastAPI uygulaması ─────────────────────────────────────────────────────────
app = FastAPI(
    title="GamePulse API",
    description=(
        "🎮 **GamePulse** — Gerçek zamanlı oyun fiyat ve indirim takip servisi.\n\n"
        "CheapShark API entegrasyonu ile Steam, GOG, Epic ve daha fazlasından "
        "en güncel fırsatları getirir."
    ),
    version=APP_VERSION,
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# Router'ı uygulamaya bağla (Tüm endpoint'ler buradan gelir)
app.include_router(router)

# ── Frontend (UI) Yapılandırması ───────────────────────────────────────────────
# Statik dosyaları (CSS, JS, Resimler) sunmak için
app.mount("/static", StaticFiles(directory="app/static"), name="static")

# HTML şablonları için Jinja2 yapılandırması
templates = Jinja2Templates(directory="app/templates")

@app.get("/", response_class=HTMLResponse, tags=["UI"])
async def serve_ui(request: Request):
    """
    Ana sayfayı (Web Arayüzü) render eder.
    Kullanıcı doğrudan tarayıcıdan geldiğinde çalışır.
    """
    return templates.TemplateResponse("index.html", {"request": request})

# ── Global hata yakalayıcı ─────────────────────────────────────────────────────
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    logger.error("Unhandled exception on %s: %s", request.url, exc, exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error. Please try again later."},
    )
