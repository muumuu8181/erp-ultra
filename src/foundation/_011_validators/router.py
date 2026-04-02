from typing import Annotated
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

try:
    from src.foundation._001_database.dependencies import get_db
except ImportError:
    # Fallback dependency if database module is not yet available
    async def get_db() -> AsyncSession:
        raise RuntimeError("Database dependency is not configured.")

from shared.types import PaginatedResponse
from src.foundation._011_validators import service
from src.foundation._011_validators.schemas import (
    ValidationRuleCreate,
    ValidationRuleUpdate,
    ValidationRuleResponse,
    ValidationRequest,
    ValidationResult
)

router = APIRouter(prefix="/api/v1/validators", tags=["validators"])

# Use an Annotated dependency for cleaner code
DbSession = Annotated[AsyncSession, Depends(get_db)]

@router.post("/rules", response_model=ValidationRuleResponse, status_code=status.HTTP_201_CREATED)
async def create_rule(rule_data: ValidationRuleCreate, db: DbSession):
    """
    Create a new validation rule.
    """
    rule = await service.create_rule(db, rule_data)
    return rule


@router.get("/rules", response_model=PaginatedResponse[ValidationRuleResponse])
async def list_rules(
    db: DbSession,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000)
):
    """
    List all validation rules.
    """
    items, total = await service.list_rules(db, skip=skip, limit=limit)

    # Calculate total pages
    total_pages = (total + limit - 1) // limit if limit > 0 else 0
    page = (skip // limit) + 1 if limit > 0 else 1

    return PaginatedResponse(
        items=items,
        total=total,
        page=page,
        page_size=limit,
        total_pages=total_pages
    )


@router.get("/rules/{rule_id}", response_model=ValidationRuleResponse)
async def get_rule(rule_id: int, db: DbSession):
    """
    Get a specific validation rule by ID.
    """
    rule = await service.get_rule(db, rule_id)
    return rule


@router.patch("/rules/{rule_id}", response_model=ValidationRuleResponse)
async def update_rule(rule_id: int, rule_data: ValidationRuleUpdate, db: DbSession):
    """
    Update a validation rule.
    """
    rule = await service.update_rule(db, rule_id, rule_data)
    return rule


@router.delete("/rules/{rule_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_rule(rule_id: int, db: DbSession):
    """
    Delete a validation rule.
    """
    await service.delete_rule(db, rule_id)


@router.post("/evaluate", response_model=ValidationResult)
async def evaluate_value(request: ValidationRequest, db: DbSession):
    """
    Evaluate a value against a named validation rule.
    """
    result = await service.evaluate(db, request.rule_name, request.value)
    return result
