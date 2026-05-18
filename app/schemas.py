"""
schemas.py — Pydantic modelleri (request/response şemaları).
Pydantic, FastAPI'nin veri doğrulama katmanıdır.
Her endpoint'in döneceği JSON yapısı burada tanımlanır.
"""
from pydantic import BaseModel
from typing import Optional


class StatusResponse(BaseModel):
    """GET /status endpoint'inin döneceği şema."""
    status: str
    version: str
    environment: str
    message: str


class GameDealResponse(BaseModel):
    """GET /game/{game_name} endpoint'inin döneceği şema."""
    game_name: str                   # İstekte gelen oyun adı
    store: str                       # Hangi mağaza (Steam, GOG vb.)
    normal_price: str                # İndirim öncesi fiyat (USD)
    sale_price: str                  # İndirimli fiyat (USD)
    discount_percent: float          # İndirim yüzdesi
    deal_url: str                    # Doğrudan alım linki
    is_fallback: bool                # True ise API'den değil, varsayılan veri döndü
    source: Optional[str] = None     # Veri kaynağı (API adı)
