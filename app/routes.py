"""
routes.py — HTTP endpoint'leri burada tanımlanır.
FastAPI Router kullanmak, endpoint'leri modüler tutar;
ileride yeni router'lar eklemek kolaylaşır.
"""
import logging
from fastapi import APIRouter
from app.config import APP_VERSION, APP_ENV
from app.schemas import StatusResponse, GameDealResponse
from app.services import fetch_game_deal

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
