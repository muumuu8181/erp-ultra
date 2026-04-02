import re
from typing import Any, Sequence
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError

from shared.errors import NotFoundError, DuplicateError, BusinessRuleError
from src.foundation._011_validators.models import ValidationRule
from src.foundation._011_validators.schemas import ValidationRuleCreate, ValidationRuleUpdate, ValidationResult


async def get_rule(db: AsyncSession, rule_id: int) -> ValidationRule:
    """
    Retrieve a validation rule by its ID.

    Args:
        db: The async database session.
        rule_id: The ID of the rule to retrieve.

    Returns:
        The ValidationRule object.

    Raises:
        NotFoundError: If the rule does not exist.
    """
    result = await db.execute(select(ValidationRule).filter(ValidationRule.id == rule_id))
    rule = result.scalars().first()
    if not rule:
        raise NotFoundError("ValidationRule", str(rule_id))
    return rule


async def get_rule_by_name(db: AsyncSession, name: str) -> ValidationRule:
    """
    Retrieve a validation rule by its unique name.

    Args:
        db: The async database session.
        name: The unique name of the rule.

    Returns:
        The ValidationRule object.

    Raises:
        NotFoundError: If the rule does not exist.
    """
    result = await db.execute(select(ValidationRule).filter(ValidationRule.name == name))
    rule = result.scalars().first()
    if not rule:
        raise NotFoundError("ValidationRule", name)
    return rule


async def list_rules(db: AsyncSession, skip: int = 0, limit: int = 100) -> tuple[Sequence[ValidationRule], int]:
    """
    List validation rules with pagination.

    Args:
        db: The async database session.
        skip: Number of records to skip.
        limit: Maximum number of records to return.

    Returns:
        A tuple containing the list of ValidationRule objects and the total count.
    """
    # Get total count
    count_stmt = select(func.count()).select_from(ValidationRule)
    count_result = await db.execute(count_stmt)
    total = count_result.scalar_one()

    # Get items
    stmt = select(ValidationRule).offset(skip).limit(limit)
    result = await db.execute(stmt)
    items = result.scalars().all()

    return items, total


async def create_rule(db: AsyncSession, rule_data: ValidationRuleCreate) -> ValidationRule:
    """
    Create a new validation rule.

    Args:
        db: The async database session.
        rule_data: The data for the new rule.

    Returns:
        The created ValidationRule object.

    Raises:
        DuplicateError: If a rule with the same name already exists.
    """
    rule = ValidationRule(**rule_data.model_dump())
    db.add(rule)
    try:
        await db.commit()
        await db.refresh(rule)
        return rule
    except IntegrityError:
        await db.rollback()
        raise DuplicateError("ValidationRule", rule_data.name)


async def update_rule(db: AsyncSession, rule_id: int, rule_data: ValidationRuleUpdate) -> ValidationRule:
    """
    Update an existing validation rule.

    Args:
        db: The async database session.
        rule_id: The ID of the rule to update.
        rule_data: The updated data for the rule.

    Returns:
        The updated ValidationRule object.

    Raises:
        NotFoundError: If the rule does not exist.
        DuplicateError: If the new name already exists for another rule.
    """
    rule = await get_rule(db, rule_id)

    update_data = rule_data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(rule, key, value)

    try:
        await db.commit()
        await db.refresh(rule)
        return rule
    except IntegrityError:
        await db.rollback()
        raise DuplicateError("ValidationRule", update_data.get('name', ''))


async def delete_rule(db: AsyncSession, rule_id: int) -> bool:
    """
    Delete a validation rule.

    Args:
        db: The async database session.
        rule_id: The ID of the rule to delete.

    Returns:
        True if the deletion was successful.

    Raises:
        NotFoundError: If the rule does not exist.
    """
    rule = await get_rule(db, rule_id)
    await db.delete(rule)
    await db.commit()
    return True


async def evaluate(db: AsyncSession, rule_name: str, value: Any) -> ValidationResult:
    """
    Evaluate a value against a specific validation rule.

    Args:
        db: The async database session.
        rule_name: The name of the rule to evaluate against.
        value: The value to evaluate.

    Returns:
        A ValidationResult indicating success or failure.

    Raises:
        NotFoundError: If the rule does not exist.
        BusinessRuleError: If the rule is inactive or misconfigured.
    """
    rule = await get_rule_by_name(db, rule_name)

    if not rule.is_active:
        raise BusinessRuleError(f"Validation rule '{rule_name}' is inactive.", "INACTIVE_RULE")

    try:
        if rule.rule_type == 'regex':
            pattern = rule.parameters.get('pattern') if rule.parameters else None
            if not pattern:
                raise BusinessRuleError("Regex rule missing 'pattern' parameter.", "INVALID_RULE_CONFIG")

            is_valid = bool(re.match(pattern, str(value)))

        elif rule.rule_type == 'range':
            min_val = rule.parameters.get('min') if rule.parameters else None
            max_val = rule.parameters.get('max') if rule.parameters else None

            try:
                numeric_val = float(value)
            except (ValueError, TypeError):
                return ValidationResult(is_valid=False, error_message=f"Value must be numeric. {rule.error_message}")

            is_valid = True
            if min_val is not None and numeric_val < float(min_val):
                is_valid = False
            if max_val is not None and numeric_val > float(max_val):
                is_valid = False

        elif rule.rule_type == 'length':
            min_len = rule.parameters.get('min') if rule.parameters else None
            max_len = rule.parameters.get('max') if rule.parameters else None

            val_len = len(str(value))
            is_valid = True

            if min_len is not None and val_len < int(min_len):
                is_valid = False
            if max_len is not None and val_len > int(max_len):
                is_valid = False

        elif rule.rule_type == 'in':
            choices = rule.parameters.get('choices', []) if rule.parameters else []
            is_valid = value in choices

        else:
            raise BusinessRuleError(f"Unsupported rule type: {rule.rule_type}", "UNSUPPORTED_RULE_TYPE")

        if is_valid:
            return ValidationResult(is_valid=True, error_message=None)
        else:
            return ValidationResult(is_valid=False, error_message=rule.error_message)

    except Exception as e:
        if isinstance(e, BusinessRuleError):
            raise e
        return ValidationResult(is_valid=False, error_message=f"Evaluation error: {str(e)}")
