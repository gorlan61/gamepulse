"""
services.py — İş mantığı bu dosyada toplanır.
API çağrılarını, fallback mantığını ve veri dönüşümlerini içerir.
Bu sayede route dosyaları temiz kalır (Separation of Concerns).
"""
import logging
import httpx
from app.config import CHEAPSHARK_BASE_URL
from app.schemas import GameDealResponse

# ── Logger kurulumu ────────────────────────────────────────────────────────────
# Her modül kendi logger'ını alır; böylece log'larda kaynak kolayca görülür.
logger = logging.getLogger(__name__)


def _build_fallback(game_name: str, reason: str) -> GameDealResponse:
    """
    API erişilemez ya da sonuç boş dönerse bu fonksiyon çağrılır.
    Hata fırlatmak yerine sahte (demo) veri dönerek uygulamanın
    ayakta kalmasını sağlar — resilience pattern.
    """
    logger.warning("Fallback data returned for '%s'. Reason: %s", game_name, reason)
    return GameDealResponse(
        game_name=game_name,
        store="N/A (Demo)",
        normal_price="59.99",
        sale_price="29.99",
        discount_percent=50.0,
        deal_url="https://www.cheapshark.com",
        is_fallback=True,
        source="fallback",
    )


async def fetch_game_deal(game_name: str) -> GameDealResponse:
    """
    CheapShark API'sini kullanarak oyun fiyatını getirir.

    Akış:
    1. /deals endpoint'ini oyun adıyla sorgula (title parametresi).
    2. Gelen listedeki ilk ve en iyi fırsatı seç.
    3. Herhangi bir ağ/HTTP hatası ya da boş yanıt durumunda
       fallback verisine geç — uygulama asla çökmez.

    Args:
        game_name: Kullanıcının aradığı oyun adı (URL'den decode edilmiş hali).

    Returns:
        GameDealResponse nesnesi.
    """
    params = {
        "title": game_name,  # Oyun adına göre arama
        "pageSize": 5,       # En fazla 5 sonuç (ilk en iyisini alacağız)
        "sortBy": "Savings", # En yüksek indirimi üste getir (CheapShark kabul ettiği enum değeri)
    }

    headers = {
        "User-Agent": "GamePulse/0.1.0 (contact@gamepulse.dev)"
    }

    try:
        # httpx.AsyncClient — async/await ile HTTP çağrısı yapar
        # timeout=10: 10 saniye içinde yanıt gelmezse TimeoutException fırlatır
        async with httpx.AsyncClient(timeout=10, headers=headers) as client:
            logger.info("Fetching deals for game: '%s'", game_name)
            response = await client.get(f"{CHEAPSHARK_BASE_URL}/deals", params=params)

            # 4xx / 5xx yanıtlar için otomatik exception fırlatır
            response.raise_for_status()
            deals = response.json()

    except httpx.TimeoutException:
        return _build_fallback(game_name, "CheapShark API timed out after 10 seconds")

    except httpx.HTTPStatusError as exc:
        return _build_fallback(
            game_name,
            f"CheapShark returned HTTP {exc.response.status_code}"
        )

    except httpx.RequestError as exc:
        # DNS hatası, bağlantı reddedildi, vb. ağ sorunları
        return _build_fallback(game_name, f"Network error: {exc}")

    # ── API'den boş liste döndüyse ─────────────────────────────────────────────
    if not deals:
        return _build_fallback(game_name, "No deals found in CheapShark API response")

    # ── İlk (en iyi) fırsatı seç ve dönüştür ─────────────────────────────────
    best = deals[0]
    logger.info(
        "Deal found for '%s': Store=%s, SalePrice=%s, Discount=%%%.1f",
        game_name,
        best.get("storeName", "Unknown"),
        best.get("salePrice", "N/A"),
        float(best.get("savings", 0)),
    )

    return GameDealResponse(
        game_name=best.get("title", game_name),
        store=best.get("storeName", "Unknown"),
        normal_price=best.get("normalPrice", "N/A"),
        sale_price=best.get("salePrice", "N/A"),
        discount_percent=round(float(best.get("savings", 0)), 2),
        deal_url=f"https://www.cheapshark.com/redirect?dealID={best.get('dealID', '')}",
        is_fallback=False,
        source="CheapShark API",
    )
