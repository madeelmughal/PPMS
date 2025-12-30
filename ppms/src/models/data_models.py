"""
Data Models for PPMS
Defines all data structures and models used throughout the application.
"""

from dataclasses import dataclass, field, asdict
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum


class UserRole(Enum):
    """User role enumeration."""
    ADMIN = "admin"
    MANAGER = "manager"
    OPERATOR = "operator"
    ACCOUNTANT = "accountant"


class ShiftStatus(Enum):
    """Shift status enumeration."""
    OPEN = "open"
    CLOSED = "closed"


class NozzleStatus(Enum):
    """Nozzle status enumeration."""
    ACTIVE = "active"
    INACTIVE = "inactive"
    LOCKED = "locked"
    MAINTENANCE = "maintenance"


class PaymentMethod(Enum):
    """Payment method enumeration."""
    CASH = "cash"
    CREDIT = "credit"
    EASY_PAISA = "easy_paisa"
    JAZZ_CASH = "jazz_cash"
    BANK = "bank"


class TransactionStatus(Enum):
    """Transaction status enumeration."""
    PENDING = "pending"
    COMPLETED = "completed"
    VERIFIED = "verified"
    FAILED = "failed"


@dataclass
class User:
    """User model."""
    uid: str
    email: str
    name: str
    role: UserRole
    status: str = "active"
    department: str = ""
    phone: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    created_by: str = ""

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for Firebase."""
        data = asdict(self)
        data['role'] = self.role.value
        data['created_at'] = self.created_at.isoformat()
        data['updated_at'] = self.updated_at.isoformat()
        return data


@dataclass
class FuelType:
    """Fuel type model."""
    id: str
    name: str  # Petrol, Diesel, CNG
    unit_price: float
    tax_percentage: float = 10.0
    status: str = "active"
    created_at: datetime = field(default_factory=datetime.now)
    created_by: str = ""

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for Firebase."""
        data = asdict(self)
        data['created_at'] = self.created_at.isoformat()
        return data


@dataclass
class Tank:
    """Tank model."""
    id: str
    name: str
    fuel_type_id: str
    capacity: float
    current_stock: float
    minimum_stock: float
    location: str = ""
    last_reading_date: Optional[datetime] = None
    created_at: datetime = field(default_factory=datetime.now)
    created_by: str = ""

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for Firebase."""
        data = asdict(self)
        data['created_at'] = self.created_at.isoformat()
        if self.last_reading_date:
            data['last_reading_date'] = self.last_reading_date.isoformat()
        return data

    @property
    def stock_percentage(self) -> float:
        """Get stock level as percentage."""
        return (self.current_stock / self.capacity) * 100 if self.capacity > 0 else 0

    @property
    def is_low_stock(self) -> bool:
        """Check if stock is below minimum."""
        return self.current_stock < self.minimum_stock


@dataclass
class Nozzle:
    """Nozzle model."""
    id: str
    machine_id: str
    nozzle_number: int
    fuel_type_id: str
    opening_reading: float = 0.0
    closing_reading: float = 0.0
    assigned_operator_id: Optional[str] = None
    status: NozzleStatus = NozzleStatus.ACTIVE
    created_at: datetime = field(default_factory=datetime.now)
    created_by: str = ""

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for Firebase."""
        data = asdict(self)
        data['status'] = self.status.value
        data['created_at'] = self.created_at.isoformat()
        return data

    @property
    def current_reading(self) -> float:
        """Get current reading value."""
        return self.closing_reading if self.closing_reading > 0 else self.opening_reading


