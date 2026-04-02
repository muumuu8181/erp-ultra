"""
Phase 1: 024_contact module
Contact Management module for ERP Ultra.
"""

from .models import Contact
from .schemas import ContactCreate, ContactUpdate, ContactResponse
from .service import create_contact, get_contact, list_contacts, update_contact, delete_contact
from .router import router

__all__ = [
    "Contact",
    "ContactCreate",
    "ContactUpdate",
    "ContactResponse",
    "create_contact",
    "get_contact",
    "list_contacts",
    "update_contact",
    "delete_contact",
    "router"
]
