from src.sales._038_shipment.schemas import ShipmentCreate, ShipmentUpdate
from shared.errors import ValidationError

def validate_shipment_create(data: ShipmentCreate) -> None:
    """Validates shipment creation payload."""
    if data.status not in ("draft", "pending"):
        raise ValidationError("New shipments must be created in 'draft' or 'pending' status.")
    if not data.items:
        raise ValidationError("Shipment must contain at least one item.")
    for item in data.items:
        if item.quantity <= 0:
            raise ValidationError("Shipment item quantity must be greater than zero.")

def validate_shipment_update(data: ShipmentUpdate) -> None:
    """Validates shipment update payload."""
    if data.status and data.status not in ("draft", "pending", "shipped", "delivered", "cancelled"):
        raise ValidationError(f"Invalid shipment status: {data.status}")
