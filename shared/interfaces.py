"""
Inter-module interfaces and contracts.
Modules communicate through these interfaces, never by direct import.
"""
from abc import ABC, abstractmethod
from datetime import datetime
from decimal import Decimal
from typing import Any, Callable, Optional


# ── Event Bus ──────────────────────────────────────────────

class Event:
    """Inter-module event."""
    def __init__(self, event_type: str, module: str, data: dict[str, Any]):
        self.event_type = event_type
        self.module = module
        self.data = data
        self.timestamp = datetime.now()


class EventBus(ABC):
    """Publish-subscribe interface for module communication."""

    @abstractmethod
    async def publish(self, event: Event) -> None:
        """Publish an event to all subscribers."""
        ...

    @abstractmethod
    async def subscribe(self, event_type: str, handler: Callable[[Event], Any]) -> None:
        """Subscribe to events of a given type."""
        ...

    @abstractmethod
    async def unsubscribe(self, event_type: str, handler: Callable[[Event], Any]) -> None:
        """Unsubscribe from events."""
        ...


# ── Repository Interface ──────────────────────────────────

class Repository(ABC):
    """Generic repository interface for data access."""

    @abstractmethod
    async def get_by_id(self, id: int) -> Any:
        ...

    @abstractmethod
    async def get_all(self, skip: int = 0, limit: int = 100) -> list[Any]:
        ...

    @abstractmethod
    async def create(self, data: dict[str, Any]) -> Any:
        ...

    @abstractmethod
    async def update(self, id: int, data: dict[str, Any]) -> Any:
        ...

    @abstractmethod
    async def delete(self, id: int) -> bool:
        ...

    @abstractmethod
    async def count(self, **filters: Any) -> int:
        ...


# ── Service Interface ─────────────────────────────────────

class CrudService(ABC):
    """Standard CRUD service interface."""

    @abstractmethod
    async def get(self, id: int) -> Any:
        ...

    @abstractmethod
    async def list(self, **filters: Any) -> list[Any]:
        ...

    @abstractmethod
    async def create(self, data: dict[str, Any]) -> Any:
        ...

    @abstractmethod
    async def update(self, id: int, data: dict[str, Any]) -> Any:
        ...

    @abstractmethod
    async def delete(self, id: int) -> bool:
        ...


# ── Approval Interface ────────────────────────────────────

class Approvable(ABC):
    """Interface for documents that go through approval workflow."""

    @abstractmethod
    async def submit_for_approval(self, document_id: int, submitted_by: str) -> Any:
        ...

    @abstractmethod
    async def approve(self, document_id: int, approved_by: str, comment: str = "") -> Any:
        ...

    @abstractmethod
    async def reject(self, document_id: int, rejected_by: str, reason: str) -> Any:
        ...


# ── Report Interface ──────────────────────────────────────

class ReportGenerator(ABC):
    """Interface for report generation."""

    @abstractmethod
    async def generate(self, params: dict[str, Any]) -> Any:
        ...

    @abstractmethod
    async def export_csv(self, params: dict[str, Any]) -> str:
        ...

    @abstractmethod
    async def export_pdf(self, params: dict[str, Any]) -> bytes:
        ...
