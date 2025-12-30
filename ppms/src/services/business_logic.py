"""
Business Logic for PPMS
Core business calculations and transaction processing.
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional
from src.config.firebase_config import FirebaseConfig
from src.config.logger_config import setup_logger
from src.models import Sale, Purchase, Tank, Shift, Customer, Expense
from src.utils.validators import calculate_tax, calculate_total

logger = setup_logger(__name__)


class SalesCalculationEngine:
    """Calculate sales totals, taxes, and reconciliation."""

    @staticmethod
    def calculate_sale_amount(quantity: float, unit_price: float, tax_percentage: float) -> Dict[str, float]:
        """
        Calculate sale amount with tax.

        Args:
            quantity: Fuel quantity
            unit_price: Price per unit
            tax_percentage: Tax percentage

        Returns:
            Dict with base, tax, and total amounts
        """
        base_amount = quantity * unit_price
        tax_amount = calculate_tax(base_amount, tax_percentage)
        total_amount = calculate_total(base_amount, tax_amount)

        return {
            'base_amount': round(base_amount, 2),
            'tax_amount': round(tax_amount, 2),
            'total_amount': round(total_amount, 2)
        }

    @staticmethod
    def calculate_daily_sales(sales_records: List[Sale]) -> Dict[str, any]:
        """
        Calculate daily sales summary.

        Args:
            sales_records: List of sales for the day

        Returns:
            Summary statistics
        """
        total_quantity = sum(s.quantity for s in sales_records)
        total_base = sum(s.base_amount for s in sales_records)
        total_tax = sum(s.tax_amount for s in sales_records)
        total_revenue = sum(s.total_amount for s in sales_records)

        payment_breakdown = {}
        for sale in sales_records:
            method = sale.payment_method.value
            if method not in payment_breakdown:
                payment_breakdown[method] = 0
            payment_breakdown[method] += sale.total_amount

        return {
            'total_transactions': len(sales_records),
            'total_quantity': round(total_quantity, 2),
            'base_amount': round(total_base, 2),
            'tax_collected': round(total_tax, 2),
            'total_revenue': round(total_revenue, 2),
            'payment_breakdown': payment_breakdown
        }

    @staticmethod
    def calculate_profit_margin(cost_price: float, selling_price: float) -> float:
        """Calculate profit margin percentage."""
        if cost_price == 0:
            return 0
        return ((selling_price - cost_price) / cost_price) * 100


class StockManagementEngine:
    """Manage fuel inventory and stock levels."""

    def __init__(self):
        """Initialize stock management engine."""
        self.firestore = FirebaseConfig.get_firestore()

    def update_tank_stock(self, tank_id: str, quantity_sold: float) -> Tuple[bool, str]:
        """
        Update tank stock after a sale.

        Args:
            tank_id: Tank ID
            quantity_sold: Quantity sold

        Returns:
            Tuple of (success, message)
        """
        try:
            tank_doc = self.firestore.collection('tanks').document(tank_id).get()
            if not tank_doc.exists:
                return False, "Tank not found"

            tank_data = tank_doc.to_dict()
            current_stock = tank_data.get('current_stock', 0)
            new_stock = current_stock - quantity_sold

            if new_stock < 0:
                return False, "Insufficient stock"

            self.firestore.collection('tanks').document(tank_id).update({
                'current_stock': new_stock,
                'last_reading_date': datetime.now().isoformat()
            })

            logger.info(f"Tank {tank_id} stock updated: {current_stock} -> {new_stock}")
            return True, "Stock updated successfully"

        except Exception as e:
            logger.error(f"Error updating stock: {str(e)}")
            return False, str(e)

    def add_stock_from_purchase(self, tank_id: str, quantity: float) -> Tuple[bool, str]:
        """
        Add stock to tank from purchase.

        Args:
            tank_id: Tank ID
            quantity: Quantity to add

        Returns:
            Tuple of (success, message)
        """
        try:
            tank_doc = self.firestore.collection('tanks').document(tank_id).get()
            if not tank_doc.exists:
                return False, "Tank not found"

            tank_data = tank_doc.to_dict()
            current_stock = tank_data.get('current_stock', 0)
            capacity = tank_data.get('capacity', 0)
            new_stock = current_stock + quantity

            if new_stock > capacity:
                return False, f"Stock would exceed capacity (max: {capacity}L)"

            self.firestore.collection('tanks').document(tank_id).update({
                'current_stock': new_stock,
                'last_reading_date': datetime.now().isoformat()
            })

            logger.info(f"Stock added to tank {tank_id}: {quantity}L")
            return True, "Stock added successfully"

        except Exception as e:
            logger.error(f"Error adding stock: {str(e)}")
            return False, str(e)

    def check_low_stock(self) -> List[Dict[str, any]]:
        """
        Check tanks with low stock levels.

        Returns:
            List of low-stock tank warnings
        """
        try:
            docs = self.firestore.collection('tanks').stream()
            low_stock_tanks = []

            for doc in docs:
                tank_data = doc.to_dict()
                current_stock = tank_data.get('current_stock', 0)
                minimum_stock = tank_data.get('minimum_stock', 0)

                if current_stock < minimum_stock:
                    low_stock_tanks.append({
                        'tank_id': tank_data.get('id'),
                        'tank_name': tank_data.get('name'),
                        'current_stock': current_stock,
                        'minimum_stock': minimum_stock,
                        'shortfall': minimum_stock - current_stock
                    })

            return low_stock_tanks

        except Exception as e:
            logger.error(f"Error checking low stock: {str(e)}")
            return []


class ShiftReconciliationEngine:
    """Manage shift open/close and reconciliation."""

    def __init__(self):
        """Initialize shift engine."""
        self.firestore = FirebaseConfig.get_firestore()
        self.sales_calc = SalesCalculationEngine()

    def open_shift(self, operator_id: str, opening_cash: float) -> Tuple[bool, str, Optional[str]]:
        """
        Open new shift for operator.

        Args:
            operator_id: Operator user ID
            opening_cash: Starting cash amount

        Returns:
            Tuple of (success, message, shift_id)
        """
        try:
            shift_id = self.firestore.collection('shifts').document().id
            shift_data = {
                'id': shift_id,
                'date': datetime.now().isoformat(),
                'opening_time': datetime.now().isoformat(),
                'closing_time': None,
                'operator_id': operator_id,
                'opening_cash': opening_cash,
                'closing_cash': 0,
                'expected_cash': opening_cash,
                'variance': 0,
                'status': 'open'
            }

            self.firestore.collection('shifts').document(shift_id).set(shift_data)
            logger.info(f"Shift opened: {shift_id} for operator {operator_id}")
            return True, "Shift opened successfully", shift_id

        except Exception as e:
            logger.error(f"Error opening shift: {str(e)}")
            return False, str(e), None

    def close_shift(self, shift_id: str, closing_cash: float) -> Tuple[bool, str, Dict]:
        """
        Close shift and reconcile.

        Args:
            shift_id: Shift ID
            closing_cash: Actual cash counted

        Returns:
            Tuple of (success, message, reconciliation_data)
        """
        try:
            shift_doc = self.firestore.collection('shifts').document(shift_id).get()
            if not shift_doc.exists:
                return False, "Shift not found", {}

            shift_data = shift_doc.to_dict()
            opening_cash = shift_data.get('opening_cash', 0)

            # Calculate expected cash from sales
            sales_docs = self.firestore.collection('sales').where(
                'shift_id', '==', shift_id
            ).stream()

            total_sales = sum(doc.to_dict().get('total_amount', 0) for doc in sales_docs)
            expected_cash = opening_cash + total_sales
            variance = closing_cash - expected_cash

            # Update shift
            self.firestore.collection('shifts').document(shift_id).update({
                'closing_time': datetime.now().isoformat(),
                'closing_cash': closing_cash,
                'expected_cash': expected_cash,
                'variance': variance,
                'status': 'closed'
            })

            reconciliation = {
                'opening_cash': opening_cash,
                'total_sales': total_sales,
                'expected_cash': expected_cash,
                'actual_cash': closing_cash,
                'variance': variance,
                'status': 'balanced' if variance == 0 else ('shortage' if variance < 0 else 'excess')
            }

            logger.info(f"Shift closed: {shift_id}, Variance: {variance}")
            return True, "Shift closed successfully", reconciliation

        except Exception as e:
            logger.error(f"Error closing shift: {str(e)}")
            return False, str(e), {}


class ProfitAndLossCalculator:
    """Calculate P&L statements."""

    def __init__(self):
        """Initialize P&L calculator."""
        self.firestore = FirebaseConfig.get_firestore()

    def calculate_daily_pl(self, date: datetime) -> Dict[str, float]:
        """
        Calculate daily P&L.

        Args:
            date: Date for calculation

        Returns:
            P&L data
        """
        try:
            date_str = date.strftime('%Y-%m-%d')

            # Get daily sales
            sales_docs = self.firestore.collection('sales').where(
                'date', '>=', f"{date_str}T00:00:00"
            ).where(
                'date', '<', f"{date_str}T23:59:59"
            ).stream()

            total_revenue = 0
            total_tax = 0
            for doc in sales_docs:
                data = doc.to_dict()
                total_revenue += data.get('total_amount', 0)
                total_tax += data.get('tax_amount', 0)

            # Get daily expenses
            expense_docs = self.firestore.collection('expenses').where(
                'date', '>=', f"{date_str}T00:00:00"
            ).where(
                'date', '<', f"{date_str}T23:59:59"
            ).stream()

            total_expenses = sum(doc.to_dict().get('amount', 0) for doc in expense_docs)

            # Calculate profit
            net_profit = total_revenue - total_expenses

            return {
                'date': date_str,
                'revenue': round(total_revenue, 2),
                'tax_collected': round(total_tax, 2),
                'expenses': round(total_expenses, 2),
                'net_profit': round(net_profit, 2),
                'profit_margin': round((net_profit / total_revenue * 100) if total_revenue > 0 else 0, 2)
            }

        except Exception as e:
            logger.error(f"Error calculating daily P&L: {str(e)}")
            return {}

    def calculate_monthly_pl(self, year: int, month: int) -> Dict[str, float]:
        """
        Calculate monthly P&L.

        Args:
            year: Year
            month: Month (1-12)

        Returns:
            P&L data
        """
        try:
            start_date = datetime(year, month, 1)
            if month == 12:
                end_date = datetime(year + 1, 1, 1)
            else:
                end_date = datetime(year, month + 1, 1)

            # Calculate using daily P&Ls
            total_revenue = 0
            total_expenses = 0

            current_date = start_date
            while current_date < end_date:
                daily_pl = self.calculate_daily_pl(current_date)
                total_revenue += daily_pl.get('revenue', 0)
                total_expenses += daily_pl.get('expenses', 0)
                current_date += timedelta(days=1)

            net_profit = total_revenue - total_expenses

            return {
                'period': f"{year}-{month:02d}",
                'revenue': round(total_revenue, 2),
                'expenses': round(total_expenses, 2),
                'net_profit': round(net_profit, 2),
                'profit_margin': round((net_profit / total_revenue * 100) if total_revenue > 0 else 0, 2)
            }

        except Exception as e:
            logger.error(f"Error calculating monthly P&L: {str(e)}")
            return {}


class CustomerCreditManager:
    """Manage customer credit and outstanding balances."""

    def __init__(self):
        """Initialize credit manager."""
        self.firestore = FirebaseConfig.get_firestore()

    def get_customer_credit_status(self, customer_id: str) -> Dict[str, float]:
        """
        Get customer credit status.

        Args:
            customer_id: Customer ID

        Returns:
            Credit status data
        """
        try:
            cust_doc = self.firestore.collection('customers').document(customer_id).get()
            if not cust_doc.exists:
                return {}

            cust_data = cust_doc.to_dict()
            credit_limit = cust_data.get('credit_limit', 0)
            outstanding = cust_data.get('outstanding_balance', 0)
            available = credit_limit - outstanding

            return {
                'customer_id': customer_id,
                'credit_limit': credit_limit,
                'outstanding_balance': outstanding,
                'available_credit': available,
                'utilization_percent': round((outstanding / credit_limit * 100) if credit_limit > 0 else 0, 2)
            }

        except Exception as e:
            logger.error(f"Error getting credit status: {str(e)}")
            return {}

    def record_payment(self, customer_id: str, amount: float) -> Tuple[bool, str]:
        """
        Record customer payment.

        Args:
            customer_id: Customer ID
            amount: Payment amount

        Returns:
            Tuple of (success, message)
        """
        try:
            cust_doc = self.firestore.collection('customers').document(customer_id).get()
            if not cust_doc.exists:
                return False, "Customer not found"

            cust_data = cust_doc.to_dict()
            outstanding = cust_data.get('outstanding_balance', 0)

            if amount > outstanding:
                return False, f"Payment exceeds outstanding balance (Rs. {outstanding})"

            new_outstanding = outstanding - amount
            self.firestore.collection('customers').document(customer_id).update({
                'outstanding_balance': new_outstanding
            })

            logger.info(f"Payment recorded: {amount} for customer {customer_id}")
            return True, "Payment recorded successfully"

        except Exception as e:
            logger.error(f"Error recording payment: {str(e)}")
            return False, str(e)

    def get_aging_report(self) -> List[Dict]:
        """
        Get customer credit aging report.

        Returns:
            List of customers with aging data
        """
        try:
            customers = []
            docs = self.firestore.collection('customers').where(
                'outstanding_balance', '>', 0
            ).stream()

            for doc in docs:
                cust_data = doc.to_dict()
                customers.append({
                    'customer_id': cust_data.get('id'),
                    'name': cust_data.get('name'),
                    'outstanding': cust_data.get('outstanding_balance', 0),
                    'credit_limit': cust_data.get('credit_limit', 0),
                    'utilization': round((cust_data.get('outstanding_balance', 0) / cust_data.get('credit_limit', 1) * 100), 2)
                })

            return sorted(customers, key=lambda x: x['outstanding'], reverse=True)

        except Exception as e:
            logger.error(f"Error getting aging report: {str(e)}")
            return []
