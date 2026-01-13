#!/usr/bin/env python3
"""Debug script to check sales data in database."""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.services.database_service import SalesService
from src.config.firebase_config import FirebaseConfig
import json

# Initialize Firebase
FirebaseConfig.initialize()

# Get sales service
sales_service = SalesService()

# Get all sales
all_sales = sales_service.list_documents('sales')

print(f"Total sales: {len(all_sales)}\n")

for idx, sale in enumerate(all_sales):
    print(f"Sale {idx + 1}:")
    if isinstance(sale, dict):
        for key, value in sale.items():
            print(f"  {key}: {value} (type: {type(value).__name__})")
    else:
        print(f"  {sale}")
    print()
