from typing import Optional
from sqlalchemy import String, Boolean, ForeignKey, Integer, Text
from sqlalchemy.orm import Mapped, mapped_column

from shared.types import BaseModel
from shared.schema import ColLen, TABLE_PREFIX

class Contact(BaseModel):
    __tablename__ = f"{TABLE_PREFIX}contact"
    __table_args__ = {'extend_existing': True}

    first_name: Mapped[str] = mapped_column(String(ColLen.NAME), nullable=False)
    last_name: Mapped[str] = mapped_column(String(ColLen.NAME), nullable=False)
    email: Mapped[Optional[str]] = mapped_column(String(ColLen.EMAIL), nullable=True)
    phone: Mapped[Optional[str]] = mapped_column(String(ColLen.PHONE), nullable=True)
    mobile: Mapped[Optional[str]] = mapped_column(String(ColLen.PHONE), nullable=True)
    department: Mapped[Optional[str]] = mapped_column(String(ColLen.NAME), nullable=True)
    position: Mapped[Optional[str]] = mapped_column(String(ColLen.NAME), nullable=True)
    is_primary: Mapped[bool] = mapped_column(Boolean, default=False, server_default="false")

    # We use Integer directly for these foreign keys as they relate to other domain modules
    # In a full system, these might have ForeignKey constraints, but for independent module testing
    # we just use Integer fields if we don't import the actual models.
    customer_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    supplier_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
