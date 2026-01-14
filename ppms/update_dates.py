from datetime import datetime, date
from firebase_admin import db, initialize_app, credentials

try:
    # Initialize Firebase
    cred = credentials.Certificate('serviceAccountKey.json')
    app = initialize_app(cred, {'databaseURL': 'https://ppms-4f9b4-default-rtdb.firebaseio.com/'})
    
    today = date.today()
    today_str = today.isoformat()
    
    print(f"Updating all purchase and expense records to today's date: {today_str}")
    print()
    
    # Update purchases
    purchase_ref = db.reference('purchases')
    purchases = purchase_ref.get()
    if purchases:
        print(f"Found {len(purchases)} purchase records")
        for key in purchases.keys():
            # Update the date to today
            purchase_ref.child(key).update({'date': today_str + 'T00:00:00Z'})
            print(f"  Updated purchase {key}")
    
    print()
    
    # Update expenses
    expense_ref = db.reference('expenses')
    expenses = expense_ref.get()
    if expenses:
        print(f"Found {len(expenses)} expense records")
        for key in expenses.keys():
            # Update the date to today
            expense_ref.child(key).update({'date': today_str + 'T00:00:00Z'})
            print(f"  Updated expense {key}")
    
    print()
    print("All records updated successfully!")
    
except Exception as e:
    print(f'Error: {e}')
    import traceback
    traceback.print_exc()
finally:
    try:
        from firebase_admin import App
        app_instances = App._apps if hasattr(App, '_apps') else {}
        if app_instances:
            print(f"\nNote: {len(app_instances)} Firebase app instances created")
    except:
        pass
