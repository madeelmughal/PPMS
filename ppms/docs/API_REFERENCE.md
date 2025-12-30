# API Reference & Developer Guide

## Overview

The Petrol Pump Management System (PPMS) provides a comprehensive set of services for managing petrol pump operations. This guide documents the API and services available for developers.

## Core Services

### 1. Authentication Service

Manages user authentication and session handling.

#### Methods

**login_with_email_password(email, password)**
- Authenticates user with email and password
- Returns: (success: bool, message: str, user: User)
- Raises: None

Example:
```python
auth_service = AuthenticationService()
success, msg, user = auth_service.login_with_email_password(
    "user@ppms.com", 
    "password123"
)
```

**create_user(email, password, name, role, department)**
- Creates new user account
- Returns: (success: bool, message: str, user_uid: str)
- Roles: 'admin', 'manager', 'operator', 'accountant'

Example:
```python
success, msg, uid = auth_service.create_user(
    "newuser@ppms.com",
    "SecurePass@123",
    "John Doe",
    "manager",
    "Operations"
)
```

**disable_user(user_id)**
- Deactivates user account
- Returns: (success: bool, message: str)

**change_password(user_id, new_password)**
- Changes user password
- Returns: (success: bool, message: str)

**has_permission(permission)**
- Checks if current user has permission
- Returns: bool

### 2. Database Service

Generic CRUD operations for database documents.

#### Methods

**create_document(collection, document_id, data, user_id)**
- Creates new document
- Returns: (success: bool, message: str)

**read_document(collection, document_id)**
- Reads document by ID
- Returns: Dict or None

**update_document(collection, document_id, data)**
- Updates document
- Returns: (success: bool, message: str)

**delete_document(collection, document_id)**
- Deletes document
- Returns: (success: bool, message: str)

**list_documents(collection, filters)**
- Lists documents with optional filters
- Filters format: [(field, operator, value), ...]
- Returns: List[Dict]

Example:
```python
db_service = DatabaseService()

# Create
success, msg = db_service.create_document(
    'customers',
    'cust_001',
    {'name': 'Ali Transport', 'phone': '+92300000000'},
    user_id='admin_001'
)

# List with filter
customers = db_service.list_documents(
    'customers',
    [('status', '==', 'active')]
)
```

### 3. Fuel Service

Manage fuel types and related operations.

#### Methods

**create_fuel_type(name, unit_price, tax_percentage, user_id)**
- Creates new fuel type
- Returns: (success: bool, message: str, fuel_id: str)

**list_fuel_types()**
- Gets all active fuel types
- Returns: List[FuelType]

### 4. Tank Service

Manage fuel storage tanks.

#### Methods

**create_tank(name, fuel_type_id, capacity, minimum_stock, user_id)**
- Creates new tank
- Returns: (success: bool, message: str, tank_id: str)

**get_tank(tank_id)**
- Gets tank by ID
- Returns: Tank or None

**update_tank_stock(tank_id, new_stock)**
- Updates tank stock level
- Returns: (success: bool, message: str)

**list_tanks()**
- Gets all tanks
- Returns: List[Tank]

### 5. Sales Service

Process and track fuel sales.

#### Methods

**record_sale(sale, user_id)**
- Records new fuel sale
- Returns: (success: bool, message: str, sale_id: str)

**list_daily_sales(date)**
- Gets sales for specific date
- Returns: List[Sale]

### 6. Business Logic Service

High-level business calculations and operations.

#### Sales Calculation Engine

```python
from src.services.business_logic import SalesCalculationEngine

engine = SalesCalculationEngine()

# Calculate sale amount with tax
result = engine.calculate_sale_amount(
    quantity=50.0,
    unit_price=289.50,
    tax_percentage=17.0
)
# Returns: {'base_amount': 14475.0, 'tax_amount': 2460.75, 'total_amount': 16935.75}

# Calculate daily sales summary
summary = engine.calculate_daily_sales(sales_list)
```

#### Stock Management Engine

```python
from src.services.business_logic import StockManagementEngine

engine = StockManagementEngine()

# Update stock after sale
success, msg = engine.update_tank_stock('tank_001', 50.0)

# Add stock from purchase
success, msg = engine.add_stock_from_purchase('tank_001', 1000.0)

# Check low stock tanks
low_stock = engine.check_low_stock()
```

#### Shift Reconciliation Engine

```python
from src.services.business_logic import ShiftReconciliationEngine

engine = ShiftReconciliationEngine()

# Open shift
success, msg, shift_id = engine.open_shift('operator_001', 50000.0)

# Close shift with reconciliation
success, msg, reconciliation = engine.close_shift('shift_001', 245000.0)
```

#### Profit & Loss Calculator

```python
from src.services.business_logic import ProfitAndLossCalculator

calc = ProfitAndLossCalculator()

# Calculate daily P&L
daily_pl = calc.calculate_daily_pl(datetime.now())
# Returns: {'revenue': 500000, 'expenses': 100000, 'net_profit': 400000, ...}

# Calculate monthly P&L
monthly_pl = calc.calculate_monthly_pl(2024, 12)
```

