from .models import SerialNumber, SerialHistory, SerialStatus, SerialEventType
from .schemas import SerialCreate, SerialResponse, SerialHistoryResponse, SerialTraceRequest, SerialTraceResponse, WarrantyCheck, WarrantyCheckResponse
from .service import register_serial, update_status, reserve, ship, return_serial, transfer, scrap, get_serial, trace_serial, check_warranty, get_by_product, get_by_customer
from .router import router

__all__ = [
    "SerialNumber",
    "SerialHistory",
    "SerialStatus",
    "SerialEventType",
    "SerialCreate",
    "SerialResponse",
    "SerialHistoryResponse",
    "SerialTraceRequest",
    "SerialTraceResponse",
    "WarrantyCheck",
    "WarrantyCheckResponse",
    "register_serial",
    "update_status",
    "reserve",
    "ship",
    "return_serial",
    "transfer",
    "scrap",
    "get_serial",
    "trace_serial",
    "check_warranty",
    "get_by_product",
    "get_by_customer",
    "router",
]
