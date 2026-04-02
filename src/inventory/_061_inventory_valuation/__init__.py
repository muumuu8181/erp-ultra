"""
061_inventory_valuation - Inventory Valuation module.

Provides:
- Inventory valuation methods (FIFO, LIFO, Weighted Average, Standard Cost)
- Cost layer tracking
- Valuation snapshot and reporting
"""

from src.inventory._061_inventory_valuation.router import router
from src.inventory._061_inventory_valuation.models import ValuationMethod, ValuationSnapshot, CostLayer
from src.inventory._061_inventory_valuation.schemas import (
    ValuationMethodCreate,
    ValuationMethodResponse,
    CostLayerCreate,
    CostLayerResponse,
    ValuationSnapshotResponse,
    ValuationReport,
    ValuationSummary
)
from src.inventory._061_inventory_valuation.service import (
    set_valuation_method,
    get_valuation_method,
    add_cost_layer,
    consume_cost_layer,
    calculate_valuation,
    generate_snapshot,
    get_valuation_report,
    get_valuation_summary,
    get_cost_layers
)

__all__ = [
    "router",
    "ValuationMethod",
    "ValuationSnapshot",
    "CostLayer",
    "ValuationMethodCreate",
    "ValuationMethodResponse",
    "CostLayerCreate",
    "CostLayerResponse",
    "ValuationSnapshotResponse",
    "ValuationReport",
    "ValuationSummary",
    "set_valuation_method",
    "get_valuation_method",
    "add_cost_layer",
    "consume_cost_layer",
    "calculate_valuation",
    "generate_snapshot",
    "get_valuation_report",
    "get_valuation_summary",
    "get_cost_layers"
]
