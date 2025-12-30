# Database Schema Documentation

## Overview
Complete Firebase Firestore database schema for PPMS.

## Collections

### 1. Users Collection
Store user accounts with role-based access control.

```
Collection: users
Document ID: {uid} (from Firebase Auth)

Fields:
- uid (string) - Unique identifier from Firebase Auth
- email (string) - User email address
- name (string) - Full name
- role (string) - admin | manager | operator | accountant
- status (string) - active | inactive
- department (string) - User's department
- phone (string, optional) - Contact number
- created_at (timestamp) - Account creation time
- updated_at (timestamp) - Last update time
- created_by (string) - Admin who created this user

Indexes Required:
- role (Ascending)
- status (Ascending)
- created_at (Descending)

Sample Data:
{
  "uid": "usr_001",
  "email": "manager@ppms.com",
  "name": "Ahmed Ali",
  "role": "manager",
  "status": "active",
  "department": "Operations",
  "phone": "+92300XXXXXXX",
  "created_at": "2024-01-15T10:30:00Z",
  "updated_at": "2024-01-15T10:30:00Z",
  "created_by": "admin_001"
}
```

### 2. Fuel Types Collection
Define fuel products available at the pump.

```
Collection: fuel_types
Document ID: {auto-generated}

Fields:
- id (string) - Unique fuel type ID
- name (string) - Petrol | Diesel | CNG
- unit_price (number) - Current price per liter/kg
- tax_percentage (number) - Sales tax percentage
- status (string) - active | inactive
- created_at (timestamp)
- created_by (string)

Indexes Required:
- status (Ascending)

Sample Data:
{
  "id": "fuel_001",
  "name": "Petrol",
  "unit_price": 289.50,
  "tax_percentage": 17.0,
  "status": "active",
  "created_at": "2024-01-01T08:00:00Z",
  "created_by": "admin_001"
}
```

### 3. Tanks Collection
Physical fuel storage tanks at the pump.

```
Collection: tanks
Document ID: {auto-generated}

Fields:
- id (string) - Unique tank ID
- name (string) - Tank identifier (e.g., "Tank A")
- fuel_type_id (string) - Reference to fuel_types
- capacity (number) - Total capacity in liters
- current_stock (number) - Current fuel level
- minimum_stock (number) - Alert threshold
- location (string) - Physical location
- last_reading_date (timestamp) - Last stock update
- created_at (timestamp)
- created_by (string)

Indexes Required:
- fuel_type_id (Ascending)
- status (Ascending)
- current_stock (Ascending)

Sample Data:
{
  "id": "tank_001",
  "name": "Tank A",
  "fuel_type_id": "fuel_001",
  "capacity": 50000.0,
  "current_stock": 35000.0,
  "minimum_stock": 10000.0,
  "location": "West Side",
  "last_reading_date": "2024-12-29T15:00:00Z",
  "created_at": "2024-01-01T08:00:00Z",
  "created_by": "admin_001"
}
```

### 4. Nozzles Collection
Pump dispensers with multiple nozzles.

```
Collection: nozzles
Document ID: {auto-generated}

Fields:
- id (string) - Unique nozzle ID
- machine_id (string) - Parent pump/machine ID
- nozzle_number (number) - Nozzle position (1, 2, 3...)
- fuel_type_id (string) - Reference to fuel_types
- opening_reading (number) - Starting meter value
- closing_reading (number) - Ending meter value
- assigned_operator_id (string, optional) - Current operator
- status (string) - active | inactive | locked | maintenance
- created_at (timestamp)
- created_by (string)

Indexes Required:
- machine_id (Ascending)
- status (Ascending)

Sample Data:
{
  "id": "nozzle_001",
  "machine_id": "pump_001",
  "nozzle_number": 1,
  "fuel_type_id": "fuel_001",
  "opening_reading": 15000.0,
  "closing_reading": 15000.0,
  "assigned_operator_id": "usr_002",
  "status": "active",
  "created_at": "2024-01-01T08:00:00Z",
  "created_by": "admin_001"
}
```

### 5. Readings Collection
Daily meter readings for nozzles.

```
Collection: readings
Document ID: {auto-generated}

Fields:
- id (string) - Unique reading ID
- nozzle_id (string) - Reference to nozzles
- date (timestamp) - Reading date
- opening_reading (number) - Start meter value
- closing_reading (number) - End meter value
- operator_id (string) - Operator who recorded
- verified (boolean) - Verified by manager
- created_at (timestamp)

Calculated Field:
- quantity_sold = closing_reading - opening_reading

Indexes Required:
- nozzle_id (Ascending)
- date (Descending)

Sample Data:
{
  "id": "reading_001",
  "nozzle_id": "nozzle_001",
  "date": "2024-12-29T00:00:00Z",
  "opening_reading": 15000.0,
  "closing_reading": 15847.5,
  "operator_id": "usr_002",
  "verified": true,
  "created_at": "2024-12-29T16:00:00Z"
}
```

### 6. Sales Collection
Individual fuel sale transactions.

