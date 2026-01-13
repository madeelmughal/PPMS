"""
Database Service
Generic database operations for PPMS entities.
"""

import logging
import uuid
from typing import Optional, List, Dict, Any
from datetime import datetime
from src.config.firebase_config import FirebaseConfig, DatabaseConfig
from src.config.logger_config import setup_logger
from src.models import (
    FuelType, Tank, Nozzle, Sale, Purchase, Customer,
    Expense, Shift, Payment, Reading, AuditLog
)

logger = setup_logger(__name__)


class DatabaseService:
    """Generic database service for CRUD operations."""

    def __init__(self):
        """Initialize database service."""
        self.firestore = FirebaseConfig.get_firestore()
        self.db = FirebaseConfig.get_realtime_db()

    def create_document(
        self,
        collection: str,
        document_id: str,
        data: Dict[str, Any],
        user_id: str = ""
    ) -> tuple[bool, str]:
        """
        Create a new document.

        Args:
            collection: Collection name
            document_id: Document ID
            data: Document data
            user_id: User ID for audit

        Returns:
            Tuple of (success, message)
        """
        try:
            # Add metadata
            data['created_at'] = datetime.now().isoformat()
            if user_id:
                data['created_by'] = user_id

            self.firestore.collection(collection).document(document_id).set(data)
            logger.info(f"Document created: {collection}/{document_id}")
            return True, "Document created successfully"

        except Exception as e:
            logger.error(f"Error creating document: {str(e)}")
            return False, f"Error: {str(e)}"

    def read_document(
        self, collection: str, document_id: str
    ) -> Optional[Dict[str, Any]]:
        """
        Read a document.

        Args:
            collection: Collection name
            document_id: Document ID

        Returns:
            Document data or None
        """
        try:
            doc = self.firestore.collection(collection).document(document_id).get()
            return doc.to_dict() if doc.exists else None
        except Exception as e:
            logger.error(f"Error reading document: {str(e)}")
            return None

    def update_document(
        self,
        collection: str,
        document_id: str,
        data: Dict[str, Any]
    ) -> tuple[bool, str]:
        """
        Update a document.

        Args:
            collection: Collection name
            document_id: Document ID
            data: Data to update

        Returns:
            Tuple of (success, message)
        """
        try:
            data['updated_at'] = datetime.now().isoformat()
            self.firestore.collection(collection).document(document_id).update(data)
            logger.info(f"Document updated: {collection}/{document_id}")
            return True, "Document updated successfully"

        except Exception as e:
            logger.error(f"Error updating document: {str(e)}")
            return False, f"Error: {str(e)}"

    def delete_document(
        self, collection: str, document_id: str
    ) -> tuple[bool, str]:
        """
        Delete a document.

        Args:
            collection: Collection name
            document_id: Document ID

        Returns:
            Tuple of (success, message)
        """
        try:
            self.firestore.collection(collection).document(document_id).delete()
            logger.info(f"Document deleted: {collection}/{document_id}")
            return True, "Document deleted successfully"

        except Exception as e:
            logger.error(f"Error deleting document: {str(e)}")
            return False, f"Error: {str(e)}"

    def list_documents(
        self, collection: str, filters: Optional[List[tuple]] = None
    ) -> List[Dict[str, Any]]:
        """
        List documents in a collection with optional filters.

        Args:
            collection: Collection name
            filters: List of (field, operator, value) tuples

        Returns:
            List of documents
        """
        try:
            query = self.firestore.collection(collection)

            # Apply filters
            if filters:
                for field, operator, value in filters:
                    query = query.where(field, operator, value)

            docs = query.stream()
            documents = [doc.to_dict() for doc in docs]
            return documents

        except Exception as e:
            logger.error(f"Error listing documents: {str(e)}")
            return []

    def get_all_inventory(self) -> List[Dict[str, Any]]:
        """Get all inventory items."""
        try:
            docs = self.firestore.collection('inventory').stream()
            items = []
            for doc in docs:
                data = doc.to_dict()
                items.append(data)
            return items
        except Exception as e:
            logger.error(f"Error getting all inventory: {str(e)}")
            return []

    def batch_write(
        self, operations: List[tuple]
    ) -> tuple[bool, str]:
        """
        Perform batch write operations.

        Args:
            operations: List of (operation, collection, doc_id, data) tuples
                       operation: 'set', 'update', 'delete'

        Returns:
            Tuple of (success, message)
        """
        try:
            batch = self.firestore.batch()

            for operation, collection, doc_id, data in operations:
                doc_ref = self.firestore.collection(collection).document(doc_id)

                if operation == 'set':
                    data['created_at'] = datetime.now().isoformat()
                    batch.set(doc_ref, data)
                elif operation == 'update':
                    data['updated_at'] = datetime.now().isoformat()
                    batch.update(doc_ref, data)
                elif operation == 'delete':
                    batch.delete(doc_ref)

            batch.commit()
            logger.info(f"Batch write completed: {len(operations)} operations")
            return True, "Batch write successful"

        except Exception as e:
            logger.error(f"Error in batch write: {str(e)}")
            return False, f"Error: {str(e)}"

    def transaction_update(
        self, updates: Dict[str, Dict[str, Any]]
    ) -> tuple[bool, str]:
        """
        Perform transactional updates across multiple documents.

        Args:
            updates: Dict of {collection.doc_id: data}

        Returns:
            Tuple of (success, message)
        """
        try:
            @self.firestore.transactional
            def update_in_transaction(transaction):
                for key, data in updates.items():
                    collection, doc_id = key.split('.')
                    doc_ref = self.firestore.collection(collection).document(doc_id)
                    data['updated_at'] = datetime.now().isoformat()
                    transaction.update(doc_ref, data)

            transaction = self.firestore.transaction()
            update_in_transaction(transaction)

            logger.info(f"Transaction completed: {len(updates)} documents updated")
            return True, "Transaction successful"

        except Exception as e:
            logger.error(f"Error in transaction: {str(e)}")
            return False, f"Error: {str(e)}"


