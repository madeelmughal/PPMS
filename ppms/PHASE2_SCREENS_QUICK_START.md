# Phase 2 Screens - Quick Start Guide

## Overview

Phase 2 adds **7 specialized screens** to the PPMS application, providing complete operational interfaces for all business modules. This guide helps you understand and use each screen effectively.

---

## 1. Fuel Management Screen

### Purpose
Manage fuel inventory, fuel types, and tank operations.

### Access
- Navigation: Dashboard → "Manage Fuel" button
- Permissions: MANAGER, ADMIN roles
- Required: At least one fuel type configured

### Key Operations

#### Adding a Fuel Type
1. Click "Add Fuel Type" button
2. Enter fuel name (e.g., "Petrol", "Diesel", "CNG")
3. Set current rate in Rs/Liter
4. Set tax percentage (default 5%)
5. Add optional description
6. Click "Save"

#### Managing Tank Inventory
1. Switch to "Tank Inventory" tab
2. Click "Add Tank" button
3. Enter tank ID/name (e.g., "TANK-01")
4. Select fuel type from dropdown
5. Enter capacity in liters
6. Set current stock level
7. Set minimum level for alerts
8. Specify location (e.g., "Pump #1")
9. Click "Save"

#### Monitoring Stock
- Red alert: Current stock below minimum level
- Green status: Stock level healthy
- Table shows all tanks with real-time status
- Click "Edit" to adjust stock levels

### Best Practices
- Set minimum levels at 20% of tank capacity
- Update stock levels after each tank refill
- Use consistent naming convention for tank IDs
- Document tank locations for quick identification

---

## 2. Sales Entry Screen

### Purpose
Record individual fuel sales transactions.

### Access
- Navigation: Dashboard → "Record Sale" button
- Permissions: OPERATOR, MANAGER roles
- Required: At least one nozzle and fuel type

### Key Operations

#### Recording a Sale
1. Click "Record Sale" button
2. Select nozzle number
3. Select fuel type
4. Enter quantity in liters (e.g., 50.50)
5. Enter unit price (auto-filled from fuel type)
6. Select payment method:
   - Cash (immediate payment)
   - Card (credit/debit card)
   - Credit (customer account)
   - Check (post-dated)
7. Optional: Enter customer name
8. Optional: Enter vehicle number
9. Add notes if needed
10. Click "Save"

#### Daily Summary
Screen automatically displays:
- **Total Sales Today**: Sum of all transactions
- **Total Liters**: Total fuel dispensed
- **Transactions**: Number of sales entries

#### Editing Sales
1. Find transaction in table
2. Click "Edit" button
3. Modify any field
4. Click "Save"

#### Deleting Sales
1. Find transaction in table
2. Click "Delete" button
3. Confirm deletion

### Important Notes
- Quantities must be > 0
- Unit prices must be > 0
- Auto-calculation of total amount
- All transactions logged with timestamp
- Customer tracking enables credit management

### Best Practices
- Record sales immediately after transaction
- Use customer names for credit sales
- Vehicle numbers help with identification
- Review daily totals for reconciliation
- Delete/edit only for genuine corrections

---

## 3. Customer Management Screen

### Purpose
Manage customer profiles and credit accounts.

### Access
- Navigation: Dashboard → "Manage Customers" button
- Permissions: MANAGER, ACCOUNTANT, ADMIN roles

### Key Operations

#### Creating a Customer
1. Click "Add Customer" button
2. Enter customer name (required)
3. Enter phone number (optional)
4. Enter email (optional)
5. Enter address (optional)
6. Enter city (optional)
7. Set credit limit in Rs
8. Select customer type:
   - Retail (single customer)
   - Wholesale (bulk customer)
   - Corporate (organization)
9. Add notes about customer
10. Click "Save"

#### Searching Customers
1. Use "Search" box
2. Search by name, phone, or email
3. Results update instantly
4. Click to select a customer

#### Managing Credit
- Credit Limit: Maximum credit allowed
- Outstanding Balance: Amount owed (red if > 0)
- See details for aging analysis
- Monitor for overdue payments

#### View Customer Details
1. Click "View Details" button
2. See all customer information
3. Credit status summary
4. Outstanding balance amount

#### Updating Customer Info
1. Click "Edit" button
2. Modify any field
3. Update credit limit if needed
4. Click "Save"

