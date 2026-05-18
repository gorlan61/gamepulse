"""
models.py — SQLAlchemy Veritabanı Modelleri.
Veritabanındaki tabloların Python sınıfları olarak karşılıklarıdır.
"""
from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.sql import func
from app.database import Base


class SearchHistory(Base):
    """
    Kullanıcıların yaptığı oyun performansı sorgularını saklayan tablo.
    Gereksinim 3'e uygun olarak tasarlanmıştır.
    """
    __tablename__ = "search_history"

    id = Column(Integer, primary_key=True, index=True)
    game_name = Column(String(150), nullable=False, index=True)
    gpu_model = Column(String(100), nullable=False, index=True)
    estimated_performance = Column(String(50), nullable=False)
    estimated_fps = Column(Integer, nullable=False)
    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        description="Sorgunun yapıldığı anlık zaman damgası"
    )

    def __repr__(self) -> str:
        return f"<SearchHistory id={self.id} game='{self.game_name}' gpu='{self.gpu_model}'>"