class FuelService(DatabaseService):
    """Service for fuel-related operations."""

    def create_fuel_type(
        self, name: str, unit_price: float, tax_percentage: float = 10.0,
        user_id: str = ""
    ) -> tuple[bool, str, Optional[str]]:
        """Create new fuel type."""
        try:
            fuel_id = str(uuid.uuid4())
            data = {
                'id': fuel_id,
                'name': name,
                'unit_price': unit_price,
                'tax_percentage': tax_percentage,
                'status': 'active'
            }
            success, msg = self.create_document('fuel_types', fuel_id, data, user_id)
            return success, msg, fuel_id if success else None
        except Exception as e:
            logger.error(f"Error creating fuel type: {str(e)}")
            return False, str(e), None

    def list_fuel_types(self) -> List[FuelType]:
        """Get all fuel types."""
        try:
            docs = self.firestore.collection('fuel_types').where(
                'status', '==', 'active'
            ).stream()

            fuel_types = []
            for doc in docs:
                data = doc.to_dict()
                fuel_type = FuelType(
                    id=data.get('id'),
                    name=data.get('name'),
                    unit_price=data.get('unit_price', 0),
                    tax_percentage=data.get('tax_percentage', 10),
                    status=data.get('status', 'active')
                )
                fuel_types.append(fuel_type)
            return fuel_types
        except Exception as e:
            logger.error(f"Error listing fuel types: {str(e)}")
            return []


