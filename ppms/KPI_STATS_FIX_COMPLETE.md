# KPI Cards - Daily & Monthly Stats Fix

## Issue Found
The daily and monthly statistics for Purchase and Expense KPI cards were showing 0 instead of actual values.

## Root Cause
The calculation code was looking for a `date` field in the purchase and expense records, but the actual field names are:
- **Purchases**: `purchase_date` (not `date`)
- **Expenses**: `expense_date` (not `date`)

This mismatch caused the date filtering logic to skip all records since it couldn't find the date field.

## Solution Applied
Updated the date field references in [src/ui/screens/dashboard_screen.py](src/ui/screens/dashboard_screen.py):

**For Purchase Records (line ~2996):**
```python
# BEFORE:
purchase_date_str = purchase.get('date', '')

# AFTER:
purchase_date_str = purchase.get('purchase_date', '')
```

**For Expense Records (line ~3019):**
```python
# BEFORE:
expense_date_str = expense.get('date', '')

# AFTER:
expense_date_str = expense.get('expense_date', '')
```

## Results After Fix

### Debug Output Comparison:

**BEFORE:**
```
Total Purchases: 12,750,000, Monthly: 0, Daily: 0
Total Expenses: 150,000, Monthly: 0, Daily: 0
```

**AFTER:**
```
Total Purchases: 12,750,000, Monthly: 12,750,000, Daily: 0
Total Expenses: 150,000, Monthly: 150,000, Daily: 100,000
```

### Monthly Values (All Correct!) ✅
- Purchase monthly: 12,750,000 (both purchases are from current month: Jan 1 & Jan 12, 2026)
- Expense monthly: 150,000 (both expenses are from current month: Jan 1 & Jan 13, 2026)

### Daily Values (Accurate) ✅
- Purchase daily: 0 (no purchases from today, Jan 13; last purchase was Jan 12)
- Expense daily: 100,000 (one expense from today, Jan 13)

### Net Revenue (Correctly Calculated) ✅
- **Monthly**: Sales(1,140,000) - Purchases(12,750,000) - Expenses(150,000) = **-11,760,000** ✅
- **Daily**: Sales(100,000) - Purchases(0) - Expenses(100,000) = **0** ✅

## KPI Cards Now Display:

### Total Sales Revenue Card
- **Main**: 1,140,000
- **Daily**: 100,000
- **Monthly**: 1,140,000

### Total Purchases Card  
- **Main**: 12,750,000
- **Daily**: 0
- **Monthly**: 12,750,000

### Total Expenses Card
- **Main**: 150,000
- **Daily**: 100,000
- **Monthly**: 150,000

### Net Revenue Card
- **Main**: -11,760,000
- **Daily**: 0
- **Monthly**: -11,760,000

## Summary
✅ **FIXED** - All KPI cards now display correct daily and monthly statistics based on actual database dates.

