"""
Service layer for Document Number Generator.
"""
from datetime import date

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from shared.errors import BusinessRuleError, NotFoundError
from src.domain._025_document_number.models import DocumentSequence
from src.domain._025_document_number.schemas import (
    DocumentSequenceCreate,
    DocumentSequenceUpdate,
    GeneratedDocumentNumberResponse,
)
from src.domain._025_document_number.validators import (
    validate_pattern,
    validate_prefix_format,
    validate_unique_prefix,
)


class DocumentSequenceService:
    """Service for managing document sequences and generating numbers."""

    async def create(self, db: AsyncSession, data: DocumentSequenceCreate, user: str) -> DocumentSequence:
        """Create a new document sequence."""
        validate_prefix_format(data.prefix)
        validate_pattern(data.pattern)
        await validate_unique_prefix(db, data.prefix)

        sequence = DocumentSequence(
            prefix=data.prefix,
            pattern=data.pattern,
            current_sequence=data.current_sequence,
            description=data.description,
            is_active=data.is_active,
        )
        db.add(sequence)
        await db.commit()
        await db.refresh(sequence)
        return sequence

    async def get(self, db: AsyncSession, id: int) -> DocumentSequence:
        """Get a document sequence by ID."""
        sequence = await db.get(DocumentSequence, id)
        if not sequence:
            raise NotFoundError("DocumentSequence", str(id))
        return sequence

    async def get_by_prefix(self, db: AsyncSession, prefix: str) -> DocumentSequence:
        """Get a document sequence by prefix."""
        stmt = select(DocumentSequence).where(DocumentSequence.prefix == prefix)
        result = await db.execute(stmt)
        sequence = result.scalars().first()
        if not sequence:
            raise NotFoundError("DocumentSequence", prefix)
        return sequence

    async def list(self, db: AsyncSession, skip: int = 0, limit: int = 100) -> tuple[list[DocumentSequence], int]:
        """List document sequences with pagination."""
        # Get total count
        count_stmt = select(func.count()).select_from(DocumentSequence)
        total = await db.scalar(count_stmt) or 0

        # Get items
        stmt = select(DocumentSequence).offset(skip).limit(limit).order_by(DocumentSequence.id)
        result = await db.execute(stmt)
        items = list(result.scalars().all())

        return items, total

    async def update(
        self, db: AsyncSession, id: int, data: DocumentSequenceUpdate, user: str
    ) -> DocumentSequence:
        """Update an existing document sequence."""
        sequence = await self.get(db, id)

        if data.pattern is not None:
            validate_pattern(data.pattern)
            sequence.pattern = data.pattern
        if data.description is not None:
            sequence.description = data.description
        if data.is_active is not None:
            sequence.is_active = data.is_active

        await db.commit()
        await db.refresh(sequence)
        return sequence

    async def delete(self, db: AsyncSession, id: int) -> bool:
        """Delete a document sequence."""
        sequence = await self.get(db, id)
        await db.delete(sequence)
        await db.commit()
        return True

    async def generate_next_number(self, db: AsyncSession, prefix: str) -> GeneratedDocumentNumberResponse:
        """
        Generate the next document number for a given prefix.
        Uses pessimistic locking to ensure safe concurrent access.
        """
        # We need a dedicated transaction or at least a locked row.
        # with_for_update() locks the row until the transaction commits.
        stmt = select(DocumentSequence).where(DocumentSequence.prefix == prefix).with_for_update()
        result = await db.execute(stmt)
        sequence = result.scalars().first()

        if not sequence:
            raise NotFoundError("DocumentSequence", prefix)

        if not sequence.is_active:
            raise BusinessRuleError(f"DocumentSequence '{prefix}' is not active.")

        # Increment sequence
        sequence.current_sequence += 1
        seq_num = sequence.current_sequence

        # We need to save the change
        await db.commit()

        # Format number based on pattern.
        # Allowed placeholders: {prefix}, {seq:0Nd}, {YYYY}, {YY}, {MM}, {DD}
        today = date.today()
        doc_number = sequence.pattern
        doc_number = doc_number.replace("{prefix}", sequence.prefix)
        doc_number = doc_number.replace("{YYYY}", today.strftime("%Y"))
        doc_number = doc_number.replace("{YY}", today.strftime("%y"))
        doc_number = doc_number.replace("{MM}", today.strftime("%m"))
        doc_number = doc_number.replace("{DD}", today.strftime("%d"))

        # Handle {seq:04d} or similar. Python's str.format will handle this if we pass seq=seq_num.
        # But we need to make sure we don't trip over '{YYYY}' etc if they are already replaced,
        # or if there are other braces.
        # A safer approach is to specifically format the sequence part.
        doc_number = doc_number.format(seq=seq_num)

        return GeneratedDocumentNumberResponse(
            document_number=doc_number,
            prefix=prefix,
            sequence=seq_num
        )
