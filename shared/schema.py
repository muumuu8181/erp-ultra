"""
Database schema constants and column conventions.
All modules use these for consistent table/column definitions.
"""

# ── Table conventions ────────────────────────────────────────

TABLE_PREFIX = ""  # No prefix; table name = class __tablename__

ID_COLUMN = "id"
CODE_COLUMN = "code"
NAME_COLUMN = "name"


# ── Standard column sizes ────────────────────────────────────

class ColLen:
    """Standard column lengths for consistent sizing across modules."""
    CODE = 50
    NAME = 200
    SHORT_NAME = 100
    DESCRIPTION = 500
    EMAIL = 254
    PHONE = 20
    URL = 500
    STATUS = 30
    CURRENCY = 3


# ── Numeric precision ────────────────────────────────────────

class Precision:
    """Standard numeric precision for financial calculations."""
    AMOUNT = (15, 2)       # Monetary amounts
    QUANTITY = (15, 3)     # Quantities with fractional units
    RATE = (10, 6)         # Exchange rates, tax rates
    PERCENTAGE = (5, 2)    # Percentages (0.00-100.00)


# ── Common status values ─────────────────────────────────────

class RowStatus:
    """Standard row-level status values for active/inactive records."""
    ACTIVE = "active"
    INACTIVE = "inactive"


# ── Pagination defaults ──────────────────────────────────────

DEFAULT_PAGE_SIZE = 50
MAX_PAGE_SIZE = 500
