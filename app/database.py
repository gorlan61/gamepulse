"""
database.py — SQLAlchemy veritabanı bağlantısı ve oturum yönetimi.
SQLite ve PostgreSQL destekler.
"""
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from app.config import DATABASE_URL

# ── SQLite vs PostgreSQL Yapılandırması ──────────────────────────────────────
# connect_args={"check_same_thread": False} sadece SQLite için gereklidir.
# FastAPI çoklu thread kullandığından, SQLite'ın aynı thread kuralını gevşetmeliyiz.
if DATABASE_URL.startswith("sqlite"):
    connect_args = {"check_same_thread": False}
else:
    connect_args = {}

# SQLAlchemy Engine oluşturma
engine = create_engine(DATABASE_URL, connect_args=connect_args)

# Veritabanı oturum fabrikası (SessionLocal)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Tüm veri modellerinin (tables) türeyeceği taban sınıf
Base = declarative_base()


def get_db():
    """
    FastAPI Dependency Injection için veritabanı oturumu üreteci.
    Her istek (request) geldiğinde yeni bir oturum açar ve
    istek tamamlandığında otomatik olarak oturumu kapatır (Session lifecycle).
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
