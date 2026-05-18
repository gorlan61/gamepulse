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

# Windows: stdout'u UTF-8'e zorla (CP1254 gibi dar codec'lerde unicode hatasını önler)
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

from fastapi import FastAPI
from fastapi.responses import JSONResponse
from app.routes import router
from app.config import APP_VERSION, APP_ENV


# ── Logging yapılandırması ─────────────────────────────────────────────────────
# Format: [LEVEL] tarih saat | modül | mesaj
logging.basicConfig(
    level=logging.INFO,
    format="%(levelname)-8s %(asctime)s | %(name)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    stream=sys.stdout,         # Docker log collector için stdout'a yaz
)
logger = logging.getLogger("gamepulse")


# ── Lifespan (startup / shutdown) ─────────────────────────────────────────────
# FastAPI'nin modern lifecycle yönetimi; eski @app.on_event yerine kullanılır.
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
    # Swagger UI'da daha temiz bir görünüm için
    docs_url="/docs",
    redoc_url="/redoc",
)

# Router'ı uygulamaya bağla
app.include_router(router)


# ── Global hata yakalayıcı ─────────────────────────────────────────────────────
# Beklenmeyen tüm Exception'ları yakalar; kullanıcıya 500 döner ama sunucu düşmez.
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    logger.error("Unhandled exception on %s: %s", request.url, exc, exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error. Please try again later."},
    )