### Customer Types

**Retail**: 
- Single customer purchases
- Lower typical credit limits
- Example: Individual vehicle owners

**Wholesale**:
- Bulk purchases
- Higher credit limits
- Example: Transport companies

**Corporate**:
- Organization accounts
- Highest credit limits
- Example: Private companies

### Best Practices
- Record complete information for tracking
- Set realistic credit limits
- Monitor outstanding balances weekly
- Follow up on overdue accounts
- Keep notes updated for reference

---

## 4. Expense Management Screen

### Purpose
Record and track daily business expenses.

### Access
- Navigation: Dashboard → "Record Expense" button (if available)
- Permissions: MANAGER, ACCOUNTANT, ADMIN roles

### Key Operations

#### Recording an Expense
1. Click "Add Expense" button
2. Select expense category:
   - **Salary**: Employee salaries
   - **Utilities**: Water, electricity, phone
   - **Maintenance**: Regular upkeep
   - **Repairs**: Equipment/building repairs
   - **Supplies**: Office and operational supplies
   - **Rent**: Facility rent
   - **Insurance**: Insurance premiums
   - **Miscellaneous**: Other expenses
3. Enter description (required)
4. Enter amount in Rs
5. Select expense date
6. Select payment method
7. Enter vendor/payee name (optional)
8. Add notes (optional)
9. Click "Save"

#### Filtering by Category
1. Use "Category Filter" dropdown
2. Select specific category
3. Table updates to show only that category
4. Select "All" to see all expenses

#### Expense Summary
Screen shows:
- **Today's Expenses**: Sum for current date
- **Monthly Expenses**: Sum for current month
- **Categories**: Number of expense categories

#### Editing Expenses
1. Find expense in table
2. Click "Edit"
3. Modify any field
4. Click "Save"

#### Deleting Expenses
1. Click "Delete"
2. Confirm deletion
3. (Note: Keep record for audit trail)

### Payment Methods
- **Cash**: Direct payment
- **Check**: Cheque issued
- **Card**: Debit/credit card
- **Transfer**: Bank transfer

### Best Practices
- Record expenses on the day they occur
- Categorize accurately for reporting
- Keep vendor receipts for audit
- Note payment method for reconciliation
- Review monthly trends for budget planning

---

## 5. Shift Management Screen

### Purpose
Manage operator shifts and cash reconciliation.

### Access
- Navigation: Dashboard → "Manage Shifts" button
- Permissions: MANAGER, ADMIN roles
- Required: At least one operator assigned

### Key Operations

#### Opening a Shift
1. Click "Open New Shift" button
2. Select operator from list
3. Enter opening cash amount
4. Set opening time (auto-filled with current time)
5. Add opening notes (optional)
6. Click "Save"

#### Shift Status Indicators
- **Open**: Active shift in progress
- **Closed**: Shift completed
- Color coded: Green = Open, Gray = Closed

#### Closing a Shift
1. Find open shift in table
2. Click "Close Shift" button
3. Set closing time
4. Enter closing cash amount
5. System shows expected sales
6. Enter any closure notes
7. Click "Save"

#### Viewing Shift Details
1. Click "View Details" button
2. See complete shift information:
   - Operator name
   - Start and end times
   - Duration in hours
   - Opening and closing cash
   - Sales during shift
   - Notes

#### Shift Summary
Screen displays:
- **Active Shifts**: Number currently open
- **Total Hours Today**: Sum of all shift durations
- **Today's Shifts**: Number of shifts in current day

#### Shift Reconciliation
Automatic calculations:
- **Duration**: End time - Start time
- **Expected Sales**: Should match recorded sales
- **Cash Variance**: Closing cash - Opening cash - Sales
- **Anomalies**: Detects short or excess cash

### Best Practices
- Open shift at start of operator's duty
- Close shift immediately after operator leaves
- Record accurate opening and closing cash
- Use notes for special circumstances
- Review variances for discrepancies
- Investigate large cash differences

### Operator Performance Insights
- Hours worked per operator
- Sales per shift
- Cash handling accuracy
- Shift patterns and trends

---

## 6. Reports Screen

### Purpose
Generate comprehensive business intelligence reports.

### Access
- Navigation: Dashboard → "View Reports" button
- Permissions: MANAGER, ACCOUNTANT, ADMIN roles

### Available Reports