```
Collection: sales
Document ID: {auto-generated}

Fields:
- id (string) - Unique sale ID
- date (timestamp) - Sale date/time
- nozzle_id (string) - Reference to nozzles
- fuel_type_id (string) - Reference to fuel_types
- quantity (number) - Liters/kg sold
- unit_price (number) - Price per unit at time of sale
- base_amount (number) - Quantity * unit_price
- tax_amount (number) - Calculated tax
- total_amount (number) - base_amount + tax
- payment_method (string) - cash | credit | easy_paisa | jazz_cash | bank
- customer_id (string, optional) - Reference to customers
- operator_id (string) - Operator who recorded
- shift_id (string) - Reference to shifts
- status (string) - completed | verified | failed
- created_at (timestamp)
- created_by (string)

Indexes Required:
- date (Descending)
- nozzle_id (Ascending)
- fuel_type_id (Ascending)
- customer_id (Ascending)

Sample Data:
{
  "id": "sale_001",
  "date": "2024-12-29T14:30:00Z",
  "nozzle_id": "nozzle_001",
  "fuel_type_id": "fuel_001",
  "quantity": 50.0,
  "unit_price": 289.50,
  "base_amount": 14475.00,
  "tax_amount": 2460.75,
  "total_amount": 16935.75,
  "payment_method": "cash",
  "customer_id": null,
  "operator_id": "usr_002",
  "shift_id": "shift_001",
  "status": "completed",
  "created_at": "2024-12-29T14:30:00Z",
  "created_by": "usr_002"
}
```

### 7. Purchases Collection
Fuel purchase orders from suppliers.

```
Collection: purchases
Document ID: {auto-generated}

Fields:
- id (string) - Unique purchase ID
- date (timestamp) - Purchase date
- supplier_name (string) - Supplier company name
- invoice_number (string) - Invoice reference
- fuel_type_id (string) - Reference to fuel_types
- quantity (number) - Quantity purchased
- rate (number) - Cost per unit
- tax_amount (number) - Tax on purchase
- total_cost (number) - rate * quantity + tax
- tank_id (string) - Reference to tanks
- status (string) - pending | received | verified
- created_at (timestamp)
- created_by (string)

Indexes Required:
- date (Descending)
- supplier_name (Ascending)
- status (Ascending)

Sample Data:
{
  "id": "purchase_001",
  "date": "2024-12-27T10:00:00Z",
  "supplier_name": "National Fuels Ltd",
  "invoice_number": "INV-2024-12-001",
  "fuel_type_id": "fuel_001",
  "quantity": 10000.0,
  "rate": 250.00,
  "tax_amount": 425000.00,
  "total_cost": 2925000.00,
  "tank_id": "tank_001",
  "status": "received",
  "created_at": "2024-12-27T10:00:00Z",
  "created_by": "usr_001"
}
```

### 8. Customers Collection
Customer profiles for credit sales.

```
Collection: customers
Document ID: {auto-generated}

Fields:
- id (string) - Unique customer ID
- name (string) - Customer name
- phone (string) - Contact number
- email (string, optional) - Email address
- address (string) - Physical address
- credit_limit (number) - Maximum credit allowed
- outstanding_balance (number) - Current owed amount
- status (string) - active | inactive
- customer_type (string) - retail | corporate
- created_at (timestamp)
- created_by (string)

Indexes Required:
- status (Ascending)
- outstanding_balance (Ascending)

Sample Data:
{
  "id": "cust_001",
  "name": "Ali's Transport",
  "phone": "+92300XXXXXXX",
  "email": "contact@alistransport.com",
  "address": "123 Main St, Karachi",
  "credit_limit": 500000.0,
  "outstanding_balance": 125000.0,
  "status": "active",
  "customer_type": "corporate",
  "created_at": "2024-01-15T10:30:00Z",
  "created_by": "usr_001"
}
```

### 9. Expenses Collection
Operating expenses and costs.

```
Collection: expenses
Document ID: {auto-generated}

Fields:
- id (string) - Unique expense ID
- date (timestamp) - Expense date
- category (string) - electricity | salary | maintenance | miscellaneous | water | rent
- amount (number) - Expense amount
- description (string) - Details
- bill_image_url (string, optional) - Firebase Storage link
- created_at (timestamp)
- created_by (string)

Indexes Required:
- date (Descending)
- category (Ascending)

Sample Data:
{
  "id": "exp_001",
  "date": "2024-12-29T08:00:00Z",
  "category": "electricity",
  "amount": 25000.0,
  "description": "Monthly electricity bill",
  "bill_image_url": "gs://ppms-bucket/bills/exp_001.pdf",
  "created_at": "2024-12-29T08:00:00Z",
  "created_by": "usr_001"
}
```

### 10. Shifts Collection
Operator shift records.

