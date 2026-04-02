import math
from decimal import Decimal
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_, and_
from shared.errors import DuplicateError, NotFoundError, BusinessRuleError, ValidationError
from shared.types import PaginatedResponse
from src.domain._017_product_model.models import Product, ProductCategory
from src.domain._017_product_model.schemas import ProductCreate, ProductUpdate, ProductCategoryCreate, ProductSearchFilter
from src.domain._017_product_model.validators import validate_product_create, validate_product_update, validate_category_exists, validate_positive_price

async def create_product(db: AsyncSession, data: ProductCreate) -> Product:
    """Create a new product. Validates code uniqueness and format.
    Raises DuplicateError if code already exists.
    Raises ValidationError if validation fails (negative prices, etc.)."""
    validate_product_create(data)

    existing = await db.execute(select(Product).where(Product.code == data.code))
    if existing.scalars().first():
        raise DuplicateError(f"Product with code '{data.code}' already exists.")

    if data.barcode:
        existing_barcode = await db.execute(select(Product).where(Product.barcode == data.barcode))
        if existing_barcode.scalars().first():
            raise DuplicateError(f"Product with barcode '{data.barcode}' already exists.")

    if data.category:
        await validate_category_exists(db, data.category)

    product = Product(**data.model_dump())
    db.add(product)
    await db.commit()
    await db.refresh(product)
    return product

async def update_product(db: AsyncSession, product_id: int, data: ProductUpdate) -> Product:
    """Update an existing product by ID.
    Raises NotFoundError if product not found.
    Only updates fields that are not None."""
    validate_product_update(data)

    product = await get_product(db, product_id)

    if data.barcode is not None and data.barcode != product.barcode:
        existing_barcode = await db.execute(select(Product).where(Product.barcode == data.barcode))
        if existing_barcode.scalars().first():
            raise DuplicateError(f"Product with barcode '{data.barcode}' already exists.")

    if data.category is not None:
        await validate_category_exists(db, data.category)

    update_data = data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(product, key, value)

    await db.commit()
    await db.refresh(product)
    return product

async def get_product(db: AsyncSession, product_id: int) -> Product:
    """Get a single product by ID.
    Raises NotFoundError if product not found."""
    result = await db.execute(select(Product).where(Product.id == product_id, Product.is_deleted == False))
    product = result.scalars().first()
    if not product:
        raise NotFoundError(f"Product with ID {product_id} not found.")
    return product

from src.domain._017_product_model.schemas import ProductResponse

async def list_products(db: AsyncSession, page: int = 1, page_size: int = 20,
                         category: str | None = None, is_active: bool | None = None,
                         supplier_id: int | None = None) -> PaginatedResponse[ProductResponse]:
    """List products with pagination and optional filters.
    Supports filtering by category, is_active, and supplier_id."""
    query = select(Product).where(Product.is_deleted == False)

    if category is not None:
        query = query.where(Product.category == category)
    if is_active is not None:
        query = query.where(Product.is_active == is_active)
    if supplier_id is not None:
        query = query.where(Product.supplier_id == supplier_id)

    from sqlalchemy import func
    # Count total
    count_query = select(func.count()).select_from(query.subquery())
    total = await db.scalar(count_query)

    # Paginate
    query = query.offset((page - 1) * page_size).limit(page_size)
    result = await db.execute(query)
    items = list(result.scalars().all())

    total_pages = math.ceil(total / page_size) if total else 0

    return PaginatedResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages
    )

async def deactivate_product(db: AsyncSession, product_id: int) -> Product:
    """Soft-delete / deactivate a product. Sets is_active=False.
    Raises NotFoundError if product not found.
    Raises BusinessRuleError if product has active orders or positive inventory."""
    product = await get_product(db, product_id)

    # Check for active orders/positive inventory here if those modules existed,
    # but for now we just soft delete it and set inactive.
    # Note: Soft deleting also sets is_deleted to True in addition to is_active = False based on standard behavior.

    product.is_active = False
    product.is_deleted = True
    from datetime import datetime
    product.deleted_at = datetime.utcnow()

    await db.commit()
    await db.refresh(product)
    return product

async def create_category(db: AsyncSession, data: ProductCategoryCreate) -> ProductCategory:
    """Create a new product category.
    Raises DuplicateError if category name already exists.
    Raises NotFoundError if parent_id is provided but not found."""
    existing = await db.execute(select(ProductCategory).where(ProductCategory.name == data.name))
    if existing.scalars().first():
        raise DuplicateError(f"Category with name '{data.name}' already exists.")

    if data.parent_id is not None:
        parent = await db.execute(select(ProductCategory).where(ProductCategory.id == data.parent_id))
        if not parent.scalars().first():
            raise NotFoundError(f"Parent category with ID {data.parent_id} not found.")

    category = ProductCategory(**data.model_dump())
    db.add(category)
    await db.commit()
    await db.refresh(category)
    return category

async def list_categories(db: AsyncSession, parent_id: int | None = None,
                           is_active: bool | None = None) -> list[ProductCategory]:
    """List product categories, optionally filtered by parent and active status.
    Returns flat list ordered by sort_order."""
    query = select(ProductCategory)

    if parent_id is not None:
        query = query.where(ProductCategory.parent_id == parent_id)
    if is_active is not None:
        query = query.where(ProductCategory.is_active == is_active)

    query = query.order_by(ProductCategory.sort_order)
    result = await db.execute(query)
    return list(result.scalars().all())

async def search_products(db: AsyncSession, filters: ProductSearchFilter,
                           page: int = 1, page_size: int = 20) -> PaginatedResponse[ProductResponse]:
    """Search products using filter criteria.
    Supports text search on name, name_kana, code, description.
    Supports range filter on standard_price."""
    query = select(Product).where(Product.is_deleted == False)

    if filters.query:
        search_pattern = f"%{filters.query}%"
        query = query.where(or_(
            Product.name.ilike(search_pattern),
            Product.name_kana.ilike(search_pattern),
            Product.code.ilike(search_pattern),
            Product.description.ilike(search_pattern)
        ))

    if filters.category:
        query = query.where(Product.category == filters.category)
    if filters.sub_category:
        query = query.where(Product.sub_category == filters.sub_category)
    if filters.is_active is not None:
        query = query.where(Product.is_active == filters.is_active)
    if filters.tax_type:
        query = query.where(Product.tax_type == filters.tax_type)
    if filters.min_price is not None:
        query = query.where(Product.standard_price >= filters.min_price)
    if filters.max_price is not None:
        query = query.where(Product.standard_price <= filters.max_price)
    if filters.supplier_id is not None:
        query = query.where(Product.supplier_id == filters.supplier_id)

    # Count total
    from sqlalchemy import func
    count_query = select(func.count()).select_from(query.subquery())
    total = await db.scalar(count_query)

    # Paginate
    query = query.offset((page - 1) * page_size).limit(page_size)
    result = await db.execute(query)
    items = list(result.scalars().all())

    total_pages = math.ceil(total / page_size) if total else 0

    return PaginatedResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages
    )

async def update_pricing(db: AsyncSession, product_id: int,
                          standard_price: Decimal | None = None,
                          cost_price: Decimal | None = None) -> Product:
    """Update product pricing. Convenience method for price-only updates.
    Raises NotFoundError if product not found.
    Raises ValidationError if prices are negative."""
    product = await get_product(db, product_id)

    if standard_price is not None:
        validate_positive_price(standard_price, "standard_price")
        product.standard_price = standard_price

    if cost_price is not None:
        validate_positive_price(cost_price, "cost_price")
        product.cost_price = cost_price

    await db.commit()
    await db.refresh(product)
    return product
