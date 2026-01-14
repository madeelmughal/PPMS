#!/usr/bin/env python3
"""
Check current dates in purchase and expense records.
"""

import sys
sys.path.insert(0, '/prog/ppms')

from datetime import datetime, date
from src.services.database_service import DatabaseService

def check_dates():
    """Check the actual dates in purchase and expense records."""
    try:
        db = DatabaseService()
        today = date.today()
        month_start = today.replace(day=1)
        
        print(f"📅 Current date: {today}")
        print(f"📅 Month start: {month_start}\n")
        
        # Check purchases
        purchases = db.list_documents('purchases')
        print(f"📦 PURCHASES ({len(purchases)} records):")
        for purchase in purchases:
            date_str = purchase.get('date', 'NO DATE')
            cost = purchase.get('total_cost', 0)
            print(f"  • Date: {date_str} | Cost: {cost}")
        
        print()
        
        # Check expenses
        expenses = db.list_documents('expenses')
        print(f"💰 EXPENSES ({len(expenses)} records):")
        for expense in expenses:
            date_str = expense.get('date', 'NO DATE')
            amount = expense.get('amount', 0)
            print(f"  • Date: {date_str} | Amount: {amount}")
            
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    check_dates()
