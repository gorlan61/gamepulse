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
