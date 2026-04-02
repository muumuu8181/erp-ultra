from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import Integer, String

from shared.types import Base


class Attachment(Base):
    __tablename__ = "attachments"
    __table_args__ = {'extend_existing': True}

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    code: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
