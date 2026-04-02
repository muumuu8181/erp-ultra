from typing import Optional
from sqlalchemy import String, Boolean, Text
from sqlalchemy.orm import Mapped, mapped_column
from shared.types import BaseModel


class InventoryEndpoint(BaseModel):
    """
    Inventory API Gateway Endpoint model.
    Represents an API endpoint managed by the Inventory API gateway.
    """
    __tablename__ = "inventory_endpoints"

    name: Mapped[str] = mapped_column(String(200), nullable=False)
    path: Mapped[str] = mapped_column(String(500), nullable=False)
    method: Mapped[str] = mapped_column(String(20), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
