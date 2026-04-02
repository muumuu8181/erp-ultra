from sqlalchemy import Integer, String, Boolean, Text, ForeignKey, UniqueConstraint, Index
from sqlalchemy.orm import Mapped, mapped_column

from shared.types import BaseModel


class Locale(BaseModel):
    __tablename__ = "locale"

    code: Mapped[str] = mapped_column(String(5), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    language: Mapped[str] = mapped_column(String(10), nullable=False)
    country: Mapped[str] = mapped_column(String(10), nullable=False)
    date_format: Mapped[str] = mapped_column(String(20), nullable=False)
    number_format: Mapped[str] = mapped_column(String(20), nullable=False)
    currency_code: Mapped[str] = mapped_column(String(3), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)


class Translation(BaseModel):
    __tablename__ = "translation"

    locale_id: Mapped[int] = mapped_column(Integer, ForeignKey("locale.id"), nullable=False)
    module: Mapped[str] = mapped_column(String(50), nullable=False)
    key: Mapped[str] = mapped_column(String(200), nullable=False)
    value: Mapped[str] = mapped_column(Text, nullable=False)

    __table_args__ = (
        UniqueConstraint("locale_id", "module", "key", name="uq_translation_locale_module_key"),
        Index("ix_translation_locale_id", "locale_id"),
        Index("ix_translation_module", "module"),
    )
