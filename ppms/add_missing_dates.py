#!/usr/bin/env python3
"""
Add missing date fields to purchase and expense records.
"""

import sys
sys.path.insert(0, '/prog/ppms')

from datetime import datetime, date, timedelta
from src.services.database_service import DatabaseService

def add_missing_dates():
    """Add date field to purchase and expense records that are missing it."""
    try:
        db = DatabaseService()
        today = datetime.now().isoformat() + 'Z'
        
        print(f"📅 Adding dates to records...")
        print(f"   Date to use: {today}\n")
        
        # Update purchases
        print(f"📦 PURCHASES:")
        for idx, doc in enumerate(db.firestore.collection('purchases').stream()):
            purchase = doc.to_dict()
            if 'date' not in purchase or not purchase.get('date'):
                # Create date distribution across month
                day_offset = (idx % 20) + 5
                purchase_date = date.today().replace(day=min(day_offset, 28))
                date_value = purchase_date.isoformat() + 'T10:00:00Z'
                
                # Update the record
                db.firestore.collection('purchases').document(doc.id).update({
                    'date': date_value
                })
                print(f"  ✓ Added date {date_value} to purchase {doc.id}")
            else:
                print(f"  ✓ Already has date: {purchase.get('date')}")
        
        print()
        
        # Update expenses
        print(f"💰 EXPENSES:")
        for idx, doc in enumerate(db.firestore.collection('expenses').stream()):
            expense = doc.to_dict()
            if 'date' not in expense or not expense.get('date'):
                # Create date distribution across month
                day_offset = (idx % 20) + 8
                expense_date = date.today().replace(day=min(day_offset, 28))
                date_value = expense_date.isoformat() + 'T14:00:00Z'
                
                # Update the record
                db.firestore.collection('expenses').document(doc.id).update({
                    'date': date_value
                })
                print(f"  ✓ Added date {date_value} to expense {doc.id}")
            else:
                print(f"  ✓ Already has date: {expense.get('date')}")
        
        print("\n✅ All records updated!")
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    success = add_missing_dates()
    sys.exit(0 if success else 1)
