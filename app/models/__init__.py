"""Re-export all ORM models for convenient imports."""

from app.models.catalog import (
    BookingStatus,
    ChargeCategory,
    DocumentType,
    NotificationType,
    ParkingSpaceType,
    PaymentMethod,
    PaymentStatus,
    PetSpecies,
    PqrStatus,
    PqrType,
    Priority,
    PropertyType,
    RelationType,
    VehicleType,
)
from app.models.core import (
    Condominium,
    Property,
    Role,
    User,
    UserCondominiumRole,
    UserDevice,
    UserProperty,
)
from app.models.amenity import Amenity, AmenityBooking
from app.models.finance import ChargeType, Invoice, Payment
from app.models.visitor import ParkingSpace, Vehicle, VisitorLog, VisitorParking
from app.models.pet import Pet
from app.models.news import NewsBoard
from app.models.pqr import Pqr, PqrComment
from app.models.notification import Notification
from app.models.email_pin import EmailPin
from app.models.rag import ChatMessage, ChatSession, Document, DocumentChunk
from app.models.audit_log import AuditLog

__all__ = [
    # catalogs
    "BookingStatus", "ChargeCategory", "DocumentType", "NotificationType",
    "ParkingSpaceType", "PaymentMethod", "PaymentStatus", "PetSpecies",
    "PqrStatus", "PqrType", "Priority", "PropertyType", "RelationType",
    "VehicleType",
    # core
    "Condominium", "Property", "Role", "User", "UserCondominiumRole",
    "UserDevice", "UserProperty",
    # domain
    "Amenity", "AmenityBooking", "ChargeType", "Invoice", "Payment",
    "ParkingSpace", "Vehicle", "VisitorLog", "VisitorParking",
    "Pet", "NewsBoard", "Pqr", "PqrComment", "Notification",
    "EmailPin",
    "Document", "DocumentChunk", "ChatSession", "ChatMessage",
    "AuditLog",
]
