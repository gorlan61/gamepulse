"""
analyzer.py — Donanım Performans Analiz Motoru.

Kullanıcının girdiği GPU model metnini analiz ederek oyun için
tahmini performans seviyesi (Low/Medium/High/Ultra) ve FPS aralığı üretir.

Tasarım: Kural tabanlı (rule-based) yaklaşım.
  - GPU model metni normalleştirilir (küçük harf, gereksiz boşluk temizlenir).
  - NVIDIA ve AMD için hiyerarşik kural tabloları tanımlanır.
  - İlk eşleşen kural, performans katmanını belirler.
  - Bilinmeyen GPU için güvenli varsayılan (Medium) döner.
"""
import re
import random
import logging
from app.schemas import PerformanceTier, PerformanceReport

logger = logging.getLogger(__name__)

# ── GPU Kural Tablosu ──────────────────────────────────────────────────────────
# Her satır: (regex_pattern, PerformanceTier, fps_min, fps_max, açıklama)
# Tablolar EN GÜÇLÜDEN EN ZAYIFA doğru sıralıdır; ilk eşleşme kazanır.
# ──────────────────────────────────────────────────────────────────────────────
_GPU_RULES: list[tuple[str, PerformanceTier, int, int, str]] = [

    # ── NVIDIA RTX 50xx Serisi (2025+) ────────────────────────────────────────
    (r"50\s*9[05]",    PerformanceTier.ULTRA,  160, 240, "RTX 50xx Flagship"),
    (r"50\s*8[05]",    PerformanceTier.ULTRA,  140, 200, "RTX 50xx High-End"),
    (r"50\s*7[05]",    PerformanceTier.ULTRA,  120, 170, "RTX 50xx Upper-Mid"),
    (r"50\s*6[05]",    PerformanceTier.HIGH,    90, 130, "RTX 50xx Mid-Range"),
    (r"50\s*5[05]",    PerformanceTier.HIGH,    80, 110, "RTX 50xx Entry"),

    # ── NVIDIA RTX 40xx Serisi ────────────────────────────────────────────────
    (r"40\s*9[05]",    PerformanceTier.ULTRA,  150, 240, "RTX 40xx Flagship"),
    (r"40\s*8[05]",    PerformanceTier.ULTRA,  130, 180, "RTX 40xx High-End"),
    (r"40\s*7[05]\s*ti", PerformanceTier.ULTRA, 120, 160, "RTX 4070 Ti"),
    (r"40\s*7[05]",    PerformanceTier.HIGH,   100, 140, "RTX 4070"),
    (r"40\s*6[05]\s*ti", PerformanceTier.HIGH,  90, 130, "RTX 4060 Ti"),
    (r"40\s*6[05]",    PerformanceTier.HIGH,    80, 120, "RTX 4060"),
    (r"40\s*5[05]",    PerformanceTier.HIGH,    80, 110, "RTX 4050"),

    # ── NVIDIA RTX 30xx Serisi ────────────────────────────────────────────────
    (r"30\s*9[05]",    PerformanceTier.ULTRA,  130, 180, "RTX 3090"),
    (r"30\s*8[05]\s*ti", PerformanceTier.ULTRA, 120, 160, "RTX 3080 Ti"),
    (r"30\s*8[05]",    PerformanceTier.HIGH,    100, 140, "RTX 3080"),
    (r"30\s*7[05]\s*ti", PerformanceTier.HIGH,   90, 130, "RTX 3070 Ti"),
    (r"30\s*7[05]",    PerformanceTier.HIGH,     80, 120, "RTX 3070"),
    (r"30\s*6[05]\s*ti", PerformanceTier.MEDIUM,  65, 95, "RTX 3060 Ti"),
    (r"30\s*6[05]",    PerformanceTier.MEDIUM,   55, 85, "RTX 3060"),
    (r"30\s*5[05]",    PerformanceTier.MEDIUM,   45, 70, "RTX 3050"),

    # ── NVIDIA RTX 20xx Serisi ────────────────────────────────────────────────
    (r"20\s*8[05]\s*ti", PerformanceTier.HIGH,   80, 120, "RTX 2080 Ti"),
    (r"20\s*8[05]",    PerformanceTier.HIGH,     70, 110, "RTX 2080"),
    (r"20\s*7[05]\s*super", PerformanceTier.MEDIUM, 65, 95, "RTX 2070 Super"),
    (r"20\s*7[05]",    PerformanceTier.MEDIUM,   60, 90, "RTX 2070"),
    (r"20\s*6[05]\s*super", PerformanceTier.MEDIUM, 55, 80, "RTX 2060 Super"),
    (r"20\s*6[05]",    PerformanceTier.MEDIUM,   50, 75, "RTX 2060"),

    # ── NVIDIA GTX 16xx Serisi ────────────────────────────────────────────────
    (r"16\s*6[05]\s*(super|ti)?", PerformanceTier.MEDIUM, 45, 70, "GTX 1660"),
    (r"16\s*5[05]",    PerformanceTier.LOW,      30, 55, "GTX 1650"),

    # ── NVIDIA GTX 10xx Serisi ────────────────────────────────────────────────
    (r"10\s*8[05]\s*ti", PerformanceTier.MEDIUM,  60, 90, "GTX 1080 Ti"),
    (r"10\s*8[05]",    PerformanceTier.MEDIUM,    50, 80, "GTX 1080"),
    (r"10\s*7[05]",    PerformanceTier.MEDIUM,    45, 70, "GTX 1070"),
    (r"10\s*6[05]",    PerformanceTier.LOW,       35, 60, "GTX 1060"),
    (r"10\s*5[05]",    PerformanceTier.LOW,       25, 45, "GTX 1050"),

    # ── AMD RX 7000 Serisi ────────────────────────────────────────────────────
    (r"rx\s*79[0-9][0-9]\s*(xt|xtx)?", PerformanceTier.ULTRA, 130, 190, "RX 7900 XT/XTX"),
    (r"rx\s*78[0-9][0-9]\s*(xt)?",     PerformanceTier.ULTRA, 110, 160, "RX 7800 XT"),
    (r"rx\s*77[0-9][0-9]\s*(xt)?",     PerformanceTier.HIGH,  90, 130, "RX 7700 XT"),
    (r"rx\s*76[0-9][0-9]\s*(xt)?",     PerformanceTier.HIGH,  80, 120, "RX 7600 XT"),
    (r"rx\s*75[0-9][0-9]",             PerformanceTier.HIGH,  75, 110, "RX 7500"),

    # ── AMD RX 6000 Serisi ────────────────────────────────────────────────────
    (r"rx\s*69[0-9][0-9]\s*(xt)?",     PerformanceTier.HIGH,  90, 130, "RX 6900 XT"),
    (r"rx\s*68[0-9][0-9]\s*(xt)?",     PerformanceTier.HIGH,  85, 120, "RX 6800 XT"),
    (r"rx\s*67[0-9][0-9]\s*(xt)?",     PerformanceTier.HIGH,  75, 110, "RX 6700 XT"),
    (r"rx\s*66[0-9][0-9]\s*(xt)?",     PerformanceTier.MEDIUM, 60, 90, "RX 6600 XT"),
    (r"rx\s*65[0-9][0-9]\s*(xt)?",     PerformanceTier.MEDIUM, 50, 75, "RX 6500 XT"),

    # ── AMD RX 5000 Serisi ────────────────────────────────────────────────────
    (r"rx\s*59[0-9][0-9]\s*(xt)?",     PerformanceTier.MEDIUM, 60, 90, "RX 5700 XT"),
    (r"rx\s*58[0-9][0-9]\s*(xt)?",     PerformanceTier.MEDIUM, 55, 80, "RX 5700"),
    (r"rx\s*57[0-9][0-9]\s*(xt)?",     PerformanceTier.MEDIUM, 50, 75, "RX 5600 XT"),

    # ── AMD RX 500 / Polaris Serisi ───────────────────────────────────────────
    (r"rx\s*5[89][0-9]",               PerformanceTier.LOW,    30, 55, "RX 580/590"),
    (r"rx\s*57[0-9]",                  PerformanceTier.LOW,    25, 50, "RX 570"),
    (r"rx\s*56[0-9]",                  PerformanceTier.LOW,    20, 40, "RX 560"),

    # ── Intel Arc ────────────────────────────────────────────────────────────
    (r"arc\s*a7[0-9][0-9]",            PerformanceTier.HIGH,   75, 110, "Intel Arc A770"),
    (r"arc\s*a7[0-9][05]",             PerformanceTier.MEDIUM,  60, 90, "Intel Arc A750"),
    (r"arc\s*a5[0-9][05]",             PerformanceTier.MEDIUM,  45, 70, "Intel Arc A580"),
    (r"arc\s*a3[0-9][05]",             PerformanceTier.LOW,     30, 55, "Intel Arc A380"),
]


