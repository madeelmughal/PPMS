"""
Unit Tests for PPMS
Test suite for core functionality.
"""

import unittest
from datetime import datetime
from src.config.firebase_config import AppConfig
from src.utils.validators import (
    validate_email, validate_phone, validate_currency,
    calculate_tax, format_currency
)
from src.models import User, UserRole, FuelType, Tank, Sale, PaymentMethod
from src.services.business_logic import SalesCalculationEngine, StockManagementEngine


class TestValidators(unittest.TestCase):
    """Test utility validators."""

    def test_email_validation(self):
        """Test email validation."""
        self.assertTrue(validate_email("user@example.com"))
        self.assertTrue(validate_email("test.user+tag@domain.co.uk"))
        self.assertFalse(validate_email("invalid.email"))
        self.assertFalse(validate_email("@example.com"))

    def test_phone_validation(self):
        """Test phone validation."""
        self.assertTrue(validate_phone("03001234567"))
        self.assertTrue(validate_phone("+923001234567"))
        self.assertFalse(validate_phone("123456"))

    def test_currency_validation(self):
        """Test currency validation."""
        self.assertTrue(validate_currency(100.0))
        self.assertTrue(validate_currency(0))
        self.assertFalse(validate_currency(-50))
        self.assertFalse(validate_currency("invalid"))

    def test_tax_calculation(self):
        """Test tax calculation."""
        base = 1000
        tax_rate = 17
        expected_tax = 170
        self.assertEqual(calculate_tax(base, tax_rate), expected_tax)

    def test_currency_formatting(self):
        """Test currency formatting."""
        formatted = format_currency(1000.50, "Rs.")
        self.assertIn("Rs.", formatted)
        self.assertIn("1,000.50", formatted)


class TestDataModels(unittest.TestCase):
    """Test data models."""

    def test_user_creation(self):
        """Test user model creation."""
        user = User(
            uid="user_001",
            email="user@example.com",
            name="Test User",
            role=UserRole.OPERATOR
        )

        self.assertEqual(user.uid, "user_001")
        self.assertEqual(user.email, "user@example.com")
        self.assertEqual(user.role, UserRole.OPERATOR)

    def test_user_to_dict(self):
        """Test user model serialization."""
        user = User(
            uid="user_001",
            email="user@example.com",
            name="Test User",
            role=UserRole.MANAGER
        )

        data = user.to_dict()
        self.assertIn('uid', data)
        self.assertEqual(data['role'], 'manager')

    def test_fuel_type_creation(self):
        """Test fuel type model."""
        fuel = FuelType(
            id="fuel_001",
            name="Petrol",
            unit_price=289.50,
            tax_percentage=17.0
        )

        self.assertEqual(fuel.name, "Petrol")
        self.assertEqual(fuel.unit_price, 289.50)

    def test_tank_stock_percentage(self):
        """Test tank stock percentage calculation."""
        tank = Tank(
            id="tank_001",
            name="Tank A",
            fuel_type_id="fuel_001",
            capacity=50000,
            current_stock=25000,
            minimum_stock=10000
        )

        self.assertEqual(tank.stock_percentage, 50.0)
        self.assertFalse(tank.is_low_stock)

    def test_tank_low_stock_alert(self):
        """Test tank low stock detection."""
        tank = Tank(
            id="tank_001",
            name="Tank A",
            fuel_type_id="fuel_001",
            capacity=50000,
            current_stock=8000,
            minimum_stock=10000
        )

        self.assertTrue(tank.is_low_stock)


class TestSalesCalculations(unittest.TestCase):
    """Test sales calculation engine."""

    def setUp(self):
        """Set up test fixtures."""
        self.engine = SalesCalculationEngine()

    def test_calculate_sale_amount(self):
        """Test sale amount calculation."""
        result = self.engine.calculate_sale_amount(50, 289.50, 17)

        self.assertEqual(result['base_amount'], 14475.0)
        self.assertEqual(result['tax_amount'], 2460.75)
        self.assertEqual(result['total_amount'], 16935.75)

    def test_profit_margin_calculation(self):
        """Test profit margin calculation."""
        cost = 250
        selling = 289.50

        margin = self.engine.calculate_profit_margin(cost, selling)
        self.assertAlmostEqual(margin, 15.8, places=1)

    def test_profit_margin_zero_cost(self):
        """Test profit margin with zero cost."""
        margin = self.engine.calculate_profit_margin(0, 100)
        self.assertEqual(margin, 0)


class TestConfiguration(unittest.TestCase):
    """Test application configuration."""

    def test_app_config_exists(self):
        """Test app config is loaded."""
        self.assertIsNotNone(AppConfig.APP_NAME)
        self.assertIsNotNone(AppConfig.CURRENCY_SYMBOL)

    def test_roles_defined(self):
        """Test all roles are defined."""
        roles = ['admin', 'manager', 'operator', 'accountant']
        for role in roles:
            self.assertIn(role, AppConfig.ROLES)

    def test_fuel_types_defined(self):
        """Test fuel types are defined."""
        self.assertIn('Petrol', AppConfig.FUEL_TYPES)
        self.assertIn('Diesel', AppConfig.FUEL_TYPES)

    def test_expense_categories(self):
        """Test expense categories."""
        self.assertIn('Electricity', AppConfig.EXPENSE_CATEGORIES)
        self.assertIn('Salaries', AppConfig.EXPENSE_CATEGORIES)


if __name__ == '__main__':
    unittest.main()
