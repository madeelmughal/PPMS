# Petrol Pump Management System (PPMS)

A comprehensive Python desktop application for managing petrol pump operations with complete fuel management, sales tracking, expense management, and detailed financial reporting.

## Features

### ✅ Core Modules Implemented
1. **Authentication Module** - Firebase-based secure login with role-based access
2. **Fuel Management** - Tank management, fuel purchases, stock monitoring
3. **Nozzle & Dispenser Management** - Multi-nozzle dispenser management with meter readings
4. **Daily Sales Management** - Per-nozzle/per-fuel-type sales with multiple payment methods
5. **Customer & Credit Management** - Customer profiles, credit limits, aging reports
6. **Expense Management** - Categorized expense tracking with bill attachments
7. **Shift Management** - Shift open/close, operator-wise reconciliation
8. **Profit & Loss Calculation** - Automated P&L generation with tax summaries
9. **Reporting Module** - PDF/Excel export for comprehensive business reports
10. **Dashboard** - Real-time monitoring with stock alerts and pending credits

### 🔐 User Roles & Access Control
- **Admin** - Full system control
- **Manager** - Daily operations and reports
- **Operator** - Fuel sales entry only
- **Accountant** - Ledger, expenses, and profit reports

## Technology Stack

- **Language:** Python 3.x
- **UI Framework:** PyQt5
- **Database:** Firebase (Firestore + Realtime DB)
- **Authentication:** Firebase Auth
- **Reporting:** ReportLab, Pandas, openpyxl
- **Architecture:** MVC + Modular Design Pattern

## Project Structure

```
ppms/
├── src/
│   ├── config/              # Configuration files
│   ├── models/              # Data models
│   ├── services/            # Business logic services
│   ├── ui/
│   │   ├── screens/         # UI screens
│   │   └── widgets/         # Reusable widgets
│   ├── utils/               # Utility functions
│   ├── reports/             # Reporting modules
│   └── main.py              # Application entry point
├── tests/                   # Unit tests
├── docs/                    # Documentation
├── logs/                    # Application logs
├── requirements.txt         # Dependencies
├── README.md
└── .env.example            # Environment configuration template
```

## Installation

### Prerequisites
- Python 3.8 or higher
- Firebase project with service account credentials
- Windows 10/11 or compatible OS

### Setup Steps

1. **Clone the repository:**
   ```bash
   cd d:\prog\ppms
   ```

