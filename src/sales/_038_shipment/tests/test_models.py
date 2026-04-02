from decimal import Decimal
from src.sales._038_shipment.models import Shipment, ShipmentItem

def test_shipment_model_instantiation():
    shipment = Shipment(
        sales_order_id=1,
        customer_id=2,
        status="draft",
        carrier="FedEx"
    )
    assert shipment.sales_order_id == 1
    assert shipment.customer_id == 2
    assert shipment.status == "draft"
    assert shipment.carrier == "FedEx"

def test_shipment_item_model_instantiation():
    item = ShipmentItem(
        shipment_id=1,
        product_id=10,
        quantity=Decimal("5.5")
    )
    assert item.shipment_id == 1
    assert item.product_id == 10
    assert item.quantity == Decimal("5.5")
