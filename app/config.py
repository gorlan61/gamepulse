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
# Render veya diğer PaaS servisleri veritabanı URL'sini postgres:// veya postgresql:// ile verebilir.
# SQLAlchemy ile psycopg 3 kullanacağımız için postgresql+psycopg:// formatına dönüştürüyoruz.
raw_db_url = os.getenv("DATABASE_URL", "sqlite:///./gamepulse.db")
if raw_db_url.startswith("postgres://"):
    DATABASE_URL = raw_db_url.replace("postgres://", "postgresql+psycopg://", 1)
elif raw_db_url.startswith("postgresql://"):
    DATABASE_URL = raw_db_url.replace("postgresql://", "postgresql+psycopg://", 1)
else:
    DATABASE_URL = raw_db_url