```
Collection: shifts
Document ID: {auto-generated}

Fields:
- id (string) - Unique shift ID
- date (timestamp) - Shift date
- opening_time (timestamp) - Shift start
- closing_time (timestamp, optional) - Shift end
- operator_id (string) - Reference to users
- opening_cash (number) - Starting cash amount
- closing_cash (number) - Ending cash amount
- expected_cash (number) - Sales + opening cash
- variance (number) - closing_cash - expected_cash
- status (string) - open | closed
- created_at (timestamp)

Indexes Required:
- date (Descending)
- operator_id (Ascending)
- status (Ascending)

Sample Data:
{
  "id": "shift_001",
  "date": "2024-12-29T00:00:00Z",
  "opening_time": "2024-12-29T06:00:00Z",
  "closing_time": "2024-12-29T14:00:00Z",
  "operator_id": "usr_002",
  "opening_cash": 50000.0,
  "closing_cash": 250000.0,
  "expected_cash": 245000.0,
  "variance": 5000.0,
  "status": "closed",
  "created_at": "2024-12-29T14:15:00Z"
}
```

### 11. Payments Collection
Customer payment receipts.

```
Collection: payments
Document ID: {auto-generated}

Fields:
- id (string) - Unique payment ID
- date (timestamp) - Payment date
- customer_id (string) - Reference to customers
- amount (number) - Payment amount
- payment_method (string) - cash | check | bank | easy_paisa | jazz_cash
- reference_number (string, optional) - Cheque/transaction number
- notes (string) - Additional notes
- created_at (timestamp)
- created_by (string)

Indexes Required:
- date (Descending)
- customer_id (Ascending)

Sample Data:
{
  "id": "pay_001",
  "date": "2024-12-28T11:00:00Z",
  "customer_id": "cust_001",
  "amount": 50000.0,
  "payment_method": "bank",
  "reference_number": "TXN-2024-12-001",
  "notes": "Payment for outstanding balance",
  "created_at": "2024-12-28T11:00:00Z",
  "created_by": "usr_001"
}
```

### 12. Reports Collection
Generated business reports.

```
Collection: reports
Document ID: {auto-generated}

Fields:
- id (string) - Unique report ID
- type (string) - daily_sales | monthly_summary | stock | p_and_l | operator_performance | customer_outstanding
- date_from (timestamp) - Report period start
- date_to (timestamp) - Report period end
- data (object) - Report data (varies by type)
- generated_by (string) - User who generated
- created_at (timestamp)

Sample Data:
{
  "id": "rep_001",
  "type": "daily_sales",
  "date_from": "2024-12-29T00:00:00Z",
  "date_to": "2024-12-29T23:59:59Z",
  "data": {
    "total_sales": 500000.0,
    "total_quantity": 1750.0,
    "payment_methods": { "cash": 400000, "credit": 100000 },
    "transactions_count": 45
  },
  "generated_by": "usr_001",
  "created_at": "2024-12-29T23:00:00Z"
}
```

### 13. Audit Logs Collection
Complete audit trail for compliance.

```
Collection: audit_logs
Document ID: {auto-generated}

Fields:
- id (string) - Unique log ID
- action (string) - create | update | delete | login | logout
- entity_type (string) - Collection name affected
- entity_id (string) - Document ID affected
- old_value (object) - Previous values
- new_value (object) - New values
- user_id (string) - User who made change
- timestamp (timestamp) - When change occurred
- ip_address (string) - Source IP address

Indexes Required:
- timestamp (Descending)
- user_id (Ascending)
- entity_type (Ascending)

Sample Data:
{
  "id": "log_001",
  "action": "create",
  "entity_type": "sales",
  "entity_id": "sale_001",
  "old_value": null,
  "new_value": { "id": "sale_001", "quantity": 50, "total_amount": 16935.75 },
  "user_id": "usr_002",
  "timestamp": "2024-12-29T14:30:00Z",
  "ip_address": "192.168.1.100"
}
```

## Indexes

### Required Composite Indexes

```
1. sales: [date DESC, nozzle_id ASC]
2. sales: [date DESC, fuel_type_id ASC]
3. purchases: [date DESC, supplier_name ASC]
4. readings: [nozzle_id ASC, date DESC]
5. shifts: [date DESC, operator_id ASC]
6. expenses: [date DESC, category ASC]
7. audit_logs: [timestamp DESC, user_id ASC]
```

## Data Validation Rules

1. **User Emails**: Unique across collection
2. **Phone Numbers**: Pakistan format or empty
3. **Amounts**: Must be positive numbers
4. **Quantities**: Must be positive numbers
5. **Status Fields**: Limited to predefined values
6. **References**: All foreign keys must point to existing documents
7. **Timestamps**: ISO 8601 format

## Performance Optimization

1. **Query Patterns**:
   - Sales by date range
   - Tank status by fuel type
   - Operator performance by date
   - Customer outstanding balance

2. **Data Size Limits**:
   - Document: Max 1MB
   - Batch write: Max 500 operations
   - Realtime DB: No practical limit but optimize

3. **Caching Strategy**:
   - Cache fuel types (rarely changes)
   - Cache user roles (static)
   - Cache tank capacity (rarely changes)
   - Real-time cache for current stock

## Backup Strategy

- Daily Firestore exports
- Weekly incremental backups
- Monthly full database backup
- Version control for critical data

---

**Version**: 1.0.0  
**Last Updated**: December 2025  
**Status**: Production Ready
