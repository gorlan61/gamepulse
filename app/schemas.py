"""
schemas.py — Pydantic modelleri (request/response şemaları).
Pydantic, FastAPI'nin veri doğrulama katmanıdır.
Her endpoint'in döneceği JSON yapısı burada tanımlanır.
"""
from enum import Enum
from pydantic import BaseModel, Field
from typing import Optional


# ─────────────────────────────────────────────────────────────────────────────
# Ortak Enumlar
# ─────────────────────────────────────────────────────────────────────────────

class PerformanceTier(str, Enum):
    """
    GPU performans katmanları.
    str mixin'i sayesinde JSON'da "Low"/"High" gibi okunabilir değerler üretir.
    """
    LOW    = "Low"
    MEDIUM = "Medium"
    HIGH   = "High"
    ULTRA  = "Ultra"


# ─────────────────────────────────────────────────────────────────────────────
# Health Check
# ─────────────────────────────────────────────────────────────────────────────

class StatusResponse(BaseModel):
    """GET /status endpoint'inin döneceği şema."""
    status: str
    version: str
    environment: str
    message: str


# ─────────────────────────────────────────────────────────────────────────────
# Oyun Fiyat Verisi
# ─────────────────────────────────────────────────────────────────────────────

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


# ─────────────────────────────────────────────────────────────────────────────
# Donanım Performans Analizi
# ─────────────────────────────────────────────────────────────────────────────

class PerformanceReport(BaseModel):
    """
    Tek bir GPU için üretilen performans analiz raporu.
    analyzer.py'deki kural motoru tarafından doldurulur.
    """
    gpu_model: str = Field(
        description="Kullanıcının girdiği ham GPU model metni"
    )
    estimated_performance: PerformanceTier = Field(
        description="Tahmini performans katmanı: Low / Medium / High / Ultra"
    )
    estimated_fps: int = Field(
        description="Tahmini FPS değeri (kural motorunun hesapladığı aralık içinde)"
    )
    fps_range: str = Field(
        description="Tespit edilen GPU'nun beklenen FPS aralığı"
    )
    matched_gpu_label: str = Field(
        description="Kural tablosundaki eşleşen GPU etiket adı"
    )
    analysis_note: str = Field(
        description="Performans katmanına göre kullanıcıya yönelik açıklama"
    )


# ─────────────────────────────────────────────────────────────────────────────
# Birleşik Analiz Yanıtı (Fiyat + Performans)
# ─────────────────────────────────────────────────────────────────────────────

class GameAnalysisResponse(BaseModel):
    """
    GET /analyze/{game_name}?gpu_model=... endpoint'inin döneceği şema.
    Hem oyun fiyat bilgisini hem de donanım performans raporunu içerir.
    """
    # ── Oyun Fiyat Verileri ──────────────────────────────────────────────────
    game_name: str
    store: str
    normal_price: str
    sale_price: str
    discount_percent: float
    deal_url: str
    is_fallback: bool
    source: Optional[str] = None

    # ── Donanım Performans Raporu ─────────────────────────────────────────────
    performance: PerformanceReport = Field(
        description="GPU analizinden üretilen performans raporu"
    )

    # ── Önbellek Durumu ───────────────────────────────────────────────────────
    is_cached: bool = Field(
        default=False,
        description="True ise bu sonuç dış API çağrısı olmadan önbellekten (cache) getirilmiştir"
    )