def _normalize(text: str) -> str:
    """GPU metnini eşleştirme için standart hale getirir."""
    return text.lower().strip()


def analyze_gpu(gpu_model: str) -> PerformanceReport:
    """
    GPU model metnini alır, kural tablosuna göre performans seviyesi belirler.

    Args:
        gpu_model: Kullanıcının girdiği ham GPU metni.
                   Örnek: "RTX 4060", "rx 580", "GeForce GTX 1650 Ti"

    Returns:
        PerformanceReport — tahmini performans, FPS ve açıklama içerir.
    """
    normalized = _normalize(gpu_model)
    logger.info("Analyzing GPU: '%s' (normalized: '%s')", gpu_model, normalized)

    for pattern, tier, fps_min, fps_max, label in _GPU_RULES:
        if re.search(pattern, normalized):
            # FPS aralığı içinde rastgele ama tutarlı bir değer seç
            fps_estimate = random.randint(fps_min, fps_max)
            logger.info(
                "GPU match: pattern='%s' → tier=%s, FPS=%d (%s)",
                pattern, tier.value, fps_estimate, label
            )
            return PerformanceReport(
                gpu_model=gpu_model,
                estimated_performance=tier,
                estimated_fps=fps_estimate,
                fps_range=f"{fps_min}–{fps_max} FPS",
                matched_gpu_label=label,
                analysis_note=_build_note(tier),
            )

    # ── Hiçbir kural eşleşmediyse — güvenli varsayılan ───────────────────────
    logger.warning("No GPU rule matched for: '%s'. Returning default Medium tier.", gpu_model)
    return PerformanceReport(
        gpu_model=gpu_model,
        estimated_performance=PerformanceTier.MEDIUM,
        estimated_fps=50,
        fps_range="40–60 FPS",
        matched_gpu_label="Unknown GPU",
        analysis_note=(
            "GPU modeliniz tanımlanamadı. Orta seviye varsayılan değerler kullanıldı. "
            "Daha doğru sonuç için tam model adını girin (örn: RTX 4060, RX 6700 XT)."
        ),
    )


def _build_note(tier: PerformanceTier) -> str:
    """Performans katmanına göre kullanıcı dostu bir açıklama üretir."""
    notes = {
        PerformanceTier.ULTRA: (
            "Mükemmel performans! Oyunu 1440p/4K Ultra ayarlarında sorunsuz oynayabilirsiniz. "
            "Ray Tracing ve DLSS/FSR gibi gelişmiş özellikler aktif tutulabilir."
        ),
        PerformanceTier.HIGH: (
            "Yüksek performans. Oyunu 1080p–1440p High/Ultra ayarlarında "
            "akıcı bir şekilde oynayabilirsiniz."
        ),
        PerformanceTier.MEDIUM: (
            "Orta-iyi performans. 1080p Medium/High ayarlarında oynanabilir. "
            "Daha akıcı deneyim için bazı grafik ayarlarını düşürmeniz önerilir."
        ),
        PerformanceTier.LOW: (
            "Düşük performans. Oyunu 720p–1080p Low/Medium ayarlarında oynayabilirsiniz. "
            "Daha iyi deneyim için GPU yükseltmesi düşünebilirsiniz."
        ),
    }
    return notes.get(tier, "Performans bilgisi mevcut değil.")
