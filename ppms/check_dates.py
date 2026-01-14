from datetime import datetime, date
from firebase_admin import db, initialize_app, credentials

try:
    cred = credentials.Certificate('serviceAccountKey.json')
    initialize_app(cred, {'databaseURL': 'https://ppms-4f9b4-default-rtdb.firebaseio.com/'})
    
    # Get today and month start
    today = date.today()
    month_start = today.replace(day=1)
    
    print(f'Today: {today}')
    print(f'Month Start: {month_start}')
    print()
    
    # Check sample purchase data
    purchase_ref = db.reference('purchases')
    purchases = purchase_ref.get()
    if purchases:
        print('Purchase Records:')
        for key, purchase in list(purchases.items()):
            date_str = purchase.get('date', 'NO DATE')
            print(f'  Key: {key}')
            print(f'  Date: {date_str}')
            print(f'  Total Cost: {purchase.get("total_cost", 0)}')
            print()
    
    # Check sample expense data
    expense_ref = db.reference('expenses')
    expenses = expense_ref.get()
    if expenses:
        print('Expense Records:')
        for key, expense in list(expenses.items()):
            date_str = expense.get('date', 'NO DATE')
            print(f'  Key: {key}')
            print(f'  Date: {date_str}')
            print(f'  Amount: {expense.get("amount", 0)}')
            print()
            
except Exception as e:
    print(f'Error: {e}')
    import traceback
    traceback.print_exc()
