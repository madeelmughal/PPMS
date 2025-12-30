# UI Flow Diagram & Navigation

## Application Navigation Structure

```
┌─────────────────────────────────────────────────────────────┐
│                     PPMS Application                         │
└─────────────────────────────────────────────────────────────┘
                           │
                    ┌──────▼──────┐
                    │ Login Screen │
                    └──────┬──────┘
                           │
                    ┌──────▼──────────────┐
                    │  Authenticate User  │
                    └──────┬──────────────┘
                           │
        ┌──────────────────┼──────────────────┐
        │                  │                  │
        ▼                  ▼                  ▼
   [Invalid]         [Valid Auth]       [Failed]
        │          Role Check             │
        │              │                  │
        │    ┌─────────┼─────────┐       │
        │    │         │         │       │
        │    ▼         ▼         ▼       │
        │  Admin    Manager   Operator   │
        │    │         │         │       │
        │    │         │         │       │
        └────┼─────────┴─────────┼───────┘
             │                   │
             └────────┬──────────┘
                      │
              ┌───────▼────────┐
              │ Main Dashboard │
              └───────┬────────┘
                      │
        ┌─────────────┼──────────────┐
        │             │              │
        ▼             ▼              ▼
    [Admin Panel] [Manager Panel] [Operator Panel]
```

## Screen Hierarchy

### 1. Login Screen
```
┌────────────────────────────────────┐
│  Petrol Pump Management System     │
│  Login to Your Account             │
├────────────────────────────────────┤
│ Email: [________________]          │
│ Password: [________________]       │
│ ☐ Remember me                      │
│ [     LOGIN BUTTON     ]           │
│ [Forgot Password?]                 │
└────────────────────────────────────┘
```

### 2. Dashboard Screen
```
┌────────────────────────────────────────────────┐
│ Welcome, Muhammad Hassan        [Logout]       │
├────────────────────────────────────────────────┤
│ ┌──────────────┐ ┌──────────────┐             │
│ │ Stock Level  │ │ Today Sales  │             │
│ │  35,000 L    │ │ Rs. 500,000  │             │
│ └──────────────┘ └──────────────┘             │
│ ┌──────────────┐ ┌──────────────┐             │
│ │ Monthly Prof │ │  Low Alerts  │             │
│ │Rs. 2,500,000 │ │   3 Tanks    │             │
│ └──────────────┘ └──────────────┘             │
│ ┌──────────────┐ ┌──────────────┐             │
│ │Pending Credit│ │Active Shifts │             │
│ │ Rs. 250,000  │ │   2 Shifts   │             │
│ └──────────────┘ └──────────────┘             │
│                                               │
│ [Record Sale] [Manage Fuel] [Manage Nozzles] │
│ [View Reports] [Manage Expenses] [Shift Mgmt]│
└────────────────────────────────────────────────┘
```

### 3. Fuel Management Screen
```
┌──────────────────────────────────────┐
│ Fuel Management          [Back] [+Add] │
├──────────────────────────────────────┤
│ Fuel Types:                          │
│ ┌────────────────────────────────┐  │
│ │ Type   │ Price  │ Tax │ Status │  │
│ ├────────┼────────┼─────┼────────┤  │
│ │ Petrol │ 289.50 │ 17% │ Active │  │
│ │ Diesel │ 279.25 │ 17% │ Active │  │
│ │ CNG    │ 140.00 │ 17% │ Active │  │
│ └────────────────────────────────┘  │
│                                     │
│ Tanks:                              │
│ ┌────────────────────────────────┐  │
│ │ Tank │ Fuel│ Stock │Min │Alert │  │
│ ├──────┼──────┼───────┼─────┼────┤  │
│ │Tank A│ Petrol │35K │ 10K │ No │  │
│ │Tank B│ Diesel │28K │ 9K  │ No │  │
│ │Tank C│ CNG   │22K │ 6K  │ Yes│  │
│ └────────────────────────────────┘  │
│                                     │
│ [Add Fuel Type] [Add Tank]          │
└──────────────────────────────────────┘
```

### 4. Sales Recording Screen
```
┌──────────────────────────────────────┐
│ Record Fuel Sale         [Back] [Save] │
├──────────────────────────────────────┤
│ Nozzle: [Nozzle 1      ]             │
│ Fuel Type: [Petrol    ▼]             │
│ Quantity: [50.00] Liters             │
│ Unit Price: [289.50]                 │
│ Tax %: [17.00]                       │
│                                      │
│ Base Amount: Rs. 14,475.00           │
│ Tax Amount: Rs. 2,460.75             │
│ Total Amount: Rs. 16,935.75          │
│                                      │
│ Payment Method: [Cash      ▼]        │
│ Customer: [Optional     ]            │
│ Shift: [Shift 1         ]            │
│                                      │
│ [     SAVE SALE    ]  [CANCEL]       │
└──────────────────────────────────────┘
```

### 5. Customer Management Screen
```
┌──────────────────────────────────────┐
│ Customer Management      [Back] [+Add] │
├──────────────────────────────────────┤
│ Search: [_______________]            │
│                                      │
│ ┌────────────────────────────────┐  │
│ │ Customer │ Phone │ Credit Limit│  │
│ │          │       │ Balance     │  │
│ ├──────────┼───────┼────────────┤  │
│ │Ali Transf│ 030... │ 500K / 125K│  │
│ │Hassan FL │ 030... │ 750K / 250K│  │
│ │Quick Log │ 030... │ 300K / 0K  │  │
│ └────────────────────────────────┘  │
│                                      │
│ [View Details] [Edit] [Deactivate]   │
└──────────────────────────────────────┘
```