#### Customer Credit Manager

```python
from src.services.business_logic import CustomerCreditManager

manager = CustomerCreditManager()

# Get credit status
status = manager.get_customer_credit_status('cust_001')

# Record payment
success, msg = manager.record_payment('cust_001', 50000.0)

# Get aging report
aging = manager.get_aging_report()
```

## Data Models

### User Model
```python
User(
    uid: str,
    email: str,
    name: str,
    role: UserRole,
    status: str = "active",
    department: str = "",
    phone: Optional[str] = None
)
```

### FuelType Model
```python
FuelType(
    id: str,
    name: str,
    unit_price: float,
    tax_percentage: float = 10.0,
    status: str = "active"
)
```

### Tank Model
```python
Tank(
    id: str,
    name: str,
    fuel_type_id: str,
    capacity: float,
    current_stock: float,
    minimum_stock: float,
    location: str = "",
    last_reading_date: Optional[datetime] = None
)

# Properties
tank.stock_percentage  # Returns percentage of capacity
tank.is_low_stock      # Returns True if below minimum
```

### Sale Model
```python
Sale(
    id: str,
    date: datetime,
    nozzle_id: str,
    fuel_type_id: str,
    quantity: float,
    unit_price: float,
    base_amount: float,
    tax_amount: float,
    total_amount: float,
    payment_method: PaymentMethod,
    operator_id: str,
    shift_id: str,
    customer_id: Optional[str] = None,
    status: TransactionStatus = TransactionStatus.COMPLETED
)
```

## Utility Functions

### Validators
```python
from src.utils.validators import (
    validate_email,
    validate_phone,
    validate_currency,
    validate_sale_data,
    validate_purchase_data,
    validate_customer_data
)

# Email validation
is_valid = validate_email("user@example.com")

# Phone validation (Pakistan format)
is_valid = validate_phone("+92300XXXXXXX")

# Currency validation
is_valid = validate_currency(1000.50)

# Sale data validation
success, msg = validate_sale_data(
    quantity=50.0,
    unit_price=289.50,
    fuel_type_id="fuel_001",
    nozzle_id="nozzle_001"
)
```

### Formatting Functions
```python
from src.utils.validators import (
    format_currency,
    format_datetime,
    format_date,
    calculate_tax,
    calculate_profit_margin
)

# Format currency
display = format_currency(1000.50)  # "Rs. 1,000.50"

# Calculate tax
tax = calculate_tax(1000, 17)  # 170

# Calculate profit margin
margin = calculate_profit_margin(250, 289.50)  # 15.8%
```

## Report Generation

### PDF Reports
```python
from src.reports.report_generator import PDFReportGenerator

generator = PDFReportGenerator(title="Daily Sales Report")

# Generate daily sales report
success, filepath = generator.generate_daily_sales_report(sales_data)

# Generate P&L report
success, filepath = generator.generate_p_and_l_report(revenue, expenses)
```

### Excel Reports
```python
from src.reports.report_generator import ExcelReportGenerator

generator = ExcelReportGenerator(title="Sales Export")

# Generate sales Excel
success, filepath = generator.generate_sales_excel(sales_data)

# Generate stock report
success, filepath = generator.generate_fuel_stock_excel(tank_data)
```

## Firebase Collections

All operations use the following Firestore collections:

- `users` - User accounts and profiles
- `fuel_types` - Available fuel products
- `tanks` - Fuel storage tanks
- `nozzles` - Pump dispensers
- `readings` - Meter readings
- `sales` - Fuel sales transactions
- `purchases` - Fuel purchases
- `customers` - Customer profiles
- `expenses` - Operating expenses
- `shifts` - Operator shifts
- `payments` - Customer payments
- `reports` - Generated reports
- `audit_logs` - Activity audit trail

## Error Handling

All services return `(success, message)` tuples or `(success, message, data)` tuples.

```python
success, message, data = service.operation()

if success:
    # Process data
    print(f"Operation completed: {message}")
else:
    # Handle error
    print(f"Error: {message}")
```

## Permission Checking

Check permissions before performing operations:

```python
if auth_service.has_permission('manage_fuel'):
    # Perform fuel management
    pass
else:
    # Show access denied
    pass
```

## Logging

Application uses structured logging:

```python
from src.config.logger_config import setup_logger

logger = setup_logger(__name__)
logger.info("User logged in successfully")
logger.warning("Low stock detected")
logger.error(f"Database operation failed: {error}")
```

## Configuration

Access application settings:

```python
from src.config.firebase_config import AppConfig, DatabaseConfig

app_name = AppConfig.APP_NAME
currency = AppConfig.CURRENCY_SYMBOL
roles = AppConfig.ROLES
fuel_types = AppConfig.FUEL_TYPES
```

---

**Version**: 1.0.0  
**Last Updated**: December 2025  
**Status**: Production Ready
