"""
Utility functions and helpers
"""

import re
import logging
from typing import Optional, Dict, Any
from datetime import datetime
from src.config.logger_config import setup_logger

logger = setup_logger(__name__)


def validate_email(email: str) -> bool:
    """Validate email format."""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None


def validate_phone(phone: str) -> bool:
    """Validate phone number format (Pakistan)."""
    # Accept various Pakistan phone formats
    pattern = r'^(\+92|0)?[3-9]\d{2}-?\d{7}$|^\+92\d{10}$|^03\d{9}$'
    return re.match(pattern, phone) is not None


def validate_currency(amount: float) -> bool:
    """Validate currency amount."""
    try:
        float(amount)
        return amount >= 0
    except (ValueError, TypeError):
        return False


def format_currency(amount: float, symbol: str = "Rs.") -> str:
    """Format amount as currency."""
    return f"{symbol} {amount:,.2f}"


def format_datetime(dt: datetime, format_str: str = "%Y-%m-%d %H:%M:%S") -> str:
    """Format datetime object."""
    if isinstance(dt, str):
        return dt
    return dt.strftime(format_str) if dt else ""


def format_date(dt: datetime, format_str: str = "%Y-%m-%d") -> str:
    """Format date object."""
    if isinstance(dt, str):
        return dt
    return dt.strftime(format_str) if dt else ""


def calculate_tax(base_amount: float, tax_percentage: float) -> float:
    """Calculate tax amount."""
    return (base_amount * tax_percentage) / 100


def calculate_total(base_amount: float, tax_amount: float) -> float:
    """Calculate total amount."""
    return base_amount + tax_amount


def calculate_profit_margin(cost: float, selling_price: float) -> float:
    """Calculate profit margin percentage."""
    if cost == 0:
        return 0
    return ((selling_price - cost) / cost) * 100


def generate_reference_number(prefix: str = "REF") -> str:
    """Generate unique reference number."""
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    return f"{prefix}-{timestamp}"


def parse_date_string(date_str: str, format_str: str = "%Y-%m-%d") -> Optional[datetime]:
    """Parse date string to datetime object."""
    try:
        return datetime.strptime(date_str, format_str)
    except (ValueError, TypeError):
        logger.warning(f"Failed to parse date: {date_str}")
        return None


def get_date_range(start_date: datetime, end_date: datetime) -> Dict[str, str]:
    """Get date range in ISO format."""
    return {
        'start': start_date.isoformat(),
        'end': end_date.isoformat()
    }


def round_decimal(value: float, decimals: int = 2) -> float:
    """Round value to specified decimal places."""
    return round(value, decimals)


def sanitize_string(value: str, max_length: Optional[int] = None) -> str:
    """Sanitize string input."""
    if not isinstance(value, str):
        return ""
    
    # Remove leading/trailing whitespace
    value = value.strip()
    
    # Remove special characters that could cause injection
    value = re.sub(r'[<>\"\'%;()&+]', '', value)
    
    # Truncate if needed
    if max_length and len(value) > max_length:
        value = value[:max_length]
    
    return value


def calculate_variance(expected: float, actual: float) -> float:
    """Calculate variance between expected and actual values."""
    return actual - expected


def is_within_range(value: float, min_val: float, max_val: float) -> bool:
    """Check if value is within range."""
    return min_val <= value <= max_val


def percentage_change(old_value: float, new_value: float) -> float:
    """Calculate percentage change."""
    if old_value == 0:
        return 0
    return ((new_value - old_value) / old_value) * 100


class ValidationError(Exception):
    """Custom validation error."""
    pass


def validate_sale_data(
    quantity: float,
    unit_price: float,
    fuel_type_id: str,
    nozzle_id: str
) -> tuple[bool, str]:
    """Validate sale transaction data."""
    try:
        if not fuel_type_id or not nozzle_id:
            return False, "Fuel type and nozzle are required"
        
        if not isinstance(quantity, (int, float)) or quantity <= 0:
            return False, "Quantity must be positive"
        
        if not isinstance(unit_price, (int, float)) or unit_price <= 0:
            return False, "Unit price must be positive"
        
        return True, "Validation successful"
    
    except Exception as e:
        logger.error(f"Validation error: {str(e)}")
        return False, str(e)


def validate_purchase_data(
    quantity: float,
    rate: float,
    supplier_name: str,
    invoice_number: str
) -> tuple[bool, str]:
    """Validate purchase transaction data."""
    try:
        if not supplier_name or len(supplier_name.strip()) == 0:
            return False, "Supplier name is required"
        
        if not invoice_number or len(invoice_number.strip()) == 0:
            return False, "Invoice number is required"
        
        if not isinstance(quantity, (int, float)) or quantity <= 0:
            return False, "Quantity must be positive"
        
        if not isinstance(rate, (int, float)) or rate <= 0:
            return False, "Rate must be positive"
        
        return True, "Validation successful"
    
    except Exception as e:
        logger.error(f"Validation error: {str(e)}")
        return False, str(e)


def validate_customer_data(name: str, phone: str) -> tuple[bool, str]:
    """Validate customer data."""
    try:
        if not name or len(name.strip()) == 0:
            return False, "Customer name is required"
        
        if not phone:
            return False, "Phone number is required"
        
        if not validate_phone(phone):
            return False, "Invalid phone number format"
        
        return True, "Validation successful"
    
    except Exception as e:
        logger.error(f"Validation error: {str(e)}")
        return False, str(e)
