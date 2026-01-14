#!/usr/bin/env python3
"""
Utility script to update test data dates to current period.
Run this to make sure monthly/daily stats show proper values.
"""

import sys
import os
from datetime import datetime, date, timedelta
from firebase_admin import db, initialize_app, credentials, get_app

def update_test_data_dates():
    """Update purchase and expense records to have current month/day dates."""
    try:
        # Initialize Firebase if not already done
        try:
            app = get_app()
        except ValueError:
            cred = credentials.Certificate('serviceAccountKey.json')
            app = initialize_app(cred, {'databaseURL': 'https://ppms-4f9b4-default-rtdb.firebaseio.com/'})
        
        today = date.today()
        month_start = today.replace(day=1)
        
        print(f"Today's date: {today}")
        print(f"Month start: {month_start}")
        print()
        
        # Update purchases to have dates across the month
        print("Updating purchases...")
        purchase_ref = db.reference('purchases')
        purchases = purchase_ref.get()
        if purchases:
            purchase_list = list(purchases.items())
            for idx, (key, purchase) in enumerate(purchase_list):
                # Distribute purchases across the month
                days_into_month = (idx % 25) + 1  # 1-25
                new_date = today.replace(day=min(days_into_month, 28))  # Avoid day 29-31 issues
                new_date_str = new_date.isoformat() + 'T10:00:00Z'
                
                purchase_ref.child(key).update({'date': new_date_str})
                print(f"  Updated purchase {key}: {new_date_str}")
        
        print()
        print("Updating expenses...")
        expense_ref = db.reference('expenses')
        expenses = expense_ref.get()
        if expenses:
            expense_list = list(expenses.items())
            for idx, (key, expense) in enumerate(expense_list):
                # Distribute expenses across the month
                days_into_month = (idx % 20) + 5  # 5-24
                new_date = today.replace(day=min(days_into_month, 28))
                new_date_str = new_date.isoformat() + 'T14:00:00Z'
                
                expense_ref.child(key).update({'date': new_date_str})
                print(f"  Updated expense {key}: {new_date_str}")
        
        print()
        print("✅ Test data dates updated successfully!")
        print("The KPI cards should now display correct monthly/daily values.")
        
    except Exception as e:
        print(f"❌ Error: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        return False
    
    return True

if __name__ == '__main__':
    success = update_test_data_dates()
    sys.exit(0 if success else 1)
