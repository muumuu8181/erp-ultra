from sqlalchemy import String, Boolean, Enum as SAEnum, Integer, ForeignKey, UniqueConstraint, Numeric
from sqlalchemy.orm import Mapped, mapped_column
from shared.types import BaseModel
from typing import Optional
from decimal import Decimal
from src.domain._027_warehouse_model.schemas import WarehouseType, ZoneType, TemperatureZone

class Warehouse(BaseModel):
    """Warehouse master data."""
    __tablename__ = "warehouse"

    code: Mapped[str] = mapped_column(String(50), nullable=False, unique=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    type: Mapped[WarehouseType] = mapped_column(
        SAEnum(WarehouseType, name='warehouse_type'),
        nullable=False
    )
    postal_code: Mapped[Optional[str]] = mapped_column(String(8), nullable=True)
    prefecture: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    city: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    street: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    manager_name: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    phone: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

class WarehouseZone(BaseModel):
    """Zone within a warehouse."""
    __tablename__ = "warehouse_zone"
    __table_args__ = (
        UniqueConstraint('warehouse_id', 'code', name='uq_zone_warehouse_code'),
    )

    warehouse_id: Mapped[int] = mapped_column(Integer, ForeignKey('warehouse.id'), nullable=False)
    code: Mapped[str] = mapped_column(String(50), nullable=False)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    zone_type: Mapped[ZoneType] = mapped_column(
        SAEnum(ZoneType, name='zone_type'),
        nullable=False
    )
    temperature_zone: Mapped[TemperatureZone] = mapped_column(
        SAEnum(TemperatureZone, name='temperature_zone'),
        nullable=False, default=TemperatureZone.ambient
    )
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

class BinLocation(BaseModel):
    """Bin location within a warehouse zone."""
    __tablename__ = "bin_location"
    __table_args__ = (
        UniqueConstraint('zone_id', 'code', name='uq_bin_zone_code'),
    )

    zone_id: Mapped[int] = mapped_column(Integer, ForeignKey('warehouse_zone.id'), nullable=False)
    code: Mapped[str] = mapped_column(String(50), nullable=False)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    row: Mapped[Optional[str]] = mapped_column(String(10), nullable=True)
    column: Mapped[Optional[str]] = mapped_column(String(10), nullable=True)
    level: Mapped[Optional[str]] = mapped_column(String(10), nullable=True)
    capacity: Mapped[Optional[Decimal]] = mapped_column(Numeric(15, 3), nullable=True)
    current_usage: Mapped[Optional[Decimal]] = mapped_column(Numeric(15, 3), nullable=True, default=0)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
