from typing import Any
from sqlalchemy import JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from shared.types import BaseModel


class InventoryReport(BaseModel):
    __tablename__ = "inventory_reports"

    code: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    report_type: Mapped[str] = mapped_column(String(50), nullable=False)
    parameters: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    status: Mapped[str] = mapped_column(String(30), default="draft")
