import math
from typing import Optional, Sequence
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from shared.errors import NotFoundError, DuplicateError
from shared.types import PaginatedResponse
from .models import InventoryEndpoint
from .schemas import InventoryEndpointCreate, InventoryEndpointUpdate
from .validators import validate_http_method, validate_endpoint_path


async def get_inventory_endpoints(
    db: AsyncSession,
    skip: int = 0,
    limit: int = 100,
    is_active: Optional[bool] = None
) -> PaginatedResponse[InventoryEndpoint]:
    """
    Retrieves a paginated list of inventory endpoints.

    Args:
        db: The async database session.
        skip: Number of records to skip.
        limit: Maximum number of records to return.
        is_active: Optional filter by active status.

    Returns:
        A paginated response containing a list of InventoryEndpoints.
    """
    query = select(InventoryEndpoint)
    if is_active is not None:
        query = query.where(InventoryEndpoint.is_active == is_active)

    total_query = select(func.count()).select_from(query.subquery())
    total_result = await db.execute(total_query)
    total = total_result.scalar() or 0

    query = query.offset(skip).limit(limit)
    result = await db.execute(query)
    items = result.scalars().all()

    # Calculate pagination metadata
    page = (skip // limit) + 1 if limit > 0 else 1
    total_pages = math.ceil(total / limit) if limit > 0 else 1

    return PaginatedResponse[InventoryEndpoint](
        items=list(items),
        total=total,
        page=page,
        page_size=limit,
        total_pages=total_pages
    )


async def get_inventory_endpoint(db: AsyncSession, endpoint_id: int) -> InventoryEndpoint:
    """
    Retrieves a single inventory endpoint by ID.

    Args:
        db: The async database session.
        endpoint_id: The ID of the endpoint to retrieve.

    Returns:
        The InventoryEndpoint.

    Raises:
        NotFoundError: If the endpoint does not exist.
    """
    result = await db.execute(
        select(InventoryEndpoint).where(InventoryEndpoint.id == endpoint_id)
    )
    endpoint = result.scalar_one_or_none()
    if not endpoint:
        raise NotFoundError(f"Inventory endpoint with ID {endpoint_id} not found")
    return endpoint


async def create_inventory_endpoint(
    db: AsyncSession,
    endpoint_in: InventoryEndpointCreate
) -> InventoryEndpoint:
    """
    Creates a new inventory endpoint.

    Args:
        db: The async database session.
        endpoint_in: The schema containing endpoint details.

    Returns:
        The newly created InventoryEndpoint.

    Raises:
        DuplicateError: If an endpoint with the same path and method already exists.
    """
    # Validation rules
    validate_http_method(endpoint_in.method)
    validate_endpoint_path(endpoint_in.path)

    # Check for duplicates
    existing = await db.execute(
        select(InventoryEndpoint).where(
            InventoryEndpoint.path == endpoint_in.path,
            InventoryEndpoint.method == endpoint_in.method.upper()
        )
    )
    if existing.scalar_one_or_none():
        raise DuplicateError(
            f"Endpoint with path {endpoint_in.path} and method {endpoint_in.method} already exists"
        )

    db_endpoint = InventoryEndpoint(
        name=endpoint_in.name,
        path=endpoint_in.path,
        method=endpoint_in.method.upper(),
        description=endpoint_in.description,
        is_active=endpoint_in.is_active
    )
    db.add(db_endpoint)
    await db.commit()
    await db.refresh(db_endpoint)
    return db_endpoint


async def update_inventory_endpoint(
    db: AsyncSession,
    endpoint_id: int,
    endpoint_in: InventoryEndpointUpdate
) -> InventoryEndpoint:
    """
    Updates an existing inventory endpoint.

    Args:
        db: The async database session.
        endpoint_id: The ID of the endpoint to update.
        endpoint_in: The schema containing fields to update.

    Returns:
        The updated InventoryEndpoint.

    Raises:
        NotFoundError: If the endpoint does not exist.
        DuplicateError: If the updated path/method conflicts with another endpoint.
    """
    db_endpoint = await get_inventory_endpoint(db, endpoint_id)

    update_data = endpoint_in.model_dump(exclude_unset=True)

    # Partial validations
    if "method" in update_data and update_data["method"]:
        validate_http_method(update_data["method"])
        update_data["method"] = update_data["method"].upper()
    if "path" in update_data and update_data["path"]:
        validate_endpoint_path(update_data["path"])

    # Check for potential duplicates if path or method are updated
    new_path = update_data.get("path", db_endpoint.path)
    new_method = update_data.get("method", db_endpoint.method).upper()

    if new_path != db_endpoint.path or new_method != db_endpoint.method:
        existing = await db.execute(
            select(InventoryEndpoint).where(
                InventoryEndpoint.path == new_path,
                InventoryEndpoint.method == new_method,
                InventoryEndpoint.id != endpoint_id
            )
        )
        if existing.scalar_one_or_none():
            raise DuplicateError(
                f"Another endpoint with path {new_path} and method {new_method} already exists"
            )

    for field, value in update_data.items():
        setattr(db_endpoint, field, value)

    await db.commit()
    await db.refresh(db_endpoint)
    return db_endpoint


async def delete_inventory_endpoint(db: AsyncSession, endpoint_id: int) -> None:
    """
    Deletes an inventory endpoint.

    Args:
        db: The async database session.
        endpoint_id: The ID of the endpoint to delete.

    Raises:
        NotFoundError: If the endpoint does not exist.
    """
    db_endpoint = await get_inventory_endpoint(db, endpoint_id)
    await db.delete(db_endpoint)
    await db.commit()
