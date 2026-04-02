from datetime import datetime
from sqlalchemy import Integer, String, DateTime, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from shared.types import Base
from shared.schema import ColLen

class CacheEntry(Base):
    __tablename__ = "cache_entries"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    key: Mapped[str] = mapped_column(String(ColLen.CODE), unique=True, nullable=False, index=True)
    value: Mapped[str] = mapped_column(Text, nullable=False)  # JSON string
    ttl_seconds: Mapped[int] = mapped_column(Integer, nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, index=True)
    module: Mapped[str] = mapped_column(String(ColLen.SHORT_NAME), nullable=False, index=True)
    hit_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=func.now(), onupdate=func.now())


class CacheStatsRecord(Base):
    __tablename__ = "cache_stats"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    module: Mapped[str] = mapped_column(String(ColLen.SHORT_NAME), nullable=False, index=True)
    hits: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    misses: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    evictions: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    recorded_at: Mapped[datetime] = mapped_column(DateTime, default=func.now())