class TankService(DatabaseService):
    """Service for tank-related operations."""

    def create_tank(
        self, name: str, fuel_type_id: str, capacity: float,
        minimum_stock: float, user_id: str = ""
    ) -> tuple[bool, str, Optional[str]]:
        """Create new tank."""
        try:
            tank_id = str(uuid.uuid4())
            data = {
                'id': tank_id,
                'name': name,
                'fuel_type_id': fuel_type_id,
                'capacity': capacity,
                'current_stock': 0,
                'minimum_stock': minimum_stock,
                'location': ''
            }
            success, msg = self.create_document('tanks', tank_id, data, user_id)
            return success, msg, tank_id if success else None
        except Exception as e:
            logger.error(f"Error creating tank: {str(e)}")
            return False, str(e), None

    def get_tank(self, tank_id: str) -> Optional[Tank]:
        """Get tank by ID."""
        try:
            data = self.read_document('tanks', tank_id)
            if data:
                return Tank(
                    id=data.get('id'),
                    name=data.get('name'),
                    fuel_type_id=data.get('fuel_type_id'),
                    capacity=data.get('capacity', 0),
                    current_stock=data.get('current_stock', 0),
                    minimum_stock=data.get('minimum_stock', 0),
                    location=data.get('location', '')
                )
            return None
        except Exception as e:
            logger.error(f"Error getting tank: {str(e)}")
            return None

    def update_tank_stock(
        self, tank_id: str, new_stock: float
    ) -> tuple[bool, str]:
        """Update tank stock level."""
        try:
            return self.update_document('tanks', tank_id, {
                'current_stock': new_stock,
                'last_reading_date': datetime.now().isoformat()
            })
        except Exception as e:
            logger.error(f"Error updating tank stock: {str(e)}")
            return False, str(e)

    def list_tanks(self) -> List[Tank]:
        """Get all tanks."""
        try:
            docs = self.firestore.collection('tanks').stream()
            tanks = []
            for doc in docs:
                data = doc.to_dict()
                tank = Tank(
                    id=data.get('id'),
                    name=data.get('name'),
                    fuel_type_id=data.get('fuel_type_id'),
                    capacity=data.get('capacity', 0),
                    current_stock=data.get('current_stock', 0),
                    minimum_stock=data.get('minimum_stock', 0),
                    location=data.get('location', '')
                )
                tanks.append(tank)
            return tanks
        except Exception as e:
            logger.error(f"Error listing tanks: {str(e)}")
            return []


