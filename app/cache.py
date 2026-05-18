"""
cache.py — SQLite tabanlı, bağımsız ve yüksek performanslı önbellek (Cache) mekanizması.
Render ücretsiz planda harici bir Redis gerektirmeden disk/in-memory cache işlevi görür.
"""
import os
import json
import time
import sqlite3
import logging

logger = logging.getLogger(__name__)

CACHE_DB_PATH = os.getenv("CACHE_DB_PATH", "gamepulse_cache.db")


def init_cache():
    """Önbellek SQLite tablosunu hazırlar."""
    logger.info("Initializing SQLite cache database at '%s'...", CACHE_DB_PATH)
    try:
        with sqlite3.connect(CACHE_DB_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS cache_store (
                    key TEXT PRIMARY KEY,
                    value TEXT,
                    expires_at REAL
                )
                """
            )
            # Performans için index ekle
            cursor.execute(
                "CREATE INDEX IF NOT EXISTS idx_expires_at ON cache_store(expires_at)"
            )
            conn.commit()
        logger.info("SQLite cache database initialized successfully.")
    except Exception as exc:
        logger.error("Failed to initialize SQLite cache database: %s", exc)


def get_cache(key: str) -> dict | None:
    """
    Önbellekten anahtara (key) karşılık gelen veriyi çeker.
    Eğer veri yoksa veya süresi (TTL) dolmuşsa None döner.
    """
    try:
        now = time.time()
        with sqlite3.connect(CACHE_DB_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT value, expires_at FROM cache_store WHERE key = ?",
                (key,)
            )
            row = cursor.fetchone()
            
            if not row:
                return None
            
            value_json, expires_at = row
            
            # TTL kontrolü
            if now > expires_at:
                logger.info("Cache expired for key '%s'. Deleting...", key)
                cursor.execute("DELETE FROM cache_store WHERE key = ?", (key,))
                conn.commit()
                return None
            
            logger.info("Cache HIT for key '%s'.", key)
            return json.loads(value_json)
            
    except Exception as exc:
        logger.error("Error reading from cache: %s", exc)
        return None


def set_cache(key: str, value: dict, ttl_seconds: int = 3600):
    """
    Veriyi belirtilen TTL (saniye) süresiyle önbelleğe kaydeder.
    Her kayıt sırasında eski süresi dolmuş verileri temizler (auto-cleanup).
    """
    try:
        now = time.time()
        expires_at = now + ttl_seconds
        value_json = json.dumps(value)
        
        with sqlite3.connect(CACHE_DB_PATH) as conn:
            cursor = conn.cursor()
            
            # Yeni kaydı ekle veya üzerine yaz
            cursor.execute(
                """
                INSERT OR REPLACE INTO cache_store (key, value, expires_at)
                VALUES (?, ?, ?)
                """,
                (key, value_json, expires_at)
            )
            
            # Auto-cleanup: Süresi dolmuş eski verileri temizle
            cursor.execute("DELETE FROM cache_store WHERE expires_at < ?", (now,))
            
            conn.commit()
        logger.info("Cache SET for key '%s' with TTL=%d seconds.", key, ttl_seconds)
        
    except Exception as exc:
        logger.error("Error writing to cache: %s", exc)
