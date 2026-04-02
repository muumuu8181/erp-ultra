"""
023_address - Address Book module.
"""
from .router import router
from .models import Address
from .schemas import AddressCreate, AddressUpdate, AddressResponse
from .service import create_address, get_address, update_address, delete_address, list_addresses

__all__ = [
    "router",
    "Address",
    "AddressCreate",
    "AddressUpdate",
    "AddressResponse",
    "create_address",
    "get_address",
    "update_address",
    "delete_address",
    "list_addresses"
]