class SalesService(DatabaseService):
    """Service for sales-related operations."""

    def record_sale(self, sale: Sale, user_id: str = "") -> tuple[bool, str, Optional[str]]:
        """Record a fuel sale."""
        try:
            success, msg = self.create_document(
                'sales',
                sale.id,
                sale.to_dict(),
                user_id
            )
            return success, msg, sale.id if success else None
        except Exception as e:
            logger.error(f"Error recording sale: {str(e)}")
            return False, str(e), None

    def add_sale(self, sale: Sale, user_id: str = "") -> tuple[bool, str]:
        """Add a new sale (alias for record_sale with tank inventory update)."""
        try:
            success, msg, sale_id = self.record_sale(sale, user_id)
            return success, msg
        except Exception as e:
            logger.error(f"Error adding sale: {str(e)}")
            return False, str(e)

    def update_sale(self, sale_id: str, sale: Sale) -> tuple[bool, str]:
        """Update an existing sale."""
        try:
            success, msg = self.update_document('sales', sale_id, sale.to_dict())
            return success, msg
        except Exception as e:
            logger.error(f"Error updating sale: {str(e)}")
            return False, str(e)

    def delete_sale(self, sale_id: str) -> tuple[bool, str]:
        """Delete a sale."""
        try:
            self.firestore.collection('sales').document(sale_id).delete()
            logger.info(f"Sale deleted: {sale_id}")
            return True, "Sale deleted successfully"
        except Exception as e:
            logger.error(f"Error deleting sale: {str(e)}")
            return False, str(e)

    def get_sales_by_date(self, date_str: str) -> List[Sale]:
        """Get all sales for a specific date (format: YYYY-MM-DD)."""
        try:
            docs = self.firestore.collection('sales').where(
                'date', '>=', f"{date_str}T00:00:00"
            ).where(
                'date', '<', f"{date_str}T23:59:59"
            ).stream()

            sales = []
            for doc in docs:
                data = doc.to_dict()
                sale = Sale(
                    id=data.get('id'),
                    nozzle_id=data.get('nozzle_id'),
                    fuel_type_id=data.get('fuel_type_id'),
                    quantity=data.get('quantity'),
                    unit_price=data.get('unit_price'),
                    total_amount=data.get('total_amount'),
                    payment_method=data.get('payment_method'),
                    customer_name=data.get('customer_name'),
                    vehicle_number=data.get('vehicle_number'),
                    notes=data.get('notes'),
                    sale_date=data.get('sale_date'),
                    created_at=data.get('created_at'),
                    created_by=data.get('created_by')
                )
                sales.append(sale)
            return sales
        except Exception as e:
            logger.error(f"Error getting sales by date: {str(e)}")
            return []

    def list_daily_sales(self, date: datetime) -> List[Sale]:
        """Get all sales for a specific date."""
        try:
            date_str = date.strftime('%Y-%m-%d')
            docs = self.firestore.collection('sales').where(
                'date', '>=', f"{date_str}T00:00:00"
            ).where(
                'date', '<', f"{date_str}T23:59:59"
            ).stream()

            sales = []
            for doc in docs:
                data = doc.to_dict()
                # Parse Sale object from data
                sales.append(data)
            return sales
        except Exception as e:
            logger.error(f"Error listing daily sales: {str(e)}")
            return []

    def get_sales_by_date_range(self, start_date: str, end_date: str) -> List[Sale]:
        """Get all sales for a specific date range (format: YYYY-MM-DD)."""
        try:
            docs = self.firestore.collection('sales').where(
                'date', '>=', f"{start_date}T00:00:00"
            ).where(
                'date', '<=', f"{end_date}T23:59:59"
            ).stream()

            sales = []
            for doc in docs:
                data = doc.to_dict()
                sale = Sale(
                    id=data.get('id'),
                    nozzle_id=data.get('nozzle_id'),
                    fuel_type_id=data.get('fuel_type_id'),
                    quantity=data.get('quantity'),
                    unit_price=data.get('unit_price'),
                    total_amount=data.get('total_amount'),
                    payment_method=data.get('payment_method'),
                    customer_name=data.get('customer_name'),
                    vehicle_number=data.get('vehicle_number'),
                    notes=data.get('notes'),
                    sale_date=data.get('sale_date'),
                    created_at=data.get('created_at'),
                    created_by=data.get('created_by')
                )
                sales.append(sale)
            return sales
        except Exception as e:
            logger.error(f"Error getting sales by date range: {str(e)}")
            return []


class CustomerService(DatabaseService):
    """Service for customer-related operations."""

    def create_customer(
        self, name: str, phone: str, email: Optional[str] = None,
        credit_limit: float = 0, user_id: str = ""
    ) -> tuple[bool, str, Optional[str]]:
        """Create new customer."""
        try:
            customer_id = self.firestore.collection('customers').document().id
            data = {
                'id': customer_id,
                'name': name,
                'phone': phone,
                'email': email or '',
                'address': '',
                'credit_limit': credit_limit,
                'outstanding_balance': 0,
                'status': 'active',
                'customer_type': 'retail'
            }
            success, msg = self.create_document('customers', customer_id, data, user_id)
            return success, msg, customer_id if success else None
        except Exception as e:
            logger.error(f"Error creating customer: {str(e)}")
            return False, str(e), None

    def list_customers(self) -> List[Customer]:
        """Get all customers."""
        try:
            docs = self.firestore.collection('customers').where(
                'status', '==', 'active'
            ).stream()

            customers = []
            for doc in docs:
                data = doc.to_dict()
                customer = Customer(
                    id=data.get('id'),
                    name=data.get('name'),
                    phone=data.get('phone'),
                    email=data.get('email'),
                    address=data.get('address', ''),
                    credit_limit=data.get('credit_limit', 0),
                    outstanding_balance=data.get('outstanding_balance', 0),
                    status=data.get('status', 'active')
                )
                customers.append(customer)
            return customers
        except Exception as e:
            logger.error(f"Error listing customers: {str(e)}")
            return []

    def get_all_customers(self) -> List[Dict[str, Any]]:
        """Get all customers as dictionaries."""
        try:
            docs = self.firestore.collection('customers').stream()
            customers = []
            for doc in docs:
                data = doc.to_dict()
                customers.append(data)
            return customers
        except Exception as e:
            logger.error(f"Error getting all customers: {str(e)}")
            return []


