"""
Unit of Measure models.
"""
from decimal import Decimal
from sqlalchemy import String, Integer, Boolean, Enum as SAEnum, Numeric, ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from shared.types import BaseModel
from shared.schema import ColLen, Precision


class UnitOfMeasure(BaseModel):
    """Unit of measure definition."""
    __tablename__ = "unit_of_measure"

    code: Mapped[str] = mapped_column(String(ColLen.CODE), nullable=False, unique=True)
    name: Mapped[str] = mapped_column(String(ColLen.NAME), nullable=False)
    symbol: Mapped[str] = mapped_column(String(ColLen.STATUS), nullable=False)
    uom_type: Mapped[str] = mapped_column(
        SAEnum('count', 'weight', 'volume', 'length', 'time', 'area', name='uom_type'),
        nullable=False
    )
    decimal_places: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)


class UomConversion(BaseModel):
    """Conversion factor between two units of measure."""
    __tablename__ = "uom_conversion"
    __table_args__ = (
        UniqueConstraint('from_uom_id', 'to_uom_id', name='uq_uom_conversion_pair'),
    )

    from_uom_id: Mapped[int] = mapped_column(Integer, ForeignKey('unit_of_measure.id'), nullable=False)
    to_uom_id: Mapped[int] = mapped_column(Integer, ForeignKey('unit_of_measure.id'), nullable=False)
    factor: Mapped[Decimal] = mapped_column(Numeric(*Precision.RATE), nullable=False)
    is_standard: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
