"""
config.py — Uygulama genelindeki ayarlar burada tanımlanır.
python-dotenv sayesinde .env dosyasındaki değerleri okuyabiliriz.
"""
import os
from dotenv import load_dotenv

load_dotenv()  # .env dosyasını yükle

APP_VERSION = os.getenv("APP_VERSION", "0.1.0")
APP_ENV = os.getenv("APP_ENV", "development")

# CheapShark API — tamamen ücretsiz, kayıt gerektirmez
CHEAPSHARK_BASE_URL = "https://www.cheapshark.com/api/1.0"

# ── Veritabanı Yapılandırması ──────────────────────────────────────────────────
# Render veya diğer PaaS servisleri veritabanı URL'sini postgres:// ile başlayarak verebilir.
# SQLAlchemy 1.4/2.0+ ise postgresql:// şemasını zorunlu tutar. Bu yüzden otomatik dönüşüm yapıyoruz.
raw_db_url = os.getenv("DATABASE_URL", "sqlite:///./gamepulse.db")
if raw_db_url.startswith("postgres://"):
    DATABASE_URL = raw_db_url.replace("postgres://", "postgresql://", 1)
else:
    DATABASE_URL = raw_db_url