class NozzleService(DatabaseService):
    """Service for nozzle-related operations."""

    def create_nozzle(
        self, machine_id: str, nozzle_number: int, fuel_type_id: str,
        opening_reading: float = 0.0, user_id: str = ""
    ) -> tuple[bool, str, Optional[str]]:
        """Create new nozzle."""
        try:
            nozzle_id = str(uuid.uuid4())
            data = {
                'id': nozzle_id,
                'machine_id': machine_id,
                'nozzle_number': nozzle_number,
                'fuel_type_id': fuel_type_id,
                'opening_reading': opening_reading,
                'current_reading': opening_reading,  # Initialize to opening reading
                'closing_reading': 0.0,
                'assigned_operator_id': '',
                'status': 'active'
            }
            success, msg = self.create_document('nozzles', nozzle_id, data, user_id)
            return success, msg, nozzle_id if success else None
        except Exception as e:
            logger.error(f"Error creating nozzle: {str(e)}")
            return False, str(e), None

    def get_nozzle(self, nozzle_id: str) -> Optional[Nozzle]:
        """Get nozzle by ID."""
        try:
            data = self.read_document('nozzles', nozzle_id)
            if data:
                return Nozzle(
                    id=data.get('id'),
                    machine_id=data.get('machine_id'),
                    nozzle_number=data.get('nozzle_number', 0),
                    fuel_type_id=data.get('fuel_type_id'),
                    opening_reading=data.get('opening_reading', 0.0),
                    closing_reading=data.get('closing_reading', 0.0),
                    assigned_operator_id=data.get('assigned_operator_id'),
                    status=data.get('status', 'active')
                )
            return None
        except Exception as e:
            logger.error(f"Error getting nozzle: {str(e)}")
            return None

    def list_nozzles(self, machine_id: Optional[str] = None) -> List[Nozzle]:
        """Get all nozzles, optionally filtered by machine."""
        try:
            query = self.firestore.collection('nozzles').where(
                'status', '==', 'active'
            )
            
            if machine_id:
                query = query.where('machine_id', '==', machine_id)
            
            docs = query.stream()
            nozzles = []
            for doc in docs:
                data = doc.to_dict()
                nozzle = Nozzle(
                    id=data.get('id'),
                    machine_id=data.get('machine_id'),
                    nozzle_number=data.get('nozzle_number', 0),
                    fuel_type_id=data.get('fuel_type_id'),
                    opening_reading=data.get('opening_reading', 0.0),
                    closing_reading=data.get('closing_reading', 0.0),
                    assigned_operator_id=data.get('assigned_operator_id'),
                    status=data.get('status', 'active')
                )
                nozzles.append(nozzle)
            return nozzles
        except Exception as e:
            logger.error(f"Error listing nozzles: {str(e)}")
            return []

    def update_nozzle_reading(
        self, nozzle_id: str, closing_reading: float
    ) -> tuple[bool, str]:
        """Update nozzle closing reading."""
        try:
            return self.update_document('nozzles', nozzle_id, {
                'closing_reading': closing_reading,
                'last_reading_date': datetime.now().isoformat()
            })
        except Exception as e:
            logger.error(f"Error updating nozzle reading: {str(e)}")
            return False, str(e)

    def assign_operator(
        self, nozzle_id: str, operator_id: str
    ) -> tuple[bool, str]:
        """Assign operator to nozzle."""
        try:
            return self.update_document('nozzles', nozzle_id, {
                'assigned_operator_id': operator_id
            })
        except Exception as e:
            logger.error(f"Error assigning operator: {str(e)}")
            return False, str(e)