#### 1. Daily Sales Report
**Purpose**: Summary of daily fuel sales
- **Inputs**: Select date, choose format (PDF/Excel)
- **Contains**: 
  - Daily sales transactions
  - Total amount and quantity
  - Payment method breakdown
  - Nozzle-wise breakdown
  - Fuel type-wise breakdown
- **Use Case**: Daily reconciliation, bank deposits

#### 2. P&L Statement
**Purpose**: Profit and loss analysis
- **Inputs**: Date range, format selection
- **Contains**:
  - Revenue (fuel sales)
  - Cost of goods (fuel purchases)
  - Operating expenses
  - Net profit/loss
  - Profit margin %
- **Use Case**: Management reporting, trend analysis

#### 3. Tax Summary
**Purpose**: Tax collection and calculation
- **Inputs**: Date range, format
- **Contains**:
  - Sales by tax rate
  - Tax amount collected
  - GST/VAT breakdown
  - Remittance due
- **Use Case**: Tax compliance, remittance calculation

#### 4. Inventory Report
**Purpose**: Current stock valuation
- **Inputs**: Format only
- **Contains**:
  - All tanks and fuel types
  - Current stock in liters
  - Current value in Rs (at current rates)
  - Capacity utilization %
  - Reorder requirements
- **Use Case**: Balance sheet, stock verification

#### 5. Operator Performance
**Purpose**: Individual operator metrics
- **Inputs**: Date range, format
- **Contains**:
  - Sales per operator
  - Shift efficiency
  - Cash handling accuracy
  - Performance ranking
- **Use Case**: Bonus calculation, performance review

#### 6. Credit Aging
**Purpose**: Customer credit analysis
- **Inputs**: Format only
- **Contains**:
  - Customers by aging bucket
  - Current to 30 days overdue
  - 30-60 days, 60+ days
  - Credit utilization %
- **Use Case**: Collection strategy, write-offs

### Generating Reports

1. **Select Report Type**: Click on tab
2. **Configure Parameters**: 
   - Set date range if needed
   - Select format (PDF or Excel)
3. **Generate**: Click "Generate Report" button
4. **Progress**: Watch progress bar
5. **Open File**: Auto-prompt to open generated file
6. **Export**: Save to desired location

### Report Formats

**PDF**:
- Professional appearance
- Print-friendly
- Good for presentations
- Smaller file size

**Excel**:
- Data analysis capability
- Pivot table support
- Charting capability
- Better for detailed review

### Best Practices
- Generate daily sales reports for reconciliation
- Run P&L monthly for management review
- Tax reports quarterly for compliance
- Inventory reports weekly for stock planning
- Operator reports monthly for performance
- Archive reports for audit trail

---

## 7. Settings & User Management Screen (Admin Only)

### Purpose
Administrative user and system configuration.

### Access
- Navigation: Dashboard → "Settings" button (ADMIN only)
- Permissions: ADMIN role exclusively
- Cannot be accessed by other roles

### Key Operations

#### User Management Tab

##### Creating a User
1. Click "Add User" button
2. Enter full name (required)
3. Enter email (required, unique)
4. Enter phone (optional)
5. Select role:
   - **ADMIN**: Full system access
   - **MANAGER**: Operational management
   - **OPERATOR**: Sales entry only
   - **ACCOUNTANT**: Financial/reporting
6. Set status: Active or Inactive
7. Enter password (min 8 characters, required)
8. Confirm password
9. Select permissions:
   - Record Sales
   - Manage Fuel
   - Manage Customers
   - Record Expenses
   - View Reports
10. Click "Save"

##### Editing Users
1. Click "Edit" button on user row
2. Modify name, phone, status
3. Cannot change email (Firebase constraint)
4. Update permissions as needed
5. Click "Save"

##### Resetting Password
1. Click "Reset Password" button
2. Confirm action
3. System sends reset email to user
4. User follows email link to set new password

##### Deactivating Users
1. Edit user
2. Change status to "Inactive"
3. User cannot login (permissions revoked)
4. Can be reactivated later

##### Deleting Users
1. Click "Delete" button
2. Confirm action
3. User completely removed from system
4. (Note: Consider deactivating instead)

#### Roles & Permissions

**ADMIN**:
- All permissions enabled
- User management access
- Settings modification
- Can perform all operations

