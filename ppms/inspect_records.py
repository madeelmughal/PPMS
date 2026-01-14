#!/usr/bin/env python3
"""
Inspect purchase and expense records to find their document IDs.
"""

import sys
sys.path.insert(0, '/prog/ppms')

from datetime import datetime, date
from src.services.database_service import DatabaseService

def inspect_records():
    """Inspect records and their structure."""
    try:
        db = DatabaseService()
        
        print("PURCHASES (inspecting structure):")
        purchases_ref = db.firestore.collection('purchases')
        count = 0
        for doc in purchases_ref.stream():
            data = doc.to_dict()
            print(f"\n  Document data: {data}")
            print(f"  Keys: {list(data.keys())}")
            count += 1
            if count >= 2:
                break
        
        print("\n\nEXPENSES (inspecting structure):")
        expenses_ref = db.firestore.collection('expenses')
        count = 0
        for doc in expenses_ref.stream():
            data = doc.to_dict()
            print(f"\n  Document data: {data}")
            print(f"  Keys: {list(data.keys())}")
            count += 1
            if count >= 2:
                break
            
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    inspect_records()