@dataclass
class Reading:
    """Meter reading model."""
    id: str
    nozzle_id: str
    date: datetime
    opening_reading: float
    closing_reading: float
    operator_id: str
    verified: bool = False
    created_at: datetime = field(default_factory=datetime.now)

    @property
    def quantity_sold(self) -> float:
        """Calculate quantity sold from readings."""
        return self.closing_reading - self.opening_reading

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for Firebase."""
        data = asdict(self)
        data['date'] = self.date.isoformat()
        data['created_at'] = self.created_at.isoformat()
        return data


@dataclass
class Sale:
    """Sale transaction model."""
    id: str
    date: datetime
    nozzle_id: str
    fuel_type_id: str
    quantity: float
    unit_price: float
    base_amount: float
    tax_amount: float
    total_amount: float
    payment_method: PaymentMethod
    operator_id: str
    shift_id: str
    customer_id: Optional[str] = None
    status: TransactionStatus = TransactionStatus.COMPLETED
    created_at: datetime = field(default_factory=datetime.now)
    created_by: str = ""

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for Firebase."""
        data = asdict(self)
        data['date'] = self.date.isoformat()
        data['payment_method'] = self.payment_method.value
        data['status'] = self.status.value
        data['created_at'] = self.created_at.isoformat()
        return data


@dataclass
class Purchase:
    """Fuel purchase model."""
    id: str
    date: datetime
    supplier_name: str
    invoice_number: str
    fuel_type_id: str
    quantity: float
    rate: float
    tax_amount: float
    total_cost: float
    tank_id: str
    status: str = "received"
    created_at: datetime = field(default_factory=datetime.now)
    created_by: str = ""

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for Firebase."""
        data = asdict(self)
        data['date'] = self.date.isoformat()
        data['created_at'] = self.created_at.isoformat()
        return data


@dataclass
class Customer:
    """Customer model."""
    id: str
    name: str
    phone: str
    email: Optional[str] = None
    address: str = ""
    credit_limit: float = 0.0
    outstanding_balance: float = 0.0
    status: str = "active"
    customer_type: str = "retail"
    created_at: datetime = field(default_factory=datetime.now)
    created_by: str = ""

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for Firebase."""
        data = asdict(self)
        data['created_at'] = self.created_at.isoformat()
        return data

    @property
    def available_credit(self) -> float:
        """Calculate available credit."""
        return self.credit_limit - self.outstanding_balance


@dataclass
class Expense:
    """Expense model."""
    id: str
    date: datetime
    category: str
    amount: float
    description: str
    bill_image_url: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.now)
    created_by: str = ""

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for Firebase."""
        data = asdict(self)
        data['date'] = self.date.isoformat()
        data['created_at'] = self.created_at.isoformat()
        return data


@dataclass
class Shift:
    """Shift model."""
    id: str
    date: datetime
    opening_time: datetime
    closing_time: Optional[datetime] = None
    operator_id: str = ""
    opening_cash: float = 0.0
    closing_cash: float = 0.0
    expected_cash: float = 0.0
    variance: float = 0.0
    status: ShiftStatus = ShiftStatus.OPEN
    created_at: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for Firebase."""
        data = asdict(self)
        data['date'] = self.date.isoformat()
        data['opening_time'] = self.opening_time.isoformat()
        if self.closing_time:
            data['closing_time'] = self.closing_time.isoformat()
        data['status'] = self.status.value
        data['created_at'] = self.created_at.isoformat()
        return data


@dataclass
class Payment:
    """Payment receipt model."""
    id: str
    date: datetime
    customer_id: str
    amount: float
    payment_method: PaymentMethod
    reference_number: Optional[str] = None
    notes: str = ""
    created_at: datetime = field(default_factory=datetime.now)
    created_by: str = ""

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for Firebase."""
        data = asdict(self)
        data['date'] = self.date.isoformat()
        data['payment_method'] = self.payment_method.value
        data['created_at'] = self.created_at.isoformat()
        return data


@dataclass
class AuditLog:
    """Audit log model."""
    id: str
    action: str
    entity_type: str
    entity_id: str
    old_value: Optional[Dict[str, Any]] = None
    new_value: Optional[Dict[str, Any]] = None
    user_id: str = ""
    timestamp: datetime = field(default_factory=datetime.now)
    ip_address: str = ""

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for Firebase."""
        data = asdict(self)
        data['timestamp'] = self.timestamp.isoformat()
        return data