**MANAGER**:
- Fuel management
- Sales monitoring
- Customer management
- Expense tracking
- Reports viewing
- Shift management
- Cannot: User management, Settings

**OPERATOR**:
- Record sales
- View own shifts
- Limited to sales transactions
- Cannot: Fuel management, expenses, reports

**ACCOUNTANT**:
- View reports
- Customer management (credit)
- Expense tracking
- Cannot: Sales recording, Fuel management

#### System Settings Tab

##### Business Configuration
1. Enter business name
2. Enter business address
3. Set default tax rate (%)
4. Select backup location

##### Saving Settings
1. Configure all fields
2. Click "Save Settings"
3. Settings applied globally

#### Audit Log Tab

**Displays**:
- All user actions
- Timestamps
- User identification
- Action type
- Module affected
- Action details

**Use for**:
- Security monitoring
- Compliance verification
- Troubleshooting issues
- User behavior analysis

### User Summary
Screen shows:
- **Total Users**: Count of all users
- **Active Users**: Count of active users

### Security Considerations
- Change default admin password immediately
- Create per-user accounts (no shared accounts)
- Regular password resets recommended
- Monitor audit log for suspicious activity
- Deactivate unused accounts
- Implement strong password policy

### Best Practices
- Create users before they start
- Assign minimal required permissions
- Regular access review (quarterly)
- Document user roles clearly
- Test new user access before assigning
- Archive audit logs regularly
- Never share admin credentials

---

## Common Workflows

### Daily Operations

**Morning (Opening)**:
1. Open Shift (Shift Management)
   - Verify opening cash
   
2. Check Fuel Levels (Fuel Management)
   - Monitor tank levels
   - Check for low-stock alerts

**During Day**:
3. Record Sales (Sales Entry)
   - Enter each transaction
   - Track customer purchases
   - Monitor payment methods

4. Record Expenses (Expense Management)
   - Document daily expenses
   - Maintain receipt records

**Evening (Closing)**:
5. Close Shift (Shift Management)
   - Record closing cash
   - Verify sales total
   - Note discrepancies

6. Daily Reconciliation
   - Run Daily Sales Report
   - Verify cash match
   - Address variances

### Weekly Operations
1. Review Operator Performance
2. Check Customer Credit Aging
3. Verify Fuel Stock Levels
4. Review Expense Categories

### Monthly Operations
1. Generate P&L Statement
2. Tax Summary Report
3. Inventory Valuation
4. Customer Aging Analysis
5. Manager Review Meeting

### Quarterly Operations
1. User Access Review
2. System Settings Audit
3. Archive Historical Data
4. Compliance Check (Tax/Legal)

---

## Troubleshooting

### Screen Won't Load
- Check Firebase connection
- Verify user permissions
- Check error logs in console
- Restart application

### Data Not Saving
- Verify Firebase connectivity
- Check input validation messages
- Confirm user permissions
- Review error messages

### Reports Not Generating
- Check date ranges
- Verify data exists for selected period
- Check available storage space
- Review report generation progress

### Missing User Roles
- Admin creates user first
- Assign proper role
- User logs out/back in
- Permissions take effect

### Cash Variance Issues
- Check closing cash amount
- Verify sales total in system
- Review recorded sales
- Check for double-entry errors
- Review payment method breakdown

---

## Tips & Tricks

### Faster Data Entry
- Use Tab key to move between fields
- Keyboard shortcuts for common actions
- Pre-fill customer info for repeat customers
- Use copy-paste for similar entries

### Better Reporting
- Generate reports at consistent time
- Use Excel for data analysis
- Create custom pivot tables
- Track trends over time

### Efficient Reconciliation
- Close shift daily without fail
- Match sales to cash collected
- Investigate large variances immediately
- Keep detailed notes for exceptions

### User Management
- Create admin account first
- Limit admin user count
- Regular permission audits
- Document role assignments

---

## Support & Documentation

For detailed information:
- Review individual screen documentation
- Check database schema guide
- Review API reference
- Check installation guide
- Consult security rules documentation

---

## Next Steps

After mastering Phase 2 screens:
1. Setup test data via Firebase initialization
2. Train operators on Sales Entry
3. Configure managers on reporting
4. Setup administrators on user management
5. Establish daily reconciliation procedures
6. Create backup strategy
7. Deploy to production

---

**Phase 2 Screens Complete** ✅
All operational interfaces ready for production use.
