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

logger = logging.getLogger(__name__)

# ── Router oluştur ─────────────────────────────────────────────────────────────
# prefix eklemek isteğe bağlı; şimdilik root level tutuyoruz
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
    Production'da bu endpoint genelde /health veya /healthz olarak adlandırılır.
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
        "mevcut en iyi fiyat + indirim bilgisini döndürür. "
        "API erişilemez olduğunda uygulama çökmez; "
        "`is_fallback: true` ile sahte veri döner."
    ),
    tags=["Games"],
)
async def get_game_deal(game_name: str) -> GameDealResponse:
    """
    Path parametresi olarak oyun adı alır.
    Örnek: GET /game/Cyberpunk%202077
    Boşluklu isimler için URL encoding kullanın (%20 ya da +).
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

    Örnek istek:
        GET /analyze/Cyberpunk%202077?gpu_model=RTX+4060
    """
    logger.info(
        "Analyze request — game: '%s', gpu: '%s'",
        game_name, gpu_model
    )

    # 1. Oyun fiyat verisini al (mevcut servis katmanını yeniden kullan)
    deal = await fetch_game_deal(game_name)

    # 2. GPU performans analizini yap (senkron kural motoru)
    perf = analyze_gpu(gpu_model)

    # 3. Arama geçmişini veritabanına kaydet (Resilience: DB hatası servisi çökertmez)
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

    # 4. İki veri kaynağını birleştir ve tek yanıt olarak dön
    return GameAnalysisResponse(
        game_name=deal.game_name,
        store=deal.store,
        normal_price=deal.normal_price,
        sale_price=deal.sale_price,
        discount_percent=deal.discount_percent,
        deal_url=deal.deal_url,
        is_fallback=deal.is_fallback,
        source=deal.source,
        performance=perf,
    )
