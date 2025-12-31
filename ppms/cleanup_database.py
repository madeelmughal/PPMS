"""
Database Cleanup Script - Remove all data except users
Use this to reset the system for testing from scratch
"""

import sys
import json
import os
from pathlib import Path

# Get app data path
def get_app_data_path():
    """Get the appropriate path for storing application data."""
    script_dir = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(script_dir, 'data')

DATA_FILE = os.path.join(get_app_data_path(), 'local_db.json')

# Collections to clear (excluding 'users')
COLLECTIONS_TO_CLEAR = [
    'sales',
    'purchases',
    'expenses',
    'tanks',
    'nozzles',
    'fuel_types',
    'customers',
    'account_heads',
    'shifts',
    'readings',
    'payments',
    'exchange_rates',
    'audit_logs'
]


def cleanup_database():
    """Clear all data from database except users collection."""
    try:
        print("\n" + "="*60)
        print("DATABASE CLEANUP - Removing all data except users")
        print("="*60 + "\n")
        
        if not os.path.exists(DATA_FILE):
            print("[WARNING] Data file not found: {}".format(DATA_FILE))
            return False
        
        # Load the JSON data
        with open(DATA_FILE, 'r') as f:
            data = json.load(f)
        
        total_deleted = 0
        print("Clearing collections...\n")
        
        for collection in COLLECTIONS_TO_CLEAR:
            if collection in data:
                count = len(data[collection])
                del data[collection]
                print("[OK] {}: Deleted {} documents".format(collection, count))
                total_deleted += count
            else:
                print("[OK] {}: Deleted 0 documents".format(collection))
        
        # Keep users collection
        if 'users' not in data:
            print("[WARNING] Users collection not found in database")
        else:
            print("[OK] Users collection preserved ({} users)".format(len(data['users'])))
        
        # Write back the cleaned data
        with open(DATA_FILE, 'w') as f:
            json.dump(data, f, indent=2)
        
        print("\n" + "="*60)
        print("[OK] Cleanup complete! Total documents deleted: {}".format(total_deleted))
        print("[OK] Data file updated: {}".format(DATA_FILE))
        print("="*60 + "\n")
        
        return True
        
    except Exception as e:
        print("\n[ERROR] Cleanup failed: {}\n".format(str(e)))
        return False


if __name__ == "__main__":
    # Allow skipping confirmation with --force flag
    skip_confirm = len(sys.argv) > 1 and sys.argv[1] == '--force'
    
    print("\nWARNING: This will delete ALL data from the database except users!")
    print("This action cannot be undone.")
    print("Data file: {}".format(DATA_FILE))
    print()
    
    if skip_confirm:
        success = cleanup_database()
        sys.exit(0 if success else 1)
    else:
        response = input("Are you sure you want to continue? (yes/no): ").strip().lower()
        
        if response == 'yes':
            success = cleanup_database()
            sys.exit(0 if success else 1)
        else:
            print("Cleanup cancelled.\n")
            sys.exit(0)