class AccountHeadService(DatabaseService):
    """Service for managing account heads (payment methods)."""

    def __init__(self):
        """Initialize account head service."""
        super().__init__()

    def create_account_head(
        self,
        name: str,
        head_type: str = "payment",
        description: str = "",
        is_active: bool = True
    ) -> tuple[bool, str]:
        """
        Create a new account head.

        Args:
            name: Account head name (e.g., "Cash", "Bank Transfer")
            head_type: Type of head ("payment", "expense", "income")
            description: Optional description
            is_active: Whether the head is active

        Returns:
            Tuple of (success, message/id)
        """
        try:
            head_id = str(uuid.uuid4())
            data = {
                'id': head_id,
                'name': name,
                'head_type': head_type,
                'description': description,
                'is_active': is_active,
                'created_at': datetime.now().isoformat()
            }
            return self.create_document('account_heads', head_id, data)
        except Exception as e:
            logger.error(f"Error creating account head: {str(e)}")
            return False, str(e)

    def get_payment_methods(self, active_only: bool = True, head_type_filter: Optional[str] = None) -> List[str]:
        """
        Get list of payment method names from account heads.

        Args:
            active_only: If True, return only active payment methods
            head_type_filter: Filter by specific account type (e.g., 'Asset', 'Expense', 'payment')

        Returns:
            List of payment method names
        """
        try:
            # Get all account heads
            all_heads = self.list_documents('account_heads')
            
            # Filter by type and active status in Python
            payment_heads = []
            for h in all_heads:
                # Check for both 'head_type' (new format) and 'account_type' (legacy format)
                head_type = h.get('head_type') or h.get('account_type', '')
                
                # Filter by type if specified
                if head_type_filter:
                    if head_type != head_type_filter:
                        continue
                else:
                    # If no filter, accept common types
                    if head_type not in ['payment', 'Asset', 'Liability', 'Equity', 'Income', 'Expense']:
                        continue
                
                # Check if active
                is_active = h.get('is_active', True) if h.get('is_active') is not None else h.get('status') == 'active'
                if not active_only or is_active:
                    name = h.get('name', '').strip()
                    if name:
                        payment_heads.append(name)
            
            if payment_heads:
                logger.info(f"Loaded {len(payment_heads)} payment methods from account heads")
                return payment_heads
            else:
                logger.warning("No payment methods found in account heads")
                # Return default payment methods if account heads not configured
                return ["Cash"]
        except Exception as e:
            logger.error(f"Error getting payment methods: {str(e)}")
            # Return default payment methods if account heads not configured
            return ["Cash"]
    def list_account_heads(
        self,
        head_type: Optional[str] = None,
        active_only: bool = True
    ) -> List[Dict[str, Any]]:
        """
        List account heads.

        Args:
            head_type: Filter by type (payment, expense, income)
            active_only: Return only active heads

        Returns:
            List of account head dictionaries
        """
        try:
            filters = []
            if head_type:
                filters.append(('head_type', '==', head_type))
            if active_only:
                filters.append(('is_active', '==', True))
            
            return self.list_documents('account_heads', filters if filters else None)
        except Exception as e:
            logger.error(f"Error listing account heads: {str(e)}")
            return []

    def update_account_head(
        self,
        head_id: str,
        data: Dict[str, Any]
    ) -> tuple[bool, str]:
        """Update an account head."""
        return self.update_document('account_heads', head_id, data)

    def delete_account_head(self, head_id: str) -> tuple[bool, str]:
        """Delete (deactivate) an account head."""
        return self.update_document('account_heads', head_id, {'is_active': False})

    def initialize_default_payment_methods(self, user_id: str = None) -> tuple[bool, str]:
        """Initialize default payment methods if none exist."""
        try:
            existing = self.list_account_heads(head_type="payment")
            if existing:
                return True, "Payment methods already exist"
            
            default_methods = [
                ("Cash", "Cash payment")
            ]
            
            for name, desc in default_methods:
                self.create_account_head(name, "payment", desc, True)
            
            logger.info("Default payment methods initialized")
            return True, "Default payment methods created"
        except Exception as e:
            logger.error(f"Error initializing default payment methods: {str(e)}")
            return False, str(e)

