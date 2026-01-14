#!/usr/bin/env python3
"""
Quick fix script to update purchase and expense dates to current period.
Uses direct Firestore API calls.
"""

import json
from datetime import datetime, date, timedelta
import os

def update_firestore_dates():
    """Update purchase and expense record dates in Firestore."""
    try:
        # Import Firebase modules
        import firebase_admin
        from firebase_admin import credentials, firestore
        
        # Initialize Firebase
        if not firebase_admin._apps:
            cred = credentials.Certificate('serviceAccountKey.json')
            firebase_admin.initialize_app(cred)
        
        db = firestore.client()
        today = date.today()
        month_start = today.replace(day=1)
        
        print(f"📅 Today's date: {today}")
        print(f"📅 Month start: {month_start}\n")
        
        # Update Purchases
        print("🔄 Updating Purchases...")
        purchases_ref = db.collection('purchases')
        docs = purchases_ref.stream()
        
        purchase_count = 0
        for idx, doc in enumerate(docs):
            # Distribute purchases across the month
            days_into_month = (idx % 20) + 5  # Days 5-24
            new_date = today.replace(day=min(days_into_month, 28))
            new_date_str = new_date.isoformat() + 'T10:00:00Z'
            
            purchases_ref.document(doc.id).update({'date': new_date_str})
            print(f"  ✓ Purchase {doc.id}: {new_date_str}")
            purchase_count += 1
        
        if purchase_count == 0:
            print("  No purchases found.")
        else:
            print(f"  ✅ Updated {purchase_count} purchase records\n")
        
        # Update Expenses
        print("🔄 Updating Expenses...")
        expenses_ref = db.collection('expenses')
        docs = expenses_ref.stream()
        
        expense_count = 0
        for idx, doc in enumerate(docs):
            # Distribute expenses across the month
            days_into_month = (idx % 20) + 8  # Days 8-27
            new_date = today.replace(day=min(days_into_month, 28))
            new_date_str = new_date.isoformat() + 'T14:00:00Z'
            
            expenses_ref.document(doc.id).update({'date': new_date_str})
            print(f"  ✓ Expense {doc.id}: {new_date_str}")
            expense_count += 1
        
        if expense_count == 0:
            print("  No expenses found.")
        else:
            print(f"  ✅ Updated {expense_count} expense records\n")
        
        print("=" * 60)
        print("✅ SUCCESS! Test data updated with current dates.")
        print("=" * 60)
        print("\nExpected KPI Card values after refresh:")
        print(f"  • Purchase Monthly: Should show total purchases from {month_start}")
        print(f"  • Purchase Daily: Should show purchases from {today}")
        print(f"  • Expense Monthly: Should show expenses from {month_start}")
        print(f"  • Expense Daily: Should show expenses from {today}")
        print("\n🔄 The app will auto-refresh in 30 seconds.")
        print("💡 If values still don't show, restart the app.\n")
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    import sys
    success = update_firestore_dates()
    sys.exit(0 if success else 1)
