"""
routes.py — HTTP endpoint'leri burada tanımlanır.
FastAPI Router kullanmak, endpoint'leri modüler tutar;
ileride yeni router'lar eklemek kolaylaşır.
"""
import logging
from fastapi import APIRouter, Query, Depends
from sqlalchemy.orm import Session
from app.config import APP_VERSION, APP_ENV
from app.schemas import StatusResponse, GameDealResponse, GameAnalysisResponse
from app.services import fetch_game_deal
from app.analyzer import analyze_gpu
from app.database import get_db
from app.models import SearchHistory
from app.cache import get_cache, set_cache

logger = logging.getLogger(__name__)

# ── Router oluştur ─────────────────────────────────────────────────────────────
router = APIRouter()


# ── 1. /status ─────────────────────────────────────────────────────────────────
@router.get(
    "/status",
    response_model=StatusResponse,
    summary="Sistem durumunu kontrol eder",
    description=(
        "Servisin ayakta olduğunu doğrular. "
        "Load balancer ve monitoring araçlarının (Prometheus, UptimeRobot vb.) "
        "çağırdığı health-check endpoint'idir."
    ),
    tags=["Health"],
)
async def get_status() -> StatusResponse:
    """
    Basit bir sağlık kontrolü endpoint'i.
    """
    logger.info("Status endpoint called")
    return StatusResponse(
        status="ok",
        version=APP_VERSION,
        environment=APP_ENV,
        message="GamePulse is up and running 🎮",
    )


# ── 2. /game/{game_name} ───────────────────────────────────────────────────────
@router.get(
    "/game/{game_name}",
    response_model=GameDealResponse,
    summary="Oyun fiyat ve indirim bilgisini getirir",
    description=(
        "Verilen oyun adı için CheapShark API'sine istek atar ve "
        "mevcut en iyi fiyat + indirim bilgisini döndürür."
    ),
    tags=["Games"],
)
async def get_game_deal(game_name: str) -> GameDealResponse:
    """
    Path parametresi olarak oyun adı alır.
    """
    logger.info("Game deal request received for: '%s'", game_name)
    return await fetch_game_deal(game_name)


# ── 3. /analyze/{game_name} ────────────────────────────────────────────────────
@router.get(
    "/analyze/{game_name}",
    response_model=GameAnalysisResponse,
    summary="Oyun fiyatı + GPU performans analizi",
    description=(
        "Verilen oyun için fiyat bilgisini CheapShark API'sinden çeker ve "
        "kullanıcının GPU modeline göre tahmini performans raporu oluşturur. "
        "Sonuç; fiyat verisi ve donanım analizi (FPS, tier, öneri) içerir."
    ),
    tags=["Analyze"],
)
async def analyze_game(
    game_name: str,
    gpu_model: str = Query(
        ...,
        description="Ekran kartı model adı. Örn: RTX 4060, RX 6700 XT, GTX 1650",
        min_length=2,
        max_length=80,
        example="RTX 4060",
    ),
    db: Session = Depends(get_db),
) -> GameAnalysisResponse:
    """
    Path param: oyun adı (URL-encoded boşluk desteklenir).
    Query param: gpu_model — kullanıcının ekran kartı.
    """
    # Key normalizasyonu
    normalized_game = game_name.lower().strip()
    normalized_gpu = gpu_model.lower().strip()
    cache_key = f"analyze:{normalized_game}:{normalized_gpu}"

    logger.info(
        "Analyze request — game: '%s' (normalized: '%s'), gpu: '%s' (normalized: '%s')",
        game_name, normalized_game, gpu_model, normalized_gpu
    )

    # 1. Önbelleği (Cache) Kontrol Et
    cached_data = get_cache(cache_key)
    if cached_data:
        logger.info("Serving response from cache for key '%s'...", cache_key)
        cached_data["is_cached"] = True
        return GameAnalysisResponse(**cached_data)

    logger.info("Cache miss for key '%s'. Fetching new data...", cache_key)

    # 2. Oyun fiyat verisini al
    deal = await fetch_game_deal(game_name)

    # 3. GPU performans analizini yap
    perf = analyze_gpu(gpu_model)

    # 4. Arama geçmişini veritabanına kaydet (Resilience: DB hatası servisi çökertmez)
    try:
        db_history = SearchHistory(
            game_name=deal.game_name,
            gpu_model=perf.gpu_model,
            estimated_performance=perf.estimated_performance.value,
            estimated_fps=perf.estimated_fps,
        )
        db.add(db_history)
        db.commit()
        db.refresh(db_history)
        logger.info("Search history saved to database: id=%d", db_history.id)
    except Exception as exc:
        db.rollback()
        logger.error("Failed to save search history to database: %s", exc)

    # 5. Birleşik yanıt objesini oluştur
    response_obj = GameAnalysisResponse(
        game_name=deal.game_name,
        store=deal.store,
        normal_price=deal.normal_price,
        sale_price=deal.sale_price,
        discount_percent=deal.discount_percent,
        deal_url=deal.deal_url,
        is_fallback=deal.is_fallback,
        source=deal.source,
        performance=perf,
        is_cached=False,
    )

    # 6. Yanıtı 1 saatliğine önbelleğe (Cache) kaydet
    set_cache(cache_key, response_obj.model_dump(), ttl_seconds=3600)

    return response_obj