### 6. Shift Management Screen
```
┌──────────────────────────────────────┐
│ Shift Management      [Back] [+Start] │
├──────────────────────────────────────┤
│ Active Shift:                        │
│ Operator: Muhammad Hassan            │
│ Opened: 2024-12-29 06:00:00         │
│ Opening Cash: Rs. 50,000             │
│                                      │
│ Current Sales: Rs. 195,000           │
│ Current Stock Variance: Rs. 0        │
│                                      │
│ [    VIEW DETAILS    ]               │
│ [    END SHIFT       ]               │
│                                      │
│ Previous Shifts:                     │
│ ┌────────────────────────────────┐  │
│ │ Date │ Operator │ Sales │ Var. │  │
│ ├──────┼──────────┼───────┼──────┤  │
│ │12/28 │ Ali Khan │ 450K  │ +5K  │  │
│ │12/27 │ Hassan R │ 380K  │ -2K  │  │
│ └────────────────────────────────┘  │
└──────────────────────────────────────┘
```

### 7. Reports Screen
```
┌──────────────────────────────────────┐
│ Reports                   [Back] [+New] │
├──────────────────────────────────────┤
│ Report Type: [Daily Sales ▼]         │
│ Date Range: [12/28] to [12/29]      │
│ [Generate Report]                    │
│                                      │
│ Recent Reports:                      │
│ ┌────────────────────────────────┐  │
│ │ Type │ Date │ Generated │ View │  │
│ ├──────┼──────┼───────────┼──────┤  │
│ │Daily │12/29 │ 11:00 AM  │ [PDF]│  │
│ │Monthly│12/1 │ 12/01 9PM │ [PDF]│  │
│ │P&L   │12/29 │ 10:30 AM  │ [PDF]│  │
│ └────────────────────────────────┘  │
│                                      │
│ [View] [Export] [Delete] [Print]    │
└──────────────────────────────────────┘
```

### 8. Expense Management Screen
```
┌──────────────────────────────────────┐
│ Expense Management       [Back] [+Add] │
├──────────────────────────────────────┤
│ Date Range: [12/01] to [12/29]      │
│ Category: [All        ▼]             │
│ [Filter]                             │
│                                      │
│ ┌────────────────────────────────┐  │
│ │Category │ Amount │ Date │ Notes │  │
│ ├─────────┼────────┼──────┼────── ┤  │
│ │Electric │ 25,000 │12/29 │ Bill  │  │
│ │Salary   │150,000 │12/25 │ Staff │  │
│ │Maint.   │ 35,000 │12/20 │ Repair│  │
│ │Misc.    │  8,500 │12/15 │Office │  │
│ └────────────────────────────────┘  │
│                                      │
│ Total Expenses (Dec): Rs. 218,500   │
│                                      │
│ [View Detail] [Edit] [Delete]        │
└──────────────────────────────────────┘
```

## Role-Based Navigation

### Admin Dashboard Access
```
Dashboard
├── User Management
│   ├── Create Users
│   ├── Edit Users
│   ├── Deactivate Users
│   └── View Audit Logs
├── System Settings
│   ├── Fuel Types
│   ├── Nozzle Configuration
│   └── System Parameters
└── All other screens visible
```

### Manager Dashboard Access
```
Dashboard
├── Fuel Management
│   ├── View Tanks
│   ├── Record Purchases
│   └── Monitor Stock
├── Operations
│   ├── Manage Shifts
│   ├── View Sales
│   └── Manage Customers
├── Finance
│   ├── Manage Expenses
│   └── View Reports
└── Reports
    ├── Daily Sales
    ├── Monthly Summary
    └── P&L Statement
```

### Operator Dashboard Access
```
Dashboard
├── Sales
│   ├── Record Sale
│   └── View Today's Sales
├── Shift
│   ├── Submit Readings
│   └── View Shift Status
└── Reports
    └── Personal Performance
```

### Accountant Dashboard Access
```
Dashboard
├── Finance
│   ├── Expense Management
│   ├── Ledger View
│   └── Customer Outstanding
└── Reports
    ├── P&L Statement
    ├── Expense Report
    └── Customer Credit Aging
```

## Navigation Flow

### Login to Dashboard
1. User enters credentials
2. System validates with Firebase
3. User role loaded from Firestore
4. Dashboard rendered based on role
5. Permission checks for each feature

### Dashboard to Feature Screens
- Menu buttons/links based on role
- Back button returns to dashboard
- Logout button available on all screens

## Data Flow

```
┌──────────────┐
│ User Action  │
└──────┬───────┘
       │
       ▼
┌──────────────────┐
│ Input Validation │
└──────┬───────────┘
       │
       ▼
┌──────────────────┐
│ Permission Check │
└──────┬───────────┘
       │
       ▼
┌──────────────────┐
│ Database Service │
└──────┬───────────┘
       │
       ▼
┌──────────────────┐
│ Firebase Storage │
└──────┬───────────┘
       │
       ▼
┌──────────────────┐
│ UI Update        │
└──────────────────┘
```

---

**Version**: 1.0.0  
**Last Updated**: December 2025  
**Status**: Production Ready
