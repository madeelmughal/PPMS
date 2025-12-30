"""
UI Screens Package - Main user interface screens
"""

from src.ui.screens.login_screen import LoginScreen
from src.ui.screens.dashboard_screen import DashboardScreen
from src.ui.screens.fuel_management_screen import FuelManagementScreen
from src.ui.screens.sales_entry_screen import SalesEntryScreen
from src.ui.screens.customer_management_screen import CustomerManagementScreen
from src.ui.screens.expense_management_screen import ExpenseManagementScreen
from src.ui.screens.shift_management_screen import ShiftManagementScreen
from src.ui.screens.reports_screen import ReportsScreen
from src.ui.screens.settings_management_screen import SettingsManagementScreen

__all__ = [
    'LoginScreen',
    'DashboardScreen',
    'FuelManagementScreen',
    'SalesEntryScreen',
    'CustomerManagementScreen',
    'ExpenseManagementScreen',
    'ShiftManagementScreen',
    'ReportsScreen',
    'SettingsManagementScreen'
]