2. **Create virtual environment:**
   ```bash
   python -m venv venv
   venv\Scripts\activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure Firebase:**
   - Download `serviceAccountKey.json` from Firebase Console
   - Copy to project root directory
   - Update `.env` with Firebase credentials

5. **Run the application:**
   ```bash
   python src/main.py
   ```

## Firebase Data Structure

### Collections

#### users
```
{
  uid: string,
  email: string,
  name: string,
  role: string (admin|manager|operator|accountant),
  status: string (active|inactive),
  department: string,
  created_at: timestamp,
  updated_at: timestamp,
  created_by: string
}
```

#### fuel_types
```
{
  id: string,
  name: string (Petrol|Diesel|CNG),
  unit_price: number,
  tax_percentage: number,
  status: string (active|inactive),
  created_at: timestamp,
  created_by: string
}
```

#### tanks
```
{
  id: string,
  name: string,
  fuel_type_id: string (reference),
  capacity: number,
  current_stock: number,
  minimum_stock: number,
  last_reading_date: timestamp,
  location: string,
  created_at: timestamp,
  created_by: string
}
```

#### nozzles
```
{
  id: string,
  machine_id: string,
  nozzle_number: number,
  fuel_type_id: string (reference),
  opening_reading: number,
  closing_reading: number,
  assigned_operator_id: string,
  status: string (active|inactive|locked),
  created_at: timestamp,
  created_by: string
}
```

#### readings
```
{
  id: string,
  nozzle_id: string (reference),
  date: timestamp,
  opening_reading: number,
  closing_reading: number,
  quantity_sold: number,
  operator_id: string (reference),
  verified: boolean,
  created_at: timestamp
}
```

#### sales
```
{
  id: string,
  date: timestamp,
  nozzle_id: string (reference),
  fuel_type_id: string (reference),
  quantity: number,
  unit_price: number,
  base_amount: number,
  tax_amount: number,
  total_amount: number,
  payment_method: string (cash|credit|easy_paisa|jazz_cash|bank),
  customer_id: string (optional, reference),
  operator_id: string (reference),
  shift_id: string (reference),
  created_at: timestamp,
  created_by: string
}
```

#### purchases
```
{
  id: string,
  date: timestamp,
  supplier_name: string,
  invoice_number: string,
  fuel_type_id: string (reference),
  quantity: number,
  rate: number,
  tax_amount: number,
  total_cost: number,
  tank_id: string (reference),
  status: string (pending|received|verified),
  created_at: timestamp,
  created_by: string
}
```

#### customers
```
{
  id: string,
  name: string,
  phone: string,
  email: string,
  address: string,
  credit_limit: number,
  outstanding_balance: number,
  status: string (active|inactive),
  customer_type: string (retail|corporate),
  created_at: timestamp,
  created_by: string
}
```

#### expenses
```
{
  id: string,
  date: timestamp,
  category: string (electricity|salary|maintenance|miscellaneous),
  amount: number,
  description: string,
  bill_image_url: string (optional),
  created_at: timestamp,
  created_by: string
}
```

#### shifts
```
{
  id: string,
  date: timestamp,
  opening_time: timestamp,
  closing_time: timestamp,
  operator_id: string (reference),
  opening_cash: number,
  closing_cash: number,
  expected_cash: number,
  variance: number,
  status: string (open|closed),
  created_at: timestamp
}
```

#### reports
```
{
  id: string,
  type: string (daily_sales|monthly_summary|stock|p&l|operator_performance|customer_outstanding),
  date_from: timestamp,
  date_to: timestamp,
  data: object,
  generated_by: string,
  created_at: timestamp
}
```

#### audit_logs
```
{
  id: string,
  action: string,
  entity_type: string,
  entity_id: string,
  old_value: object,
  new_value: object,
  user_id: string (reference),
  timestamp: timestamp,
  ip_address: string
}
```

## Firebase Security Rules

See `docs/firebase-security-rules.json` for complete security rules.

## Usage Examples

### Admin Dashboard
- View real-time stock levels
- Monitor daily sales performance
- Review operator performance
- Access all reports
- Manage users and system settings

### Manager Operations
- Track daily sales
- Manage fuel purchases
- Monitor tank levels
- Review expense reports
- Generate business reports

### Operator
- Record nozzle readings
- Process fuel sales
- Handle customer transactions
- Submit shift reports

### Accountant
- Review financial reports
- Track expenses
- Generate P&L statements
- Monitor outstanding credits

## Testing

```bash
python -m pytest tests/
```

## Deployment

### Windows EXE Generation

```bash
pyinstaller --onefile --windowed --name PPMS src/main.py
```

## Key Features

### Real-Time Monitoring
- Live stock levels across all tanks
- Daily sales performance metrics
- Pending customer credits
- Low stock alerts

### Automated Calculations
- Sale quantity from meter readings
- Fuel costs with tax calculations
- Profit margins per transaction
- Monthly P&L summaries

### Comprehensive Reporting
- Daily sales breakdown
- Monthly revenue trends
- Operator performance metrics
- Customer credit aging
- Profit & loss statements

### Security & Audit
- Role-based access control
- Complete audit trail
- Transaction logging
- User activity tracking

## Database Transaction Safety

All critical operations use Firestore transactions:
- Fuel purchase and tank update
- Sales and stock reconciliation
- Shift open/close operations
- Credit adjustments

## Offline Tolerance

The application can:
- Cache essential data locally
- Queue operations for sync
- Display cached reports
- Notify when sync is pending

## Future Enhancements

1. **Multi-Location Support** - Manage multiple petrol pump locations
2. **Mobile App** - Flutter-based companion app for operators
3. **Advanced Analytics** - ML-based sales forecasting
4. **Integration** - ERP system and accounting software integration
5. **Hardware Integration** - Direct pump meter API integration
6. **SMS/Email Notifications** - Real-time alerts for critical events
7. **QR Code Integration** - Customer quick payment links
8. **Blockchain** - Immutable audit trail

## Support & Documentation

- Complete API documentation in `docs/`
- Database schema in `docs/database-schema.md`
- UI flow diagram in `docs/ui-flow.md`
- Installation guide in `docs/INSTALLATION.md`
- Sample test data in `docs/sample-data.json`

## License

Proprietary - Petrol Pump Management System

## Support

For issues, contact your system administrator or refer to documentation in `docs/` folder.

---

**Version:** 1.0.0  
**Last Updated:** December 2025  
**Status:** Production Ready
