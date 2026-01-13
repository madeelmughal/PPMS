"""
Dashboard Screen - Main application dashboard
"""

from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QGridLayout, QFrame, QScrollArea, QMenuBar, QMenu, QDialog, QLineEdit,
    QDoubleSpinBox, QSpinBox, QComboBox, QMessageBox, QFormLayout, QTableWidget,
    QTableWidgetItem, QHeaderView, QTabWidget, QFileDialog, QDateEdit
)
from PyQt5.QtCore import Qt, QTimer, pyqtSignal, QDate
from PyQt5.QtGui import QFont, QColor
from src.services.database_service import (
    FuelService, TankService, SalesService, DatabaseService, NozzleService, CustomerService, AccountHeadService
)
from src.config.firebase_config import AppConfig
from src.config.logger_config import setup_logger
from src.ui.screens.inventory_screen import UpdateStockLevelDialog
from datetime import datetime

import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import numpy as np

logger = setup_logger(__name__)


class DailyTransactionsReportDialog(QDialog):
    """Dialog for daily transactions report with date range filtering and dynamic stats calculation."""

    def __init__(self, parent, all_sales, all_purchases, all_expenses, nozzle_service, tank_service, fuel_service):
        """Initialize dialog."""
        super().__init__(parent)
        self.all_sales = all_sales
        self.all_purchases = all_purchases
        self.all_expenses = all_expenses
        self.nozzle_service = nozzle_service
        self.tank_service = tank_service
        self.fuel_service = fuel_service
        
        self.setWindowTitle("Daily Transactions Report")
        self.resize(1300, 750)
        self.setStyleSheet(
            "QDialog { background-color: #f5f5f5; }"
            "QLabel { color: #333; }"
            "QDateEdit { padding: 5px; border: 1px solid #ddd; border-radius: 3px; }"
        )
        
        # Center on screen
        from PyQt5.QtWidgets import QDesktopWidget
        screen = QDesktopWidget().screenGeometry()
        size = self.geometry()
        self.move((screen.width() - size.width()) // 2, (screen.height() - size.height()) // 2)
        
        self.init_ui()
        self.apply_date_filter()  # Load initial data

    def init_ui(self):
        """Initialize UI components."""
        layout = QVBoxLayout()
        
        # Header
        header = QLabel("Daily Transactions Report")
        header.setFont(QFont("Arial", 14, QFont.Bold))
        layout.addWidget(header)
        
        # Date filter controls
        filter_layout = QHBoxLayout()
        filter_layout.addWidget(QLabel("Date Range:"))
        
        self.start_date_filter = QDateEdit()
        self.start_date_filter.setDate(QDate.currentDate().addDays(-30))
        self.start_date_filter.setCalendarPopup(True)
        self.start_date_filter.dateChanged.connect(self.apply_date_filter)
        filter_layout.addWidget(self.start_date_filter)
        
        filter_layout.addWidget(QLabel("To:"))
        self.end_date_filter = QDateEdit()
        self.end_date_filter.setDate(QDate.currentDate())
        self.end_date_filter.setCalendarPopup(True)
        self.end_date_filter.dateChanged.connect(self.apply_date_filter)
        filter_layout.addWidget(self.end_date_filter)
        
        reset_btn = QPushButton("Reset Filter")
        reset_btn.setMaximumWidth(100)
        reset_btn.clicked.connect(self.reset_filter)
        filter_layout.addWidget(reset_btn)
        filter_layout.addStretch()
        
        layout.addLayout(filter_layout)
        
        # Summary stats section
        self.summary_layout = QHBoxLayout()
        layout.addLayout(self.summary_layout)
        
        # Create tabs for different transaction types
        self.tabs = QTabWidget()
        layout.addWidget(self.tabs)
        
        # Export and Close buttons
        button_layout = QHBoxLayout()
        pdf_btn = QPushButton("📄 Export to PDF")
        pdf_btn.clicked.connect(self.export_to_pdf)
        button_layout.addWidget(pdf_btn)
        button_layout.addStretch()
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.accept)
        button_layout.addWidget(close_btn)
        layout.addLayout(button_layout)
        
        self.setLayout(layout)

    def apply_date_filter(self):
        """Apply date filter and refresh stats and tables."""
        start_date = self.start_date_filter.date().toString("yyyy-MM-dd")
        end_date = self.end_date_filter.date().toString("yyyy-MM-dd")
        
        # Filter transactions by date range
        filtered_sales = [s for s in self.all_sales 
                         if self._check_date_in_range(s.get('date', ''), start_date, end_date)]
        filtered_purchases = [p for p in self.all_purchases 
                             if self._check_date_in_range(p.get('purchase_date', p.get('date', '')), start_date, end_date)]
        filtered_expenses = [e for e in self.all_expenses 
                            if self._check_date_in_range(e.get('expense_date', e.get('date', '')), start_date, end_date)]
        
        # Calculate stats based on filtered data
        total_sales = sum(float(s.get('total_amount', 0)) for s in filtered_sales)
        total_sale_qty = sum(float(s.get('quantity', 0)) for s in filtered_sales)
        total_purchases = sum(float(p.get('total_cost', 0)) for p in filtered_purchases)
        total_expenses = sum(float(e.get('amount', 0)) for e in filtered_expenses)
        net_profit = total_sales - total_purchases - total_expenses
        
        # Update summary stats
        self._update_summary_stats(total_sales, total_sale_qty, total_purchases, total_expenses, net_profit)
        
        # Update tabs with filtered data
        self._update_tables(filtered_sales, filtered_purchases, filtered_expenses)

    def reset_filter(self):
        """Reset date filter to default."""
        self.start_date_filter.setDate(QDate.currentDate().addDays(-30))
        self.end_date_filter.setDate(QDate.currentDate())

    def _check_date_in_range(self, date_str, start_date, end_date):
        """Check if date string is within range."""
        if not date_str:
            return False
        date_part = date_str[:10]  # Extract YYYY-MM-DD
        return start_date <= date_part <= end_date

    def _update_summary_stats(self, total_sales, total_sale_qty, total_purchases, total_expenses, net_profit):
        """Update summary statistics display."""
        # Clear existing stats
        while self.summary_layout.count():
            self.summary_layout.takeAt(0).widget().deleteLater()
        
        # Add new stats with improved color scheme
        self.summary_layout.addWidget(self._create_stat_card("Total Sales", f"Rs. {total_sales:,.2f}", "#27AE60"))
        self.summary_layout.addWidget(self._create_stat_card("Fuel Sold", f"{total_sale_qty:,.2f} L", "#3498DB"))
        self.summary_layout.addWidget(self._create_stat_card("Purchases", f"Rs. {total_purchases:,.2f}", "#E67E22"))
        self.summary_layout.addWidget(self._create_stat_card("Expenses", f"Rs. {total_expenses:,.2f}", "#E74C3C"))
        # Net Profit always uses purple/violet color
        self.summary_layout.addWidget(self._create_stat_card("Net Profit", f"Rs. {net_profit:,.2f}", "#8E44AD"))

    def _create_stat_card(self, label, value, color):
        """Create a statistics card with improved styling."""
        card = QFrame()
        card.setStyleSheet(f"""
            QFrame {{
                background-color: white;
                border-left: 5px solid {color};
                border-radius: 4px;
                padding: 15px;
                box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
            }}
        """)
        
        layout = QVBoxLayout()
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(5)
        
        label_widget = QLabel(label)
        label_widget.setFont(QFont("Arial", 10, QFont.Bold))
        label_widget.setStyleSheet(f"color: {color}; font-weight: bold;")
        
        value_widget = QLabel(value)
        value_widget.setFont(QFont("Arial", 13, QFont.Bold))
        value_widget.setStyleSheet("color: #2C3E50; font-weight: bold;")
        
        layout.addWidget(label_widget)
        layout.addWidget(value_widget)
        card.setLayout(layout)
        
        return card

    def _update_tables(self, sales_data, purchases_data, expenses_data):
        """Update transaction tables."""
        # Clear existing tabs
        while self.tabs.count():
            self.tabs.removeTab(0)
        
        # Sales Tab
        sales_table = self._create_sales_table(sales_data)
        self.tabs.addTab(sales_table, f"Sales ({len(sales_data)})")
        
        # Purchases Tab
        purchases_table = self._create_purchases_table(purchases_data)
        self.tabs.addTab(purchases_table, f"Purchases ({len(purchases_data)})")
        
        # Expenses Tab
        expenses_table = self._create_expenses_table(expenses_data)
        self.tabs.addTab(expenses_table, f"Expenses ({len(expenses_data)})")

    def _create_sales_table(self, sales_data):
        """Create sales transactions table."""
        table = QTableWidget()
        table.setColumnCount(11)
        table.setHorizontalHeaderLabels([
            "Nozzle", "Fuel Type", "Open Reading", "Quantity (L)", "Close Reading",
            "Unit Price (Rs)", "Total (Rs)", "Payment Method", "Customer", "Date", "Time"
        ])
        table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        table.setRowCount(len(sales_data))
        
        # Get lookup data
        nozzles = {n.id: f"M{n.machine_id}-N{n.nozzle_number}" for n in self.nozzle_service.list_nozzles()}
        fuels = {f.id: f.name for f in self.fuel_service.list_fuel_types()}
        
        for row, sale in enumerate(sales_data):
            nozzle_name = nozzles.get(sale.get('nozzle_id', ''), 'Unknown')
            fuel_name = fuels.get(sale.get('fuel_type_id', ''), 'Unknown')
            
            date_str = sale.get('date', '')
            date_display = date_str[:10] if len(date_str) > 10 else ''
            time_str = date_str[11:19] if len(date_str) > 11 else ''
            
            items = [
                QTableWidgetItem(nozzle_name),
                QTableWidgetItem(fuel_name),
                QTableWidgetItem(f"{float(sale.get('opening_reading', 0)):,.2f}"),
                QTableWidgetItem(f"{float(sale.get('quantity', 0)):,.2f}"),
                QTableWidgetItem(f"{float(sale.get('closing_reading', 0)):,.2f}"),
                QTableWidgetItem(f"{float(sale.get('unit_price', 0)):,.2f}"),
                QTableWidgetItem(f"{float(sale.get('total_amount', 0)):,.2f}"),
                QTableWidgetItem(sale.get('payment_method', 'Cash')),
                QTableWidgetItem(sale.get('customer_name', 'Walk-in')),
                QTableWidgetItem(date_display),
                QTableWidgetItem(time_str)
            ]
            
            for col_idx, item in enumerate(items):
                item.setFlags(item.flags() & ~Qt.ItemIsEditable)
                table.setItem(row, col_idx, item)
        
        return table

    def _create_purchases_table(self, purchases_data):
        """Create purchases transactions table."""
        table = QTableWidget()
        table.setColumnCount(8)
        table.setHorizontalHeaderLabels([
            "Tank", "Fuel Type", "Quantity (L)", "Unit Cost (Rs)", 
            "Total Cost (Rs)", "Account Head", "Supplier", "Date"
        ])
        table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        table.setRowCount(len(purchases_data))
        
        # Get lookup data
        tanks = {t.id: {'name': t.name, 'fuel_type_id': t.fuel_type_id} for t in self.tank_service.list_tanks()}
        fuels = {f.id: f.name for f in self.fuel_service.list_fuel_types()}
        
        for row, purchase in enumerate(purchases_data):
            tank_id = purchase.get('tank_id', '')
            tank_info = tanks.get(tank_id, {})
            tank_name = tank_info.get('name', 'Unknown')
            
            tank_fuel_type_id = tank_info.get('fuel_type_id', '')
            fuel_name = fuels.get(tank_fuel_type_id, 'Unknown')
            
            date_str = purchase.get('purchase_date', purchase.get('date', ''))
            date_display = date_str[:10] if date_str else ''
            
            items = [
                QTableWidgetItem(tank_name),
                QTableWidgetItem(fuel_name),
                QTableWidgetItem(f"{float(purchase.get('quantity', 0)):,.2f}"),
                QTableWidgetItem(f"{float(purchase.get('unit_cost', 0)):,.2f}"),
                QTableWidgetItem(f"{float(purchase.get('total_cost', 0)):,.2f}"),
                QTableWidgetItem(purchase.get('account_head_name', '')),
                QTableWidgetItem(purchase.get('supplier_name', 'Unknown')),
                QTableWidgetItem(date_display)
            ]
            
            for col_idx, item in enumerate(items):
                item.setFlags(item.flags() & ~Qt.ItemIsEditable)
                table.setItem(row, col_idx, item)
        
        return table

    def _create_expenses_table(self, expenses_data):
        """Create expenses transactions table."""
        table = QTableWidget()
        table.setColumnCount(6)
        table.setHorizontalHeaderLabels([
            "Description", "Category", "Amount (Rs)", "Payment Method", "Notes", "Date"
        ])
        table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        table.setRowCount(len(expenses_data))
        
        for row, expense in enumerate(expenses_data):
            date_str = expense.get('expense_date', expense.get('date', ''))
            date_display = date_str[:10] if date_str else ''
            
            items = [
                QTableWidgetItem(expense.get('description', '')),
                QTableWidgetItem(expense.get('category', '')),
                QTableWidgetItem(f"{float(expense.get('amount', 0)):,.2f}"),
                QTableWidgetItem(expense.get('payment_method', '')),
                QTableWidgetItem(expense.get('notes', '')),
                QTableWidgetItem(date_display)
            ]
            
            for col_idx, item in enumerate(items):
                item.setFlags(item.flags() & ~Qt.ItemIsEditable)
                table.setItem(row, col_idx, item)
        
        return table

    def export_to_pdf(self):
        """Export filtered transactions to PDF."""
        QMessageBox.information(self, "Export", "PDF export feature coming soon!")


class DataViewDialog(QDialog):
    """Professional data view dialog with table grid and date filtering."""

    def __init__(self, title, columns, data, parent=None, date_field=None, raw_data=None):
        """Initialize data view dialog.
        
        Args:
            title: Dialog title
            columns: List of column names
            data: List of lists with display data
            parent: Parent widget
            date_field: Name of the date field in raw_data for filtering
            raw_data: Original data dictionaries for filtering purposes
        """
        super().__init__(parent)
        self.setWindowTitle(title)
        self.resize(1200, 700)
        # Center on screen
        from PyQt5.QtWidgets import QDesktopWidget, QDateEdit
        screen = QDesktopWidget().screenGeometry()
        size = self.geometry()
        self.move((screen.width() - size.width()) // 2, (screen.height() - size.height()) // 2)
        self.setStyleSheet(
            "QDialog { background-color: #f5f5f5; }"
            "QTableWidget { background-color: white; alternate-background-color: #f9f9f9; border: 1px solid #ddd; }"
            "QHeaderView::section { background-color: #2196F3; color: white; padding: 5px; border: none; font-weight: bold; }"
            "QTableWidget::item { padding: 5px; border-bottom: 1px solid #e0e0e0; color: #333333; }"
            "QTableWidget::item:selected { background-color: #2196F3; color: white; }"
            "QPushButton { background-color: #4CAF50; color: white; padding: 8px 20px; border-radius: 5px; font-weight: bold; }"
            "QPushButton:hover { background-color: #45a049; }"
            "QDateEdit { padding: 5px; border: 1px solid #ddd; border-radius: 3px; }"
            "QLabel { color: #333; font-weight: bold; }"
        )
        
        # Store data for filtering
        self.date_field = date_field
        self.raw_data = raw_data or []
        self.all_data = data  # Original data
        self.display_columns = columns
        
        # Layout
        layout = QVBoxLayout()
        
        # Title label
        title_label = QLabel(title)
        title_label.setFont(QFont("Arial", 14, QFont.Bold))
        layout.addWidget(title_label)
        
        # Date filter section (if date field is available)
        if date_field and raw_data:
            filter_layout = QHBoxLayout()
            filter_layout.addWidget(QLabel("Date Filter:"))
            
            self.filter_start_date = QDateEdit()
            self.filter_start_date.setDate(QDate.currentDate().addMonths(-1))
            self.filter_start_date.setCalendarPopup(True)
            self.filter_start_date.dateChanged.connect(self.apply_date_filter)
            filter_layout.addWidget(self.filter_start_date)
            
            filter_layout.addWidget(QLabel("To:"))
            self.filter_end_date = QDateEdit()
            self.filter_end_date.setDate(QDate.currentDate())
            self.filter_end_date.setCalendarPopup(True)
            self.filter_end_date.dateChanged.connect(self.apply_date_filter)
            filter_layout.addWidget(self.filter_end_date)
            
            self.reset_filter_btn = QPushButton("Reset Filter")
            self.reset_filter_btn.clicked.connect(self.reset_filter)
            filter_layout.addWidget(self.reset_filter_btn)
            
            filter_layout.addStretch()
            layout.addLayout(filter_layout)
        
        # Create table
        self.table = QTableWidget()
        self.table.setColumnCount(len(columns))
        self.table.setHorizontalHeaderLabels(columns)
        self.table.setAlternatingRowColors(True)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        
        # Set column widths based on column type
        self._set_column_widths(columns)
        
        # Store table data and fill it
        self.table_data = data
        self.populate_table(data)
        
        layout.addWidget(self.table)
        
        # Close button
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.accept)
        close_btn.setMaximumWidth(100)
        
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        btn_layout.addWidget(close_btn)
        layout.addLayout(btn_layout)
        
        self.setLayout(layout)

    def populate_table(self, data):
        """Populate table with data."""
        self.table.setRowCount(len(data))
        for row_idx, row_data in enumerate(data):
            for col_idx, cell_value in enumerate(row_data):
                item = QTableWidgetItem(str(cell_value))
                item.setFlags(item.flags() & ~Qt.ItemIsEditable)
                self.table.setItem(row_idx, col_idx, item)

    def apply_date_filter(self):
        """Apply date filter to table data."""
        if not self.date_field or not self.raw_data:
            return
        
        start_date = self.filter_start_date.date().toString("yyyy-MM-dd")
        end_date = self.filter_end_date.date().toString("yyyy-MM-dd")
        
        filtered_data = []
        for idx, raw_item in enumerate(self.raw_data):
            if idx >= len(self.all_data):
                break
            
            # Extract date from raw data
            date_str = self._extract_date(raw_item)
            
            if date_str and start_date <= date_str <= end_date:
                filtered_data.append(self.all_data[idx])
        
        if not filtered_data:
            filtered_data = [["No records found for selected date range"] + [""] * (len(self.display_columns) - 1)]
        
        self.populate_table(filtered_data)

    def reset_filter(self):
        """Reset date filter."""
        self.filter_start_date.setDate(QDate.currentDate().addMonths(-1))
        self.filter_end_date.setDate(QDate.currentDate())
        self.populate_table(self.all_data)

    def _extract_date(self, raw_item):
        """Extract date from raw item."""
        if isinstance(raw_item, dict):
            # Try multiple date field names
            for field in [self.date_field, 'date', 'timestamp', 'created_at', 'purchase_date', 'expense_date', 'sale_date']:
                if field in raw_item:
                    date_val = raw_item[field]
                    if isinstance(date_val, str):
                        return date_val[:10]  # Get YYYY-MM-DD format
        return None

    def _set_column_widths(self, columns):
        """Set column widths based on column names - wider for text, narrower for numbers."""
        # Define wide columns (text fields)
        wide_columns = ['Name', 'Description', 'Address', 'Email', 'Notes', 'Location', 'Supplier', 'Nozzle', 'Tank']
        # Define medium columns
        medium_columns = ['Phone', 'Type', 'Category', 'Payment', 'Payment Method', 'Invoice', 'Reference', 'Code', 
                          'Machine ID', 'Fuel Type', 'From Currency', 'To Currency']
        # Define narrow columns (numeric fields)
        narrow_columns = ['Rate', 'Tax', 'Tax %', 'Amount', 'Price', 'Total', 'Quantity', 'Unit Price', 'Unit Cost',
                          'Capacity', 'Min Stock', 'Credit Limit', 'Opening Reading', 'Nozzle Number', 'Date',
                          'Effective Date']
        
        for col_idx, col_name in enumerate(columns):
            # Check for wide columns (text)
            if any(wide in col_name for wide in wide_columns):
                self.table.setColumnWidth(col_idx, 200)
            # Check for medium columns
            elif any(med in col_name for med in medium_columns):
                self.table.setColumnWidth(col_idx, 130)
            # Check for narrow columns (numeric)
            elif any(narrow in col_name for narrow in narrow_columns):
                self.table.setColumnWidth(col_idx, 100)
            else:
                self.table.setColumnWidth(col_idx, 120)  # Default width
        
        # Stretch last section to fill remaining space
        self.table.horizontalHeader().setStretchLastSection(True)


class DashboardScreen(QMainWindow):
    """Main dashboard screen."""

    logout_requested = pyqtSignal()

    def __init__(self, user):
        """Initialize dashboard."""
        super().__init__()
        self.user = user
        self.fuel_service = FuelService()
        self.tank_service = TankService()
        self.sales_service = SalesService()
        self.db_service = DatabaseService()
        self.nozzle_service = NozzleService()
        self.customer_service = CustomerService()
        self.account_head_service = AccountHeadService()
        
        # KPI card label references for dynamic updates
        self.kpi_labels = {}
        self.payment_methods = []

        self.setWindowTitle(f"PPMS Dashboard - {user.name}")
        self.setGeometry(100, 100, 1400, 900)

        self.init_ui()
        self.setup_refresh_timer()
        self.load_dashboard_data()

    def init_ui(self):
        """Initialize UI components with professional dashboard design."""
        # Create menu bar using QMainWindow's built-in menu bar
        self.create_menu_bar()

        # Main central widget
        central_widget = QWidget()
        central_widget.setStyleSheet("background-color: #f0f2f5;")
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Top header with logo and user info - Professional gradient style
        header_frame = QFrame()
        header_frame.setStyleSheet("""
            QFrame {
                background-color: #1a2332;
                padding: 10px 15px;
                border-bottom: 3px solid #2196F3;
            }
        """)
        header_layout = QHBoxLayout()
        header_layout.setContentsMargins(15, 6, 15, 6)
        header_layout.setSpacing(15)

        # Logo section with icon placeholder
        logo_label = QLabel("📊 PPMS")
        logo_font = QFont("Arial", 18, QFont.Bold)
        logo_label.setFont(logo_font)
        logo_label.setStyleSheet("color: #2196F3;")
        header_layout.addWidget(logo_label)

        # Subtitle
        subtitle_label = QLabel("Petroleum Point of Sales Management System")
        subtitle_font = QFont("Arial", 9)
        subtitle_label.setFont(subtitle_font)
        subtitle_label.setStyleSheet("color: #b0b0b0;")
        header_layout.addWidget(subtitle_label)

        header_layout.addStretch()

        # User section with role badge
        role_text = str(self.user.role.name) if hasattr(self.user.role, 'name') else str(self.user.role)
        role_badge = QLabel(f"👤 {role_text.upper()}")
        role_badge.setFont(QFont("Arial", 8))
        role_badge.setStyleSheet("""
            background-color: rgba(33, 150, 243, 0.2);
            color: #2196F3;
            padding: 4px 10px;
            border-radius: 12px;
            border: 1px solid #2196F3;
        """)
        header_layout.addWidget(role_badge)

        user_label = QLabel(f"{self.user.name}")
        user_label.setFont(QFont("Arial", 10, QFont.Bold))
        user_label.setStyleSheet("color: white;")
        header_layout.addWidget(user_label)

        logout_btn = QPushButton("🚪 Logout")
        logout_btn.setMaximumWidth(110)
        logout_btn.setMaximumHeight(32)
        logout_btn.setFont(QFont("Arial", 9, QFont.Bold))
        logout_btn.setStyleSheet("""
            QPushButton {
                background-color: #0052CC;
                color: white;
                border: none;
                padding: 6px 14px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #0041a3;
                border: 2px solid white;
            }
            QPushButton:pressed {
                background-color: #003080;
            }
        """)
        logout_btn.setCursor(Qt.PointingHandCursor)
        logout_btn.clicked.connect(self.logout_requested.emit)
        header_layout.addWidget(logout_btn)

        header_frame.setLayout(header_layout)
        main_layout.addWidget(header_frame)

        # Scroll area for dashboard content
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("""
            QScrollArea {
                border: none;
                background-color: #f0f2f5;
            }
            QScrollBar:vertical {
                background-color: #f0f2f5;
                width: 10px;
                border-radius: 5px;
            }
            QScrollBar::handle:vertical {
                background-color: #bdbdbd;
                border-radius: 5px;
                min-height: 20px;
            }
            QScrollBar::handle:vertical:hover {
                background-color: #9e9e9e;
            }
        """)
        scroll_widget = QWidget()
        scroll_widget.setStyleSheet("background-color: #f0f2f5;")
        scroll_layout = QVBoxLayout(scroll_widget)
        scroll_layout.setContentsMargins(15, 15, 15, 15)
        scroll_layout.setSpacing(15)

        # ===== KPI CARDS SECTION =====
        # Section title
        kpi_title = QLabel("📈 Key Performance Indicators")
        kpi_title.setFont(QFont("Arial", 14, QFont.Bold))
        kpi_title.setStyleSheet("color: #1a2332;")
        scroll_layout.addWidget(kpi_title)

        kpi_layout = QGridLayout()
        kpi_layout.setSpacing(12)
        kpi_layout.setColumnStretch(0, 1)
        kpi_layout.setColumnStretch(1, 1)
        kpi_layout.setColumnStretch(2, 1)

        # Card 1: Total Sales (Yellow)
        sales_card, sales_label = self.create_kpi_card(
            "Total Sales",
            "0",
            "0",
            "#FFC107",
            "Units"
        )
        self.kpi_labels['total_sales'] = sales_label
        kpi_layout.addWidget(sales_card, 0, 0)

        # Card 2: Total Revenue (Green) - Net Revenue = Sales - Purchases
        revenue_card, revenue_label = self.create_kpi_card(
            "Net Revenue",
            "0",
            "0",
            "#4CAF50",
            "PKR"
        )
        self.kpi_labels['total_revenue'] = revenue_label
        kpi_layout.addWidget(revenue_card, 0, 1)

        # Card 3: Average Ticket (Blue)
        ticket_card, ticket_label = self.create_kpi_card(
            "Average Ticket",
            "0",
            "0",
            "#2196F3",
            "PKR"
        )
        self.kpi_labels['average_ticket'] = ticket_label
        kpi_layout.addWidget(ticket_card, 0, 2)

        # Card 4: Daily Fuel Sold (Orange)
        fuel_card, fuel_label = self.create_kpi_card(
            "Daily Fuel Sold",
            "0",
            "0",
            "#FF9800",
            "Liters"
        )
        self.kpi_labels['daily_fuel'] = fuel_label
        kpi_layout.addWidget(fuel_card, 1, 0)

        # Card 5: Total Customers (Purple)
        customers_card, customers_label = self.create_kpi_card(
            "Total Customers",
            "0",
            "0",
            "#9C27B0",
            "Count"
        )
        self.kpi_labels['total_customers'] = customers_label
        kpi_layout.addWidget(customers_card, 1, 1)

        # Card 6: Conversion Rate (Red)
        conversion_card, conversion_label = self.create_kpi_card(
            "Inventory Status",
            "0",
            "0",
            "#F44336",
            "Liters"
        )
        self.kpi_labels['inventory_status'] = conversion_label
        kpi_layout.addWidget(conversion_card, 1, 2)

        scroll_layout.addLayout(kpi_layout)

        # ===== CHARTS SECTION =====
        charts_title = QLabel("📊 Analytics & Reports")
        charts_title.setFont(QFont("Arial", 14, QFont.Bold))
        charts_title.setStyleSheet("color: #1a2332; margin-top: 20px;")
        scroll_layout.addWidget(charts_title)

        charts_layout = QGridLayout()
        charts_layout.setSpacing(12)

        # Chart 1: Monthly Sales Trend (Bar Chart)
        chart_1 = self.create_demo_bar_chart("📈 Monthly Sales Trend", 250)
        charts_layout.addWidget(chart_1, 0, 0, 1, 2)

        # Chart 2: Top 5 Customers (List)
        chart_2 = self.create_demo_customer_list("👥 Top 5 Customers", 220)
        charts_layout.addWidget(chart_2, 1, 0)

        # Chart 3: Fuel Type Distribution (Pie Chart)
        chart_3 = self.create_demo_fuel_chart("⛽ Fuel Type Distribution", 220)
        charts_layout.addWidget(chart_3, 1, 1)

        scroll_layout.addLayout(charts_layout)

        # ===== QUICK ACTIONS SECTION =====
        actions_title = QLabel("⚡ Quick Actions")
        actions_title.setFont(QFont("Arial", 14, QFont.Bold))
        actions_title.setStyleSheet("color: #1a2332; margin-top: 20px;")
        scroll_layout.addWidget(actions_title)

        actions_layout = QHBoxLayout()
        actions_layout.setSpacing(8)
        actions_layout.setContentsMargins(0, 10, 0, 10)

        actions = [
            ("💰 Record Sale", "#0052CC", self.record_sale_dialog),
            ("👤 Add Customer", "#0052CC", self.add_customer_dialog),
            ("🛢️ Record Purchase", "#0052CC", self.record_purchase_dialog),
            ("📝 Record Expense", "#0052CC", self.record_expense_dialog),
            ("📊 View Reports", "#0052CC", self.view_sales_records),
        ]

        for btn_text, color, handler in actions:
            btn = QPushButton(btn_text)
            btn.setMinimumHeight(42)
            btn.setMinimumWidth(130)
            btn.setFont(QFont("Arial", 10, QFont.Bold))
            btn.setCursor(Qt.PointingHandCursor)
            btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: {color};
                    color: white;
                    border: none;
                    border-radius: 6px;
                    padding: 10px 16px;
                    font-weight: bold;
                }}
                QPushButton:hover {{
                    background-color: {self.lighten_color(color)};
                }}
                QPushButton:pressed {{
                    background-color: {self.darken_color(color)};
                }}
            """)
            btn.clicked.connect(handler)
            actions_layout.addWidget(btn)

        scroll_layout.addLayout(actions_layout)
        scroll_layout.addSpacing(20)
        scroll_layout.addStretch()

        scroll.setWidget(scroll_widget)
        main_layout.addWidget(scroll)

        central_widget.setLayout(main_layout)
        self.setCentralWidget(central_widget)

    def create_demo_bar_chart(self, title, height):
        """Create a professional bar chart using matplotlib."""
        # Create figure and axis
        fig = Figure(figsize=(12, 3.5), dpi=100, facecolor='white')
        ax = fig.add_subplot(111)
        
        # Data
        months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Ago", "Set", "Out", "Nov", "Dez"]
        vendas = [3, 3, 5, 2, 5, 7, 0, 0, 0, 0, 0, 0]
        meta = [3, 3, 5, 2, 5, 7, 0, 0, 0, 0, 0, 0]
        
        # Position for bars
        x = np.arange(len(months))
        width = 0.35
        
        # Create bars
        bars1 = ax.bar(x - width/2, vendas, width, label='Vendas', color='#FFC107', edgecolor='none')
        bars2 = ax.bar(x + width/2, meta, width, label='Meta', color='#FFB74D', edgecolor='none')
        
        # Add value labels on top of bars
        for bar in bars1:
            height_bar = bar.get_height()
            if height_bar > 0:
                ax.text(bar.get_x() + bar.get_width()/2., height_bar,
                        f'{int(height_bar)}', ha='center', va='bottom', fontsize=9, fontweight='bold', color='#FFC107')
        
        for bar in bars2:
            height_bar = bar.get_height()
            if height_bar > 0:
                ax.text(bar.get_x() + bar.get_width()/2., height_bar,
                        f'{int(height_bar)}', ha='center', va='bottom', fontsize=9, fontweight='bold', color='#FFB74D')
        
        # Customize chart
        ax.set_ylabel('', fontsize=10)
        ax.set_xticks(x)
        ax.set_xticklabels(months, fontsize=10, fontweight='bold')
        ax.set_ylim(0, 8)
        ax.legend(loc='upper left', fontsize=10, frameon=False)
        ax.grid(axis='y', alpha=0.3, linestyle='--')
        ax.set_axisbelow(True)
        
        # Remove top and right spines
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        
        fig.suptitle(title, fontsize=12, fontweight='bold', color='#1a2332', y=0.98)
        fig.tight_layout(rect=[0, 0, 1, 0.96])
        
        # Create canvas
        canvas = FigureCanvas(fig)
        canvas.setMinimumHeight(height)
        
        return canvas

    def create_demo_customer_list(self, title, height):
        """Create a professional bar chart for top customers using matplotlib."""
        # Create figure and axis
        fig = Figure(figsize=(5, 3.5), dpi=100, facecolor='white')
        ax = fig.add_subplot(111)
        
        # Data
        customers = ["Petrol Corp", "Fuel Systems", "Energy Solutions", "Transport Hub", "Commercial Fleet"]
        amounts = [45250, 38900, 32150, 28500, 24300]
        
        # Create horizontal bars
        colors = ['#2196F3', '#1976D2', '#1565C0', '#0D47A1', '#0A3F7B']
        bars = ax.barh(customers, amounts, color=colors, edgecolor='none')
        
        # Add value labels
        for i, (bar, amount) in enumerate(zip(bars, amounts)):
            ax.text(amount, bar.get_y() + bar.get_height()/2, f'₹ {amount:,}',
                    ha='left', va='center', fontsize=10, fontweight='bold', color='#1a2332')
        
        # Customize chart
        ax.set_xlabel('', fontsize=10)
        ax.set_ylim(-0.5, len(customers) - 0.5)
        ax.grid(axis='x', alpha=0.3, linestyle='--')
        ax.set_axisbelow(True)
        
        # Remove spines
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        ax.spines['left'].set_color('#ddd')
        
        fig.suptitle(title, fontsize=12, fontweight='bold', color='#1a2332', y=0.98)
        fig.tight_layout(rect=[0, 0, 1, 0.96])
        
        # Create canvas
        canvas = FigureCanvas(fig)
        canvas.setMinimumHeight(height)
        
        return canvas

    def create_demo_fuel_chart(self, title, height):
        """Create a line chart for fuel type distribution using matplotlib."""
        # Create figure and axis
        fig = Figure(figsize=(5, 3.5), dpi=100, facecolor='white')
        ax = fig.add_subplot(111)
        
        # Data - Fuel types and their monthly distribution
        months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun']
        petrol = [45, 48, 42, 50, 55, 60]
        diesel = [35, 32, 38, 30, 28, 25]
        cng = [15, 16, 15, 14, 12, 10]
        lpg = [5, 4, 5, 6, 5, 5]
        
        # Create line chart
        ax.plot(months, petrol, marker='o', linewidth=2.5, markersize=6, 
                label='Petrol', color='#FFC107', markerfacecolor='#FFD54F')
        ax.plot(months, diesel, marker='s', linewidth=2.5, markersize=6,
                label='Diesel', color='#FF9800', markerfacecolor='#FFB74D')
        ax.plot(months, cng, marker='^', linewidth=2.5, markersize=6,
                label='CNG', color='#2196F3', markerfacecolor='#64B5F6')
        ax.plot(months, lpg, marker='D', linewidth=2.5, markersize=6,
                label='LPG', color='#9C27B0', markerfacecolor='#CE93D8')
        
        # Customize chart
        ax.set_ylabel('Distribution %', fontsize=10, color='#1a2332')
        ax.set_ylim(0, 70)
        ax.grid(True, alpha=0.3, linestyle='--')
        ax.set_axisbelow(True)
        
        # Legend
        ax.legend(loc='upper left', fontsize=9, frameon=True, fancybox=False, 
                  edgecolor='#e0e0e0', framealpha=0.95)
        
        # Remove spines
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        ax.spines['left'].set_color('#ddd')
        ax.spines['bottom'].set_color('#ddd')
        
        fig.suptitle(title, fontsize=12, fontweight='bold', color='#1a2332', y=0.98)
        fig.tight_layout(rect=[0, 0, 1, 0.96])
        
        # Create canvas
        canvas = FigureCanvas(fig)
        canvas.setMinimumHeight(height)
        
        return canvas

    def create_kpi_card(self, title, value, meta_value, color, meta_label):
        """Create a clean professional KPI card with figure only."""
        card = QFrame()
        card.setStyleSheet(f"""
            QFrame {{
                background-color: {color};
                border-radius: 6px;
                padding: 8px;
            }}
        """)
        card.setMinimumHeight(140)
        card.setMaximumHeight(160)
        card.setCursor(Qt.PointingHandCursor)

        layout = QVBoxLayout()
        layout.setContentsMargins(4, 4, 4, 4)
        layout.setSpacing(0)

        # Title - Small, at top
        title_label = QLabel(title)
        title_label.setFont(QFont("Arial", 9, QFont.Bold))
        title_label.setStyleSheet("color: white; opacity: 0.95;")
        title_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(title_label, 1)

        # Main value - Large and prominent, centered
        value_label = QLabel(value)
        value_font = QFont("Arial", 36, QFont.Bold)
        value_label.setFont(value_font)
        value_label.setStyleSheet("color: white;")
        value_label.setAlignment(Qt.AlignCenter | Qt.AlignVCenter)
        value_label.setMinimumHeight(55)
        layout.addWidget(value_label, 2)

        layout.addStretch()

        card.setLayout(layout)
        return card, value_label

    def lighten_color(self, color_hex):
        """Lighten a hex color by 20%."""
        from PyQt5.QtGui import QColor
        color = QColor(color_hex)
        h, s, v, a = color.getHsv()
        color.setHsv(h, s, min(255, v + 40), a)
        return color.name()

    def darken_color(self, color_hex):
        """Darken a hex color by 20%."""
        from PyQt5.QtGui import QColor
        color = QColor(color_hex)
        h, s, v, a = color.getHsv()
        color.setHsv(h, s, max(0, v - 40), a)
        return color.name()

    def create_menu_bar(self):
        """Create professional menu bar using QMainWindow's menu bar."""
        menubar = self.menuBar()
        menubar.setStyleSheet(
            "QMenuBar { background-color: #f5f5f5; color: #333; border-bottom: 1px solid #ddd; font-size: 12pt; }"
            "QMenuBar::item:selected { background-color: #e0e0e0; }"
            "QMenu { background-color: #ffffff; color: #333; border: 1px solid #ddd; font-size: 11pt; }"
            "QMenu::item:selected { background-color: #e3f2fd; }"
        )
        
        # File Menu
        file_menu = menubar.addMenu("File")
        file_menu.addAction("Export Data", self.export_data)
        file_menu.addSeparator()
        file_menu.addAction("Exit", self.logout_requested.emit)
        
        # View Menu
        view_menu = menubar.addMenu("View")
        view_menu.addAction("View Sales", self.view_sales_records)
        view_menu.addAction("View Purchase", self.view_purchase_records)  
        view_menu.addAction("View Expenses", self.view_expenses)
        view_menu.addSeparator()
        view_menu.addAction("View Customers", self.view_customers)
        view_menu.addSeparator()
        view_menu.addAction("View Fuel Types", self.view_fuel_types)
        view_menu.addAction("View Tanks", self.view_tanks)
        view_menu.addAction("View Nozzles", self.view_nozzles)
        view_menu.addSeparator()
        #view_menu.addAction("View Exchange Rates", self.view_exchange_rates)
        view_menu.addAction("View Account Heads", self.view_account_heads)
        view_menu.addAction("Account Position Report", self.view_account_position_report)
        view_menu.addSeparator()
        view_menu.addAction("View Daily Summary", self.view_daily_summary)
        view_menu.addAction("Daily Transactions Report", self.daily_transactions_report)
        view_menu.addAction("View Inventory Report", self.view_inventory_report)
        
        # Transaction Menu
        daily_menu = menubar.addMenu("Transaction")
        daily_menu.addAction("Add Sales", self.record_sale_dialog)
        daily_menu.addAction("Add Purchase", self.record_purchase_dialog)
        daily_menu.addAction("Add Expense", self.record_expense_dialog)
        daily_menu.addSeparator()
        #daily_menu.addAction("Add New Customer", self.add_customer_dialog)
        daily_menu.addAction("Record Customer Payment", self.customer_payments_dialog)
        
        # Setup Menu (One-time settings)
        setup_menu = menubar.addMenu("Setup")
        setup_menu.addAction("Add Fuel Types", self.add_fuel_type_settings)
        setup_menu.addAction("Add Tanks", self.add_tank)
        setup_menu.addAction("Add Nozzles", self.add_nozzles_settings)
        setup_menu.addSeparator()
        setup_menu.addAction("Add Account Heads", self.add_account_heads)
        setup_menu.addSeparator()
        setup_menu.addAction("Configure System", self.configure_system)
        
        # Inventory Menu
        inventory_menu = menubar.addMenu("Inventory")
        inventory_menu.addAction("Update Stock Levels", self.update_stock_levels)
        inventory_menu.addSeparator()
        inventory_menu.addAction("Manage Nozzles", self.manage_nozzles)
        
        # Settings Menu
        settings_menu = menubar.addMenu("Settings")
        settings_menu.addAction("User Settings", self.user_settings)
        settings_menu.addAction("System Settings", self.system_settings)
        settings_menu.addSeparator()
        settings_menu.addAction("Backup Data", self.backup_data)

    def export_data(self):
        """Export data action."""
        QMessageBox.information(self, "Export", "Data export feature coming soon!")

    def record_sale_dialog(self):
        """Open dialog to record a sale."""
        # Get payment methods for Asset type (Cash, Bank, etc.)
        asset_payment_methods = self.account_head_service.get_payment_methods(head_type_filter='Asset')
        dialog = RecordSaleDialog(self.fuel_service, self.nozzle_service, self.sales_service, self.db_service, self.tank_service, self.account_head_service, asset_payment_methods)
        self._center_dialog_on_screen(dialog)
        if dialog.exec_() == QDialog.Accepted:
            QMessageBox.information(self, "Success", "Sale recorded successfully!")

    def record_purchase_dialog(self):
        """Open dialog to record a fuel purchase."""
        dialog = RecordPurchaseDialog(self.fuel_service, self.tank_service, self.db_service, self.account_head_service)
        if dialog.exec_() == QDialog.Accepted:
            QMessageBox.information(self, "Success", "Fuel purchase recorded successfully!")

    def update_exchange_rate_dialog(self):
        """Open dialog to update exchange rate."""
        dialog = UpdateExchangeRateDialog(self.db_service)
        if dialog.exec_() == QDialog.Accepted:
            QMessageBox.information(self, "Success", "Exchange rate updated successfully!")

    def record_expense_dialog(self):
        """Open dialog to record an expense."""
        # Get payment methods for Expense type
        expense_payment_methods = self.account_head_service.get_payment_methods(head_type_filter='Expense')
        dialog = RecordExpenseDialog(self.db_service, expense_payment_methods)
        if dialog.exec_() == QDialog.Accepted:
            QMessageBox.information(self, "Success", "Expense recorded successfully!")

    def add_customer_dialog(self):
        """Open dialog to add a new customer."""
        dialog = AddCustomerDialog(self.db_service)
        if dialog.exec_() == QDialog.Accepted:
            QMessageBox.information(self, "Success", "Customer added successfully!")

    def customer_payments_dialog(self):
        """Open dialog for customer payments."""
        QMessageBox.information(self, "Customer Payments", "Customer payments feature coming soon!")

    def view_daily_summary(self):
        """View daily summary."""
        QMessageBox.information(self, "Daily Summary", "Daily summary report coming soon!")

    def daily_transactions_report(self):
        """Daily transactions report with date filtering."""
        try:
            # Get all transactions
            sales = self.db_service.list_documents('sales')
            purchases = self.db_service.list_documents('purchases')
            expenses = self.db_service.list_documents('expenses')
            
            # Create dialog with date filtering
            dialog = DailyTransactionsReportDialog(
                self, 
                sales, 
                purchases, 
                expenses,
                self.nozzle_service,
                self.tank_service,
                self.fuel_service
            )
            self._center_dialog_on_screen(dialog)
            dialog.exec_()
            
        except Exception as e:
            logger.error(f"Error viewing daily transactions report: {str(e)}")
            QMessageBox.critical(self, "Error", f"Failed to load daily transactions report: {str(e)}")

    def _create_sales_table(self, sales_data):
        """Create sales transactions table."""
        table = QTableWidget()
        table.setColumnCount(11)
        table.setHorizontalHeaderLabels([
            "Nozzle", "Fuel Type", "Open Reading", "Quantity (L)", "Close Reading",
            "Unit Price (Rs)", "Total (Rs)", "Payment Method", "Customer", "Date", "Time"
        ])
        table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        table.setRowCount(len(sales_data))
        
        # Get lookup data
        nozzles = {n.id: f"M{n.machine_id}-N{n.nozzle_number}" for n in self.nozzle_service.list_nozzles()}
        fuels = {f.id: f.name for f in self.fuel_service.list_fuel_types()}
        
        for row, sale in enumerate(sales_data):
            nozzle_name = nozzles.get(sale.get('nozzle_id', ''), 'Unknown')
            fuel_name = fuels.get(sale.get('fuel_type_id', ''), 'Unknown')
            
            # Extract date and time
            date_str = sale.get('date', '')
            date_display = date_str[:10] if len(date_str) > 10 else ''
            time_str = date_str[11:19] if len(date_str) > 11 else ''
            
            items = [
                QTableWidgetItem(nozzle_name),
                QTableWidgetItem(fuel_name),
                QTableWidgetItem(f"{float(sale.get('opening_reading', 0)):,.2f}"),
                QTableWidgetItem(f"{float(sale.get('quantity', 0)):,.2f}"),
                QTableWidgetItem(f"{float(sale.get('closing_reading', 0)):,.2f}"),
                QTableWidgetItem(f"{float(sale.get('unit_price', 0)):,.2f}"),
                QTableWidgetItem(f"{float(sale.get('total_amount', 0)):,.2f}"),
                QTableWidgetItem(sale.get('payment_method', 'Cash')),
                QTableWidgetItem(sale.get('customer_name', 'Walk-in')),
                QTableWidgetItem(date_display),
                QTableWidgetItem(time_str)
            ]
            
            for col_idx, item in enumerate(items):
                item.setFlags(item.flags() & ~Qt.ItemIsEditable)
                table.setItem(row, col_idx, item)
        
        return table

    def _create_purchases_table(self, purchases_data):
        """Create purchases transactions table."""
        table = QTableWidget()
        table.setColumnCount(8)
        table.setHorizontalHeaderLabels([
            "Tank", "Fuel Type", "Quantity (L)", "Unit Cost (Rs)", 
            "Total Cost (Rs)", "Account Head", "Supplier", "Date"
        ])
        table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        table.setRowCount(len(purchases_data))
        
        # Get lookup data
        tanks = {t.id: {'name': t.name, 'fuel_type_id': t.fuel_type_id} for t in self.tank_service.list_tanks()}
        fuels = {f.id: f.name for f in self.fuel_service.list_fuel_types()}
        
        for row, purchase in enumerate(purchases_data):
            tank_id = purchase.get('tank_id', '')
            tank_info = tanks.get(tank_id, {})
            tank_name = tank_info.get('name', 'Unknown')
            
            # Get fuel type from tank's fuel_type_id
            tank_fuel_type_id = tank_info.get('fuel_type_id', '')
            fuel_name = fuels.get(tank_fuel_type_id, 'Unknown')
            
            date_str = purchase.get('purchase_date', purchase.get('date', ''))
            date_display = date_str[:10] if date_str else ''
            
            items = [
                QTableWidgetItem(tank_name),
                QTableWidgetItem(fuel_name),
                QTableWidgetItem(f"{float(purchase.get('quantity', 0)):,.2f}"),
                QTableWidgetItem(f"{float(purchase.get('unit_cost', 0)):,.2f}"),
                QTableWidgetItem(f"{float(purchase.get('total_cost', 0)):,.2f}"),
                QTableWidgetItem(purchase.get('account_head_name', '')),
                QTableWidgetItem(purchase.get('supplier_name', 'Unknown')),
                QTableWidgetItem(date_display)
            ]
            
            for col_idx, item in enumerate(items):
                item.setFlags(item.flags() & ~Qt.ItemIsEditable)
                table.setItem(row, col_idx, item)
        
        return table

    def _create_expenses_table(self, expenses_data):
        """Create expenses transactions table."""
        table = QTableWidget()
        table.setColumnCount(6)
        table.setHorizontalHeaderLabels([
            "Description", "Category", "Amount (Rs)", "Payment Method", "Notes", "Date"
        ])
        table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        table.setRowCount(len(expenses_data))
        
        for row, expense in enumerate(expenses_data):
            date_str = expense.get('expense_date', expense.get('date', ''))
            date_display = date_str[:10] if date_str else ''
            
            items = [
                QTableWidgetItem(expense.get('description', '')),
                QTableWidgetItem(expense.get('category', '')),
                QTableWidgetItem(f"{float(expense.get('amount', 0)):,.2f}"),
                QTableWidgetItem(expense.get('payment_method', 'Cash')),
                QTableWidgetItem(expense.get('notes', '')),
                QTableWidgetItem(date_display)
            ]
            
            for col_idx, item in enumerate(items):
                item.setFlags(item.flags() & ~Qt.ItemIsEditable)
                table.setItem(row, col_idx, item)
        
        return table

    def view_sales_records(self):
        """View sales records."""
        try:
            sales_data = self.db_service.list_documents('sales')
            # Build lookup maps for nozzle names and fuel types
            nozzles = self.nozzle_service.list_nozzles()
            nozzle_map = {n.id: f"Machine {n.machine_id} - Nozzle {n.nozzle_number}" for n in nozzles}
            fuel_types = self.fuel_service.list_fuel_types()
            fuel_map = {f.id: f.name for f in fuel_types}
            # Build account head map
            account_heads = self.db_service.list_documents('account_heads')
            account_head_map = {a.get('id'): a.get('name', '') for a in account_heads}
            
            columns = ["Date", "Nozzle", "Fuel Type", "Opening (L)", "Quantity (L)", "Closing (L)", "Unit Price (Rs)", "Total (Rs)", "Account Head"]
            data = []
            
            for sale in sales_data:
                nozzle_id = sale.get('nozzle_id', '')
                nozzle_name = nozzle_map.get(nozzle_id, nozzle_id)
                fuel_type_id = sale.get('fuel_type_id', '')
                fuel_name = fuel_map.get(fuel_type_id, sale.get('fuel_type', ''))
                # Get account head name from map
                account_head_id = sale.get('account_head_id', '')
                account_head_name = account_head_map.get(account_head_id, sale.get('account_head_name', ''))
                
                # Extract date
                date_str = sale.get('date', sale.get('timestamp', sale.get('created_at', '')))[:10] if sale.get('date') or sale.get('timestamp') or sale.get('created_at') else ''
                
                data.append([
                    date_str,
                    nozzle_name,
                    fuel_name,
                    f"{sale.get('opening_reading', 0):.2f}",
                    f"{sale.get('quantity', 0):.2f}",
                    f"{sale.get('closing_reading', 0):.2f}",
                    f"{sale.get('unit_price', sale.get('price', 0)):.2f}",
                    f"{sale.get('total_amount', 0):.2f}",
                    account_head_name
                ])
            
            if not data:
                data = [["No sales records found", "", "", "", "", "", "", "", ""]]
            
            dialog = DataViewDialog("Sales Records", columns, data, self, date_field='date', raw_data=sales_data)
            dialog.exec_()
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Failed to load sales: {str(e)}")

    def view_purchase_records(self):
        """View purchase records."""
        try:
            purchases_data = self.db_service.list_documents('purchases')
            # Build lookup map for tank names
            tanks = self.tank_service.list_tanks()
            tank_map = {t.id: t.name for t in tanks}
            
            columns = ["Date", "Tank", "Supplier", "Quantity (L)", "Unit Cost", "Total (Rs)", "Invoice"]
            data = []
            
            for purchase in purchases_data:
                tank_id = purchase.get('tank_id', '')
                tank_name = tank_map.get(tank_id, tank_id)
                # Get date from 'purchase_date' or 'timestamp' field
                date_str = purchase.get('purchase_date', purchase.get('timestamp', purchase.get('created_at', '')))[:10] if purchase.get('purchase_date') or purchase.get('timestamp') or purchase.get('created_at') else ''
                data.append([
                    date_str,
                    tank_name,
                    purchase.get('supplier_name', ''),
                    f"{purchase.get('quantity', 0):.2f}",
                    f"{purchase.get('unit_cost', 0):.2f}",
                    f"{purchase.get('total_cost', 0):.2f}",
                    purchase.get('invoice_number', '')
                ])
            
            if not data:
                data = [["No purchase records found", "", "", "", "", "", ""]]
            
            dialog = DataViewDialog("Purchase Records", columns, data, self, date_field='purchase_date', raw_data=purchases_data)
            dialog.exec_()
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Failed to load purchases: {str(e)}")

    def view_customers(self):
        """View customers."""
        try:
            customers_data = self.db_service.list_documents('customers')
            columns = ["Name", "Phone", "Email", "Address", "Credit Limit (Rs)", "Type", "Created Date"]
            data = []
            
            for customer in customers_data:
                created_date = customer.get('created_at', '')[:10] if customer.get('created_at') else ''
                data.append([
                    customer.get('name', ''),
                    customer.get('phone', ''),
                    customer.get('email', ''),
                    customer.get('address', ''),
                    f"{customer.get('credit_limit', 0):.2f}",
                    customer.get('customer_type', ''),
                    created_date
                ])
            
            if not data:
                data = [["No customers found", "", "", "", "", "", ""]]
            
            dialog = DataViewDialog("Customers", columns, data, self, date_field='created_at', raw_data=customers_data)
            dialog.exec_()
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Failed to load customers: {str(e)}")

    def view_expenses(self):
        """View expenses."""
        try:
            expenses_data = self.db_service.list_documents('expenses')
            columns = ["Date", "Category", "Description", "Amount (Rs)", "Payment Method", "Reference"]
            data = []
            
            for expense in expenses_data:
                # Get date from 'expense_date' or 'timestamp' field
                date_str = expense.get('expense_date', expense.get('timestamp', expense.get('created_at', '')))[:10] if expense.get('expense_date') or expense.get('timestamp') or expense.get('created_at') else ''
                data.append([
                    date_str,
                    expense.get('category', ''),
                    expense.get('description', ''),
                    f"{expense.get('amount', 0):.2f}",
                    expense.get('payment_method', ''),
                    expense.get('reference_number', '')
                ])
            
            if not data:
                data = [["No expenses found", "", "", "", "", ""]]
            
            dialog = DataViewDialog("Expenses", columns, data, self, date_field='expense_date', raw_data=expenses_data)
            dialog.exec_()
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Failed to load expenses: {str(e)}")

    def view_fuel_types(self):
        """View fuel types."""
        try:
            fuel_types = self.fuel_service.list_fuel_types()
            columns = ["Name", "Unit Price (Rs)", "Tax %"]
            data = []
            
            for fuel in fuel_types:
                data.append([
                    fuel.name,
                    f"{float(fuel.unit_price):.2f}",
                    f"{float(fuel.tax_percentage):.2f}"
                ])
            
            if not data:
                data = [["No fuel types found", "", ""]]
            
            dialog = DataViewDialog("Fuel Types", columns, data, self)
            dialog.exec_()
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Failed to load fuel types: {str(e)}")

    def view_tanks(self):
        """View tanks."""
        try:
            tanks = self.tank_service.list_tanks()
            # Build lookup map for fuel type names
            fuel_types = self.fuel_service.list_fuel_types()
            fuel_map = {f.id: f.name for f in fuel_types}
            
            columns = ["Name", "Fuel Type", "Capacity (L)", "Min Stock (L)", "Location"]
            data = []
            
            for tank in tanks:
                fuel_name = fuel_map.get(tank.fuel_type_id, tank.fuel_type_id)
                data.append([
                    tank.name,
                    fuel_name,
                    f"{float(tank.capacity):.0f}",
                    f"{float(tank.minimum_stock):.0f}",
                    tank.location
                ])
            
            if not data:
                data = [["No tanks found", "", "", "", ""]]
            
            dialog = DataViewDialog("Tanks", columns, data, self)
            dialog.exec_()
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Failed to load tanks: {str(e)}")

    def view_nozzles(self):
        """View nozzles."""
        try:
            nozzles = self.nozzle_service.list_nozzles()
            # Build lookup map for fuel type names
            fuel_types = self.fuel_service.list_fuel_types()
            fuel_map = {f.id: f.name for f in fuel_types}
            
            columns = ["Machine ID", "Nozzle Number", "Fuel Type", "Opening Reading"]
            data = []
            
            for nozzle in nozzles:
                fuel_name = fuel_map.get(nozzle.fuel_type_id, nozzle.fuel_type_id)
                data.append([
                    nozzle.machine_id,
                    str(nozzle.nozzle_number),
                    fuel_name,
                    f"{float(nozzle.opening_reading):.2f}"
                ])
            
            if not data:
                data = [["No nozzles found", "", "", ""]]
            
            dialog = DataViewDialog("Nozzles", columns, data, self)
            dialog.exec_()
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Failed to load nozzles: {str(e)}")

    def view_exchange_rates(self):
        """View exchange rates."""
        try:
            rates_data = self.db_service.list_documents('exchange_rates')
            columns = ["From Currency", "To Currency", "Rate", "Effective Date"]
            data = []
            
            for rate in rates_data:
                data.append([
                    rate.get('from_currency', ''),
                    rate.get('to_currency', ''),
                    f"{rate.get('rate', 0):.4f}",
                    rate.get('effective_date', '')
                ])
            
            if not data:
                data = [["No exchange rates found", "", "", ""]]
            
            dialog = DataViewDialog("Exchange Rates", columns, data, self)
            dialog.exec_()
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Failed to load exchange rates: {str(e)}")

    def view_account_heads(self):
        """View account heads."""
        try:
            accounts = self.db_service.list_documents('account_heads')
            columns = ["Name", "Type", "Code", "Description", "Created Date"]
            data = []
            
            for account in accounts:
                account_type = account.get('account_type', '') or account.get('head_type', '')
                created_date = account.get('created_at', '')[:10] if account.get('created_at') else ''
                data.append([
                    account.get('name', ''),
                    account_type,
                    account.get('code', ''),
                    account.get('description', ''),
                    created_date
                ])
            
            if not data:
                data = [["No account heads found", "", "", "", ""]]
            
            dialog = DataViewDialog("Account Heads", columns, data, self, date_field='created_at', raw_data=accounts)
            dialog.exec_()
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Failed to load account heads: {str(e)}")

    def view_account_position_report(self):
        """View account position report showing outstanding balance of all account heads with real-time impact from transactions.
        
        Transaction Impact Logic:
        - Sales: CREDIT (positive impact - cash received)
        - Purchases: DEBIT (negative impact - cash paid out)
        - Expenses: DEBIT (negative impact - cash paid out)
        """
        try:
            # Get all account heads
            accounts = self.db_service.list_documents('account_heads')
            
            if not accounts:
                QMessageBox.information(self, "Account Position Report", "No account heads found.")
                return
            
            # Get all transactions
            sales = self.db_service.list_documents('sales')
            expenses = self.db_service.list_documents('expenses')
            purchases = self.db_service.list_documents('purchases')
            
            # Create a map of account ID to transaction impact
            account_impacts = {}
            for account in accounts:
                account_id = account.get('id', '')
                account_name = account.get('name', '')
                account_type = account.get('head_type', account.get('account_type', ''))
                account_impacts[account_id] = {
                    'impact': 0.0,
                    'type': account_type,
                    'name': account_name
                }
            
            # Calculate impacts based on account head ID and transaction type
            # CREDIT: Sales - cash received (positive impact)
            for sale in sales:
                account_head_id = sale.get('account_head_id', '')
                amount = float(sale.get('total_amount', 0))
                if account_head_id in account_impacts:
                    account_impacts[account_head_id]['impact'] += amount  # CREDIT: add to account
            
            # DEBIT: Expenses - cash paid out (negative impact)
            for expense in expenses:
                account_head_id = expense.get('account_head_id', '')
                amount = float(expense.get('amount', 0))
                if account_head_id in account_impacts:
                    account_impacts[account_head_id]['impact'] -= amount  # DEBIT: subtract from account
            
            # DEBIT: Purchases - cash paid out (negative impact)
            for purchase in purchases:
                account_head_id = purchase.get('account_head_id', '')
                amount = float(purchase.get('total_cost', 0))
                if account_head_id in account_impacts:
                    account_impacts[account_head_id]['impact'] -= amount  # DEBIT: subtract from account
            
            # Create dialog
            dialog = QDialog(self)
            dialog.setWindowTitle("Account Position Report - Real Time")
            dialog.setGeometry(100, 100, 1200, 650)
            self._center_dialog_on_screen(dialog)
            
            layout = QVBoxLayout()
            
            # Header
            header = QLabel("Account Position Report - Real Time Impact")
            header.setFont(QFont("Arial", 16, QFont.Bold))
            layout.addWidget(header)
            
            # Subtitle with date
            from datetime import date
            today = date.today()
            subtitle = QLabel(f"As on {today.strftime('%d-%b-%Y')} | Updated in Real Time")
            subtitle.setFont(QFont("Arial", 10))
            subtitle.setStyleSheet("color: #666;")
            layout.addWidget(subtitle)
            
            # Create table
            table = QTableWidget()
            table.setColumnCount(6)
            table.setHorizontalHeaderLabels([
                "Account Head", "Code", "Type", "Opening Balance (Rs)", "Transaction Impact (Rs)", "Outstanding Position (Rs)"
            ])
            table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
            table.setRowCount(len(accounts))
            
            total_opening = 0.0
            total_impact = 0.0
            total_outstanding = 0.0
            
            for row, account in enumerate(accounts):
                account_id = account.get('id', '')
                name = account.get('name', '')
                code = account.get('code', '')
                head_type = account.get('head_type', account.get('account_type', ''))
                opening_balance = float(account.get('opening_balance', 0))
                
                # Get transaction impact for this account head using account ID
                impact_data = account_impacts.get(account_id, {'impact': 0.0, 'type': ''})
                transaction_impact = impact_data['impact']
                
                # Outstanding = Opening Balance + Transaction Impact
                outstanding = opening_balance + transaction_impact
                
                total_opening += opening_balance
                total_impact += transaction_impact
                total_outstanding += outstanding
                
                items = [
                    QTableWidgetItem(name),
                    QTableWidgetItem(code),
                    QTableWidgetItem(head_type),
                    QTableWidgetItem(f"{opening_balance:,.2f}"),
                    QTableWidgetItem(f"{transaction_impact:,.2f}"),
                    QTableWidgetItem(f"{outstanding:,.2f}")
                ]
                for col_idx, item in enumerate(items):
                    item.setFlags(item.flags() & ~Qt.ItemIsEditable)
                    table.setItem(row, col_idx, item)
                
                # Color code the transaction impact (CREDIT = green, DEBIT = red)
                if transaction_impact > 0:
                    table.item(row, 4).setBackground(QColor("#C8E6C9"))  # Green for CREDIT (positive)
                elif transaction_impact < 0:
                    table.item(row, 4).setBackground(QColor("#FFCDD2"))  # Red for DEBIT (negative)
            
            layout.addWidget(table)
            
            # Summary section
            summary_layout = QHBoxLayout()
            summary_layout.addStretch()
            
            # Summary in boxes
            summary_box = QFrame()
            summary_box_layout = QHBoxLayout(summary_box)
            
            opening_label = QLabel(f"Total Opening: Rs. {total_opening:,.2f}")
            opening_label.setFont(QFont("Arial", 11, QFont.Bold))
            opening_label.setStyleSheet("padding: 8px; background-color: #E3F2FD; border-radius: 5px;")
            summary_box_layout.addWidget(opening_label)
            
            impact_label = QLabel(f"Total Transaction Impact: Rs. {total_impact:,.2f}")
            impact_label.setFont(QFont("Arial", 11, QFont.Bold))
            impact_label.setStyleSheet("padding: 8px; background-color: #C8E6C9; border-radius: 5px; color: #2E7D32;")
            summary_box_layout.addWidget(impact_label)
            
            outstanding_label = QLabel(f"Total Outstanding: Rs. {total_outstanding:,.2f}")
            outstanding_label.setFont(QFont("Arial", 11, QFont.Bold))
            outstanding_label.setStyleSheet("padding: 8px; background-color: #BBDEFB; border-radius: 5px; color: #1565C0;")
            summary_box_layout.addWidget(outstanding_label)
            
            summary_layout.addWidget(summary_box)
            summary_layout.addStretch()
            layout.addLayout(summary_layout)
            
            # Buttons
            button_layout = QHBoxLayout()
            pdf_btn = QPushButton("📄 Export to PDF")
            pdf_btn.clicked.connect(lambda: self._export_account_position_to_pdf(accounts, account_impacts))
            button_layout.addWidget(pdf_btn)
            button_layout.addStretch()
            close_btn = QPushButton("Close")
            close_btn.clicked.connect(dialog.accept)
            button_layout.addWidget(close_btn)
            layout.addLayout(button_layout)
            
            dialog.setLayout(layout)
            dialog.exec_()
            
            
        except Exception as e:
            logger.error(f"Error viewing account position report: {str(e)}")
            QMessageBox.critical(self, "Error", f"Failed to load account position report: {str(e)}")

    def _export_account_position_to_pdf(self, accounts, account_impacts):
        """Export account position report to PDF with real-time transaction impact."""
        try:
            from PyQt5.QtWidgets import QFileDialog
            from datetime import date
            
            # Get file path from user
            file_path, _ = QFileDialog.getSaveFileName(
                self,
                "Export Account Position Report to PDF",
                f"Account_Position_Report_{date.today().isoformat().replace('-', '')}.pdf",
                "PDF Files (*.pdf)"
            )
            
            if not file_path:
                return
            
            try:
                from reportlab.lib import colors
                from reportlab.lib.pagesizes import letter, A4
                from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
                from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
                from reportlab.lib.units import inch
                
                # Create PDF document
                doc = SimpleDocTemplate(file_path, pagesize=letter, topMargin=0.5*inch, bottomMargin=0.5*inch)
                elements = []
                
                # Title
                styles = getSampleStyleSheet()
                title_style = ParagraphStyle(
                    'CustomTitle',
                    parent=styles['Heading1'],
                    fontSize=18,
                    textColor=colors.HexColor('#1565C0'),
                    spaceAfter=12,
                    alignment=1  # Center
                )
                elements.append(Paragraph("Account Position Report", title_style))
                elements.append(Paragraph(f"As on {date.today().strftime('%d-%b-%Y')}", styles['Normal']))
                elements.append(Spacer(1, 0.3*inch))
                
                # Account positions table with real-time transaction impact
                account_data = [['Account Head', 'Code', 'Type', 'Opening Balance (Rs)', 'Transaction Impact (Rs)', 'Outstanding Position (Rs)']]
                total_opening = 0.0
                total_transaction_impact = 0.0
                total_outstanding = 0.0
                
                for account in accounts:
                    account_id = account.get('id', '')
                    name = account.get('name', '')
                    code = account.get('code', '')
                    head_type = account.get('head_type', account.get('account_type', ''))
                    opening_balance = float(account.get('opening_balance', 0))
                    
                    # Get transaction impact for this account head using account ID
                    impact_data = account_impacts.get(account_id, {})
                    transaction_impact = impact_data.get('impact', 0.0) if isinstance(impact_data, dict) else 0.0
                    
                    # Outstanding = Opening Balance + Transaction Impact
                    outstanding = opening_balance + transaction_impact
                    
                    total_opening += opening_balance
                    total_transaction_impact += transaction_impact
                    total_outstanding += outstanding
                    
                    account_data.append([
                        name,
                        code,
                        head_type,
                        f"{opening_balance:,.2f}",
                        f"{transaction_impact:,.2f}",
                        f"{outstanding:,.2f}"
                    ])
                
                # Add total row
                account_data.append([
                    '',
                    '',
                    'TOTAL',
                    f"{total_opening:,.2f}",
                    f"{total_transaction_impact:,.2f}",
                    f"{total_outstanding:,.2f}"
                ])
                
                account_table = Table(account_data, colWidths=[1.6*inch, 0.9*inch, 1*inch, 1.2*inch, 1.2*inch, 1.4*inch])
                account_table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1565C0')),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                    ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                    ('ALIGN', (3, 0), (-1, -1), 'RIGHT'),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, 0), 10),
                    ('FONTSIZE', (0, 1), (-1, -1), 9),
                    ('TOPPADDING', (0, 0), (-1, -1), 5),
                    ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
                    ('ROWBACKGROUNDS', (0, 1), (-1, -2), [colors.white, colors.HexColor('#E3F2FD')]),
                    ('BACKGROUND', (0, -1), (-1, -1), colors.HexColor('#BBDEFB')),
                    ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
                    ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#BDBDBD'))
                ]))
                elements.append(account_table)
                
                # Build PDF
                doc.build(elements)
                QMessageBox.information(self, "Success", f"Account position report exported successfully to:\n{file_path}")
                
            except ImportError:
                QMessageBox.warning(self, "Missing Library", "reportlab is not installed. Please install it to export to PDF.\n\nRun: pip install reportlab")
        except Exception as e:
            logger.error(f"Error exporting account position to PDF: {str(e)}")
            QMessageBox.critical(self, "Error", f"Failed to export PDF: {str(e)}")

    def manage_credit_accounts(self):
        """Manage credit accounts."""
        QMessageBox.information(self, "Credit Accounts", "Credit accounts management coming soon!")

    def configure_system(self):
        """Configure system settings."""
        QMessageBox.information(self, "Configuration", "System configuration coming soon!")

    def user_settings(self):
        """User settings."""
        QMessageBox.information(self, "User Settings", "User settings coming soon!")

    def system_settings(self):
        """System settings."""
        QMessageBox.information(self, "System Settings", "System settings coming soon!")

    def backup_data(self):
        """Backup data."""
        QMessageBox.information(self, "Backup", "Data backup coming soon!")

    def add_fuel_type(self):
        """Add new fuel type."""
        print("Add Fuel Type clicked")

    def add_tank(self):
        """Add new tank."""
        dialog = AddTankDialog(self.tank_service, self.fuel_service)
        if dialog.exec_() == QDialog.Accepted:
            QMessageBox.information(self, "Success", "Tank added successfully!")

    def update_stock_levels(self):
        """Update stock levels."""
        dialog = UpdateStockLevelDialog(self.tank_service, self.fuel_service, self.db_service, self)
        dialog.exec_()

    def view_inventory_report(self):
        """View inventory report."""
        try:
            # Get all tanks
            tanks = self.tank_service.list_tanks()
            
            if not tanks:
                QMessageBox.information(self, "Inventory Report", "No tanks found in the system.")
                return
            
            # Get fuel types
            fuel_types = self.fuel_service.list_fuel_types()
            fuel_dict = {f.id: f.name for f in fuel_types}
            
            # Create dialog to display inventory report
            dialog = QDialog(self)
            dialog.setWindowTitle("Inventory Report")
            dialog.setGeometry(100, 100, 1000, 600)
            self._center_dialog_on_screen(dialog)
            
            layout = QVBoxLayout()
            
            # Header
            header = QLabel("Tank Inventory Report")
            header.setFont(QFont("Arial", 16, QFont.Bold))
            layout.addWidget(header)
            
            # Summary stats
            summary_layout = QHBoxLayout()
            total_capacity = sum(t.capacity for t in tanks)
            total_stock = sum(t.current_stock for t in tanks)
            avg_stock_pct = (total_stock / total_capacity * 100) if total_capacity > 0 else 0
            
            summary_layout.addWidget(self.create_stat_card("Total Capacity", f"{total_capacity:,.2f} L", "#2196F3"))
            summary_layout.addWidget(self.create_stat_card("Total Stock", f"{total_stock:,.2f} L", "#4CAF50"))
            summary_layout.addWidget(self.create_stat_card("Average Stock %", f"{avg_stock_pct:.1f}%", "#FF9800"))
            layout.addLayout(summary_layout)
            
            # Create table
            table = QTableWidget()
            table.setColumnCount(7)
            table.setHorizontalHeaderLabels([
                "Tank Name", "Fuel Type", "Capacity (L)", "Current Stock (L)", 
                "Minimum Stock (L)", "Stock %", "Status"
            ])
            table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
            
            table.setRowCount(len(tanks))
            
            for row, tank in enumerate(tanks):
                fuel_name = fuel_dict.get(tank.fuel_type_id, "Unknown")
                stock_pct = (tank.current_stock / tank.capacity * 100) if tank.capacity > 0 else 0
                
                # Determine status
                if tank.current_stock < tank.minimum_stock:
                    status = "⚠ Low Stock"
                    status_color = QColor("red")
                elif stock_pct < 25:
                    status = "⚠ Critical"
                    status_color = QColor("orange")
                elif stock_pct > 90:
                    status = "✓ Full"
                    status_color = QColor("green")
                else:
                    status = "✓ Normal"
                    status_color = QColor("green")
                
                # Tank Name
                name_item = QTableWidgetItem(tank.name)
                name_item.setFlags(name_item.flags() & ~Qt.ItemIsEditable)
                table.setItem(row, 0, name_item)
                
                # Fuel Type
                fuel_item = QTableWidgetItem(fuel_name)
                fuel_item.setFlags(fuel_item.flags() & ~Qt.ItemIsEditable)
                table.setItem(row, 1, fuel_item)
                
                # Capacity
                capacity_item = QTableWidgetItem(f"{tank.capacity:,.2f}")
                capacity_item.setFlags(capacity_item.flags() & ~Qt.ItemIsEditable)
                table.setItem(row, 2, capacity_item)
                
                # Current Stock
                stock_item = QTableWidgetItem(f"{tank.current_stock:,.2f}")
                stock_item.setFlags(stock_item.flags() & ~Qt.ItemIsEditable)
                table.setItem(row, 3, stock_item)
                
                # Minimum Stock
                min_stock_item = QTableWidgetItem(f"{tank.minimum_stock:,.2f}")
                min_stock_item.setFlags(min_stock_item.flags() & ~Qt.ItemIsEditable)
                table.setItem(row, 4, min_stock_item)
                
                # Stock Percentage
                pct_item = QTableWidgetItem(f"{stock_pct:.1f}%")
                pct_item.setFlags(pct_item.flags() & ~Qt.ItemIsEditable)
                table.setItem(row, 5, pct_item)
                
                # Status
                status_item = QTableWidgetItem(status)
                status_item.setFlags(status_item.flags() & ~Qt.ItemIsEditable)
                status_item.setForeground(status_color)
                status_item.setFont(QFont("Arial", 10, QFont.Bold))
                table.setItem(row, 6, status_item)
            
            layout.addWidget(table)
            
            # Export and Close buttons
            button_layout = QHBoxLayout()
            pdf_btn = QPushButton("📄 Export to PDF")
            pdf_btn.clicked.connect(lambda: self._export_inventory_to_pdf(tanks, fuel_dict))
            button_layout.addWidget(pdf_btn)
            button_layout.addStretch()
            close_btn = QPushButton("Close")
            close_btn.clicked.connect(dialog.accept)
            button_layout.addWidget(close_btn)
            
            layout.addLayout(button_layout)
            dialog.setLayout(layout)
            dialog.exec_()
            
        except Exception as e:
            logger.error(f"Error viewing inventory report: {str(e)}")
            QMessageBox.critical(self, "Error", f"Failed to load inventory report: {str(e)}")

    def create_stat_card(self, label: str, value: str, color: str) -> QWidget:
        """Create a stat card widget."""
        card = QFrame()
        card.setStyleSheet(f"background-color: {color}; border-radius: 5px; padding: 10px;")
        layout = QVBoxLayout(card)
        
        label_widget = QLabel(label)
        label_widget.setStyleSheet("color: white; font-size: 11px;")
        layout.addWidget(label_widget)
        
        value_widget = QLabel(value)
        value_widget.setStyleSheet("color: white; font-size: 14px; font-weight: bold;")
        layout.addWidget(value_widget)
        
        return card

    def _center_dialog_on_screen(self, dialog):
        """Center dialog on screen."""
        from PyQt5.QtWidgets import QDesktopWidget
        screen = QDesktopWidget().screenGeometry()
        size = dialog.geometry()
        dialog.move((screen.width() - size.width()) // 2, (screen.height() - size.height()) // 2)

    def _export_inventory_to_pdf(self, tanks, fuel_dict):
        """Export inventory report to PDF."""
        try:
            file_path, _ = QFileDialog.getSaveFileName(
                self,
                "Export Inventory Report to PDF",
                f"Inventory_Report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf",
                "PDF Files (*.pdf)"
            )
            
            if not file_path:
                return
            
            # Create PDF
            try:
                from reportlab.lib import colors
                from reportlab.lib.pagesizes import letter
                from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
                from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
                from reportlab.lib.units import inch
                
                # Create PDF document
                doc = SimpleDocTemplate(file_path, pagesize=letter, topMargin=0.75*inch, bottomMargin=0.75*inch)
                elements = []
                
                # Styles
                styles = getSampleStyleSheet()
                title_style = ParagraphStyle(
                    'CustomTitle',
                    parent=styles['Heading1'],
                    fontSize=20,
                    textColor=colors.HexColor('#1565C0'),
                    spaceAfter=6,
                    alignment=1,
                    fontName='Helvetica-Bold'
                )
                
                heading_style = ParagraphStyle(
                    'CustomHeading',
                    parent=styles['Heading2'],
                    fontSize=12,
                    textColor=colors.HexColor('#1565C0'),
                    spaceAfter=8,
                    spaceBefore=8,
                    fontName='Helvetica-Bold'
                )
                
                # Title
                elements.append(Paragraph("TANK INVENTORY REPORT", title_style))
                elements.append(Paragraph(f"Generated: {datetime.now().strftime('%B %d, %Y at %H:%M:%S')}", styles['Normal']))
                elements.append(Spacer(1, 0.25*inch))
                
                # Summary stats
                total_capacity = sum(t.capacity for t in tanks)
                total_stock = sum(t.current_stock for t in tanks)
                avg_stock_pct = (total_stock / total_capacity * 100) if total_capacity > 0 else 0
                
                summary_data = [
                    ['Metric', 'Value'],
                    ['Total Capacity', f'{total_capacity:,.2f} L'],
                    ['Total Current Stock', f'{total_stock:,.2f} L'],
                    ['Average Stock Level', f'{avg_stock_pct:.1f}%']
                ]
                
                summary_table = Table(summary_data, colWidths=[2.5*inch, 2.5*inch])
                summary_table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1565C0')),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, 0), 11),
                    ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                    ('TOPPADDING', (0, 0), (-1, 0), 8),
                    ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#E3F2FD')),
                    ('TEXTCOLOR', (0, 1), (-1, -1), colors.HexColor('#0D47A1')),
                    ('FONTNAME', (0, 1), (0, -1), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 1), (-1, -1), 10),
                    ('GRID', (0, 0), (-1, -1), 1.5, colors.HexColor('#1565C0')),
                    ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.HexColor('#FFFFFF'), colors.HexColor('#E3F2FD')]),
                    ('LEFTPADDING', (0, 0), (-1, -1), 10),
                    ('RIGHTPADDING', (0, 0), (-1, -1), 10),
                    ('VALIGN', (0, 0), (-1, -1), 'MIDDLE')
                ]))
                elements.append(summary_table)
                elements.append(Spacer(1, 0.3*inch))
                
                # Inventory table
                elements.append(Paragraph("TANK INVENTORY DETAILS", heading_style))
                
                data = [['Tank Name', 'Fuel Type', 'Capacity\n(L)', 'Current Stock\n(L)', 'Min Stock\n(L)', 'Stock %', 'Status']]
                
                for tank in tanks:
                    fuel_name = fuel_dict.get(tank.fuel_type_id, "Unknown")
                    stock_pct = (tank.current_stock / tank.capacity * 100) if tank.capacity > 0 else 0
                    
                    if tank.current_stock < tank.minimum_stock:
                        status = "Low Stock"
                    elif stock_pct < 25:
                        status = "Critical"
                    elif stock_pct > 90:
                        status = "Full"
                    else:
                        status = "Normal"
                    
                    data.append([
                        tank.name,
                        fuel_name,
                        f'{tank.capacity:,.0f}',
                        f'{tank.current_stock:,.0f}',
                        f'{tank.minimum_stock:,.0f}',
                        f'{stock_pct:.1f}%',
                        status
                    ])
                
                table = Table(data, colWidths=[1.1*inch, 1*inch, 0.9*inch, 1*inch, 0.9*inch, 0.8*inch, 0.8*inch])
                table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1565C0')),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, 0), 9),
                    ('TOPPADDING', (0, 0), (-1, 0), 8),
                    ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
                    ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#90CAF9')),
                    ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.HexColor('#FFFFFF'), colors.HexColor('#E3F2FD')]),
                    ('FONTSIZE', (0, 1), (-1, -1), 8),
                    ('LEFTPADDING', (0, 0), (-1, -1), 6),
                    ('RIGHTPADDING', (0, 0), (-1, -1), 6),
                    ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                    ('TOPPADDING', (0, 1), (-1, -1), 6),
                    ('BOTTOMPADDING', (0, 1), (-1, -1), 6)
                ]))
                elements.append(table)
                
                # Build PDF
                doc.build(elements)
                QMessageBox.information(self, "Success", f"Inventory report exported successfully to:\n{file_path}")
                
            except ImportError:
                QMessageBox.warning(self, "Missing Library", "reportlab is not installed. Please install it to export to PDF.\n\nRun: pip install reportlab")
        except Exception as e:
            logger.error(f"Error exporting inventory to PDF: {str(e)}")
            QMessageBox.critical(self, "Error", f"Failed to export PDF: {str(e)}")

    def _export_transactions_to_pdf(self, today, total_sales, total_sale_qty, total_purchases, total_expenses, net_profit, today_sales, today_purchases, today_expenses):
        """Export daily transactions report to PDF."""
        try:
            from PyQt5.QtWidgets import QFileDialog
            from PyQt5.QtCore import QDateTime
            
            # Get file path from user
            file_path, _ = QFileDialog.getSaveFileName(
                self,
                "Export Daily Transactions Report to PDF",
                f"Daily_Transactions_{today.replace('-', '')}.pdf",
                "PDF Files (*.pdf)"
            )
            
            if not file_path:
                return
            
            # Create PDF
            try:
                from reportlab.lib import colors
                from reportlab.lib.pagesizes import letter, A4
                from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak
                from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
                from reportlab.lib.units import inch
                from datetime import datetime
                
                # Create PDF document
                doc = SimpleDocTemplate(file_path, pagesize=letter, topMargin=0.5*inch, bottomMargin=0.5*inch)
                elements = []
                
                # Title
                styles = getSampleStyleSheet()
                title_style = ParagraphStyle(
                    'CustomTitle',
                    parent=styles['Heading1'],
                    fontSize=18,
                    textColor=colors.HexColor('#1565C0'),
                    spaceAfter=12,
                    alignment=1  # Center
                )
                elements.append(Paragraph("Daily Transactions Report", title_style))
                elements.append(Paragraph(f"Date: {today}", styles['Normal']))
                elements.append(Spacer(1, 0.2*inch))
                
                # Summary stats with professional formatting
                summary_data = [
                    ['Metric', 'Value'],
                    ['Total Sales', f'Rs. {total_sales:,.2f}'],
                    ['Fuel Sold', f'{total_sale_qty:,.2f} L'],
                    ['Total Purchases', f'Rs. {total_purchases:,.2f}'],
                    ['Total Expenses', f'Rs. {total_expenses:,.2f}'],
                    ['Net Profit', f'Rs. {net_profit:,.2f}']
                ]
                
                summary_table = Table(summary_data, colWidths=[3*inch, 2*inch])
                summary_table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1565C0')),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                    ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                    ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, 0), 11),
                    ('FONTSIZE', (0, 1), (-1, -1), 10),
                    ('TOPPADDING', (0, 0), (-1, -1), 6),
                    ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
                    ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#E3F2FD')]),
                    ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#BDBDBD'))
                ]))
                elements.append(summary_table)
                elements.append(Spacer(1, 0.3*inch))
                
                # Sales section
                if today_sales:
                    sales_heading_style = ParagraphStyle(
                        'SalesHeading',
                        parent=styles['Heading2'],
                        fontSize=12,
                        textColor=colors.HexColor('#388E3C'),
                        spaceAfter=8
                    )
                    elements.append(Paragraph(f"Sales ({len(today_sales)} transactions)", sales_heading_style))
                    
                    # Build nozzle lookup
                    nozzles = {n.id: f"M{n.machine_id}-N{n.nozzle_number}" for n in self.nozzle_service.list_nozzles()}
                    fuels = {f.id: f.name for f in self.fuel_service.list_fuel_types()}
                    
                    sales_data = [['Nozzle', 'Fuel Type', 'Open Read', 'Qty (L)', 'Close Read', 'Unit Price', 'Total (Rs)', 'Date', 'Time']]
                    for sale in today_sales:
                        nozzle_name = nozzles.get(sale.get('nozzle_id', ''), 'Unknown')
                        fuel_name = fuels.get(sale.get('fuel_type_id', ''), 'Unknown')
                        
                        # Extract date and time
                        date_str = sale.get('date', '')
                        date_display = date_str[:10] if len(date_str) > 10 else ''
                        time_display = date_str[11:19] if len(date_str) > 11 else ''
                        
                        sales_data.append([
                            nozzle_name,
                            fuel_name,
                            f"{float(sale.get('opening_reading', 0)):.2f}",
                            f"{float(sale.get('quantity', 0)):.2f}",
                            f"{float(sale.get('closing_reading', 0)):.2f}",
                            f"{float(sale.get('unit_price', 0)):.2f}",
                            f"{float(sale.get('total_amount', 0)):,.2f}",
                            date_display,
                            time_display
                        ])
                    
                    sales_table = Table(sales_data, colWidths=[0.9*inch, 0.9*inch, 0.7*inch, 0.7*inch, 0.7*inch, 0.7*inch, 0.9*inch, 0.8*inch, 0.7*inch])
                    sales_table.setStyle(TableStyle([
                        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#388E3C')),
                        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                        ('FONTSIZE', (0, 0), (-1, 0), 9),
                        ('FONTSIZE', (0, 1), (-1, -1), 8),
                        ('TOPPADDING', (0, 0), (-1, -1), 4),
                        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
                        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#F1F8E9')]),
                        ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#BDBDBD'))
                    ]))
                    elements.append(sales_table)
                    elements.append(Spacer(1, 0.2*inch))
                
                # Purchases section
                if today_purchases:
                    elements.append(PageBreak())
                    purchases_heading_style = ParagraphStyle(
                        'PurchasesHeading',
                        parent=styles['Heading2'],
                        fontSize=12,
                        textColor=colors.HexColor('#E65100'),
                        spaceAfter=8
                    )
                    elements.append(Paragraph(f"Purchases ({len(today_purchases)} transactions)", purchases_heading_style))
                    
                    # Build lookups for fuel types
                    tanks = {t.id: {'name': t.name, 'fuel_type_id': t.fuel_type_id} for t in self.tank_service.list_tanks()}
                    fuels = {f.id: f.name for f in self.fuel_service.list_fuel_types()}
                    
                    purchases_data = [['Tank', 'Fuel Type', 'Qty (L)', 'Unit Cost', 'Total Cost (Rs)', 'Supplier', 'Date']]
                    for purchase in today_purchases:
                        tank_id = purchase.get('tank_id', '')
                        tank_info = tanks.get(tank_id, {})
                        tank_name = tank_info.get('name', 'Unknown')
                        
                        # Get fuel type from tank's fuel_type_id
                        tank_fuel_type_id = tank_info.get('fuel_type_id', '')
                        fuel_name = fuels.get(tank_fuel_type_id, 'Unknown')
                        
                        # Extract date
                        date_str = purchase.get('purchase_date', purchase.get('date', ''))
                        date_display = date_str[:10] if date_str else ''
                        
                        purchases_data.append([
                            tank_name,
                            fuel_name,
                            f"{float(purchase.get('quantity', 0)):.2f}",
                            f"{float(purchase.get('unit_cost', 0)):.2f}",
                            f"{float(purchase.get('total_cost', 0)):,.2f}",
                            purchase.get('supplier_name', 'Unknown'),
                            date_display
                        ])
                    
                    purchases_table = Table(purchases_data, colWidths=[1.1*inch, 1.1*inch, 0.9*inch, 0.9*inch, 1.1*inch, 1*inch, 0.8*inch])
                    purchases_table.setStyle(TableStyle([
                        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#E65100')),
                        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                        ('FONTSIZE', (0, 0), (-1, 0), 10),
                        ('FONTSIZE', (0, 1), (-1, -1), 9),
                        ('TOPPADDING', (0, 0), (-1, -1), 5),
                        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
                        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#FFF3E0')]),
                        ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#BDBDBD'))
                    ]))
                    elements.append(purchases_table)
                    elements.append(Spacer(1, 0.2*inch))
                
                # Expenses section
                if today_expenses:
                    expenses_heading_style = ParagraphStyle(
                        'ExpensesHeading',
                        parent=styles['Heading2'],
                        fontSize=12,
                        textColor=colors.HexColor('#D32F2F'),
                        spaceAfter=8
                    )
                    elements.append(Paragraph(f"Expenses ({len(today_expenses)} transactions)", expenses_heading_style))
                    expenses_data = [['Description', 'Category', 'Amount (Rs)', 'Payment Method']]
                    for expense in today_expenses:
                        expenses_data.append([
                            expense.get('description', '')[:20],
                            expense.get('category', '')[:15],
                            f"{float(expense.get('amount', 0)):,.2f}",
                            expense.get('payment_method', 'Cash')
                        ])
                    
                    expenses_table = Table(expenses_data, colWidths=[2*inch, 1.5*inch, 1*inch, 1*inch])
                    expenses_table.setStyle(TableStyle([
                        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#D32F2F')),
                        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                        ('FONTSIZE', (0, 0), (-1, 0), 10),
                        ('FONTSIZE', (0, 1), (-1, -1), 9),
                        ('TOPPADDING', (0, 0), (-1, -1), 5),
                        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
                        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#FFEBEE')]),
                        ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#BDBDBD'))
                    ]))
                    elements.append(expenses_table)
                
                # Build PDF
                doc.build(elements)
                QMessageBox.information(self, "Success", f"Daily transactions report exported successfully to:\n{file_path}")
                
            except ImportError:
                QMessageBox.warning(self, "Missing Library", "reportlab is not installed. Please install it to export to PDF.\n\nRun: pip install reportlab")
        except Exception as e:
            logger.error(f"Error exporting transactions to PDF: {str(e)}")
            QMessageBox.critical(self, "Error", f"Failed to export PDF: {str(e)}")

    def manage_nozzles(self):
        """Manage nozzles."""
        print("Manage Nozzles clicked")

    def add_nozzles_settings(self):
        """Add nozzles from settings."""
        dialog = AddNozzleDialog(self.fuel_service, self.nozzle_service)
        if dialog.exec_() == QDialog.Accepted:
            QMessageBox.information(self, "Success", "Nozzle added successfully!")

    def add_fuel_type_settings(self):
        """Add fuel type from settings."""
        dialog = AddFuelTypeDialog(self.fuel_service)
        if dialog.exec_() == QDialog.Accepted:
            QMessageBox.information(self, "Success", "Fuel type added successfully!")

    def add_account_heads(self):
        """Add account heads."""
        dialog = AddAccountHeadsDialog(self.db_service)
        if dialog.exec_() == QDialog.Accepted:
            QMessageBox.information(self, "Success", "Account head added successfully!")

    def create_card(self, title: str, value: str, bg_color: str) -> QFrame:
        """Create dashboard card."""
        card = QFrame()
        card.setStyleSheet(f"background-color: {bg_color}; border-radius: 10px; padding: 15px;")

        layout = QVBoxLayout(card)
        title_label = QLabel(title)
        title_label.setFont(QFont("Arial", 11))
        title_label.setStyleSheet("color: #666;")
        layout.addWidget(title_label)

        value_label = QLabel(value)
        value_label.setFont(QFont("Arial", 20, QFont.Bold))
        value_label.setStyleSheet("color: #333;")
        layout.addWidget(value_label)

        # Store reference for updates
        card.value_label = value_label

        return card

    def create_action_button(self, text: str, color: str) -> QPushButton:
        """Create action button."""
        btn = QPushButton(text)
        btn.setMinimumHeight(50)
        btn.setFont(QFont("Arial", 10, QFont.Bold))
        btn.setStyleSheet(
            f"QPushButton {{ background-color: {color}; color: white; border-radius: 5px; }}"
            f"QPushButton:hover {{ background-color: {self._darken_color(color)}; }}"
        )
        return btn

    def setup_refresh_timer(self):
        """Setup auto-refresh timer."""
        self.refresh_timer = QTimer()
        self.refresh_timer.timeout.connect(self.load_dashboard_data)
        self.refresh_timer.start(30000)  # Refresh every 30 seconds

    def load_dashboard_data(self):
        """Load dashboard data from real sales and purchase records."""
        try:
            # Load payment methods from account heads
            self.payment_methods = self.account_head_service.get_payment_methods()
            
            # Initialize default payment methods if none exist
            if not self.payment_methods:
                self.account_head_service.initialize_default_payment_methods()
                self.payment_methods = self.account_head_service.get_payment_methods()
            
            # Get all sales records
            sales_data = self.db_service.list_documents('sales')
            
            # Get all purchase records
            purchase_data = self.db_service.list_documents('purchases')
            
            # Get all customers
            customers_data = self.db_service.list_documents('customers')
            
            # Get all expenses
            expenses_data = self.db_service.list_documents('expenses')
            
            # Get all tanks for inventory status
            tanks = self.tank_service.list_tanks()
            
            # Calculate sales metrics
            total_sales_units = 0
            total_sales_revenue = 0
            total_sales_count = 0
            
            for sale in sales_data:
                quantity = float(sale.get('quantity', 0))
                total_amount = float(sale.get('total_amount', 0))
                total_sales_units += quantity
                total_sales_revenue += total_amount
                total_sales_count += 1
            
            # Calculate purchase costs
            total_purchase_cost = 0
            for purchase in purchase_data:
                total_cost = float(purchase.get('total_cost', 0))
                total_purchase_cost += total_cost
            
            # Calculate total expenses
            total_expenses = 0
            for expense in expenses_data:
                amount = float(expense.get('amount', 0))
                total_expenses += amount
            
            # Net Revenue = Sales Revenue - Purchase Cost - Expenses
            net_revenue = total_sales_revenue - total_purchase_cost - total_expenses
            
            # Average ticket (revenue per transaction)
            average_ticket = total_sales_revenue / total_sales_count if total_sales_count > 0 else 0
            
            # Total customers count
            total_customers = len(customers_data)
            
            # Daily fuel sold (assuming all sales are from today - can be filtered by date)
            daily_fuel = total_sales_units
            
            # Inventory status (total current stock in all tanks)
            inventory_status = sum(float(tank.current_stock) for tank in tanks if hasattr(tank, 'current_stock'))
            
            # Update KPI labels with calculated values
            if 'total_sales' in self.kpi_labels:
                self.kpi_labels['total_sales'].setText(f"{total_sales_units:,.2f}")
            
            # Now showing Net Revenue (Sales - Purchases - Expenses)
            if 'total_revenue' in self.kpi_labels:
                self.kpi_labels['total_revenue'].setText(f"Rs. {net_revenue:,.0f}")
            
            if 'average_ticket' in self.kpi_labels:
                self.kpi_labels['average_ticket'].setText(f"Rs. {average_ticket:,.0f}")
            
            if 'daily_fuel' in self.kpi_labels:
                self.kpi_labels['daily_fuel'].setText(f"{daily_fuel:,.2f}")
            
            if 'total_customers' in self.kpi_labels:
                self.kpi_labels['total_customers'].setText(str(total_customers))
            
            if 'inventory_status' in self.kpi_labels:
                self.kpi_labels['inventory_status'].setText(f"{inventory_status:,.0f}")
                
        except Exception as e:
            print(f"Error loading dashboard data: {str(e)}")

    def _has_permission(self, permission: str) -> bool:
        """Check if user has permission."""
        from src.config.firebase_config import AppConfig
        role_config = AppConfig.ROLES.get(self.user.role.value, {})
        permissions = role_config.get('permissions', [])
        return 'all' in permissions or permission in permissions

    def _darken_color(self, hex_color: str) -> str:
        """Darken a hex color."""
        return hex_color


class AddFuelTypeDialog(QDialog):
    """Dialog for adding multiple fuel types in grid format."""

    def __init__(self, fuel_service, parent=None):
        """Initialize dialog."""
        super().__init__(parent)
        self.fuel_service = fuel_service
        
        self.setWindowTitle("Add Fuel Types")
        self.resize(800, 500)
        self._center_on_screen()
        self.init_ui()

    def _center_on_screen(self):
        """Center dialog on screen."""
        from PyQt5.QtWidgets import QDesktopWidget
        screen = QDesktopWidget().screenGeometry()
        size = self.geometry()
        self.move((screen.width() - size.width()) // 2, (screen.height() - size.height()) // 2)

    def init_ui(self):
        """Initialize UI components with grid-based entry."""
        layout = QVBoxLayout()
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(10)

        # Title
        title_label = QLabel("Add Multiple Fuel Types")
        title_label.setFont(QFont("Arial", 12, QFont.Bold))
        layout.addWidget(title_label)

        # Create table for data entry
        self.table = QTableWidget()
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels(["Name", "Unit Price (Rs)", "Tax %", "Actions"])
        self.table.setAlternatingRowColors(True)
        self.table.setMinimumHeight(300)
        self.table.setStyleSheet(
            "QTableWidget { background-color: white; alternate-background-color: #f9f9f9; border: 1px solid #ddd; }"
            "QHeaderView::section { background-color: #2196F3; color: white; padding: 5px; border: none; font-weight: bold; }"
            "QTableWidget::item { padding: 5px; border-bottom: 1px solid #e0e0e0; }"
        )
        # Set column widths - Name wider, numeric fields narrower
        self.table.setColumnWidth(0, 240)  # Name
        self.table.setColumnWidth(1, 120)  # Unit Price
        self.table.setColumnWidth(2, 80)   # Tax %
        self.table.setColumnWidth(3, 100)  # Actions
        self.table.horizontalHeader().setStretchLastSection(False)
        self.table.verticalHeader().setDefaultSectionSize(40)
        
        # Add initial single empty row
        self.add_empty_rows(1)
        
        layout.addWidget(self.table)

        # Buttons
        button_layout = QHBoxLayout()
        
        add_row_btn = QPushButton("+ Add Row")
        add_row_btn.setStyleSheet(
            "QPushButton { background-color: #FF9800; color: white; padding: 8px 20px; border-radius: 5px; }"
            "QPushButton:hover { background-color: #F57C00; }"
        )
        add_row_btn.clicked.connect(lambda: self.add_empty_rows(1))
        button_layout.addWidget(add_row_btn)
        
        save_btn = QPushButton("Save All")
        save_btn.setStyleSheet(
            "QPushButton { background-color: #4CAF50; color: white; padding: 8px 20px; border-radius: 5px; }"
            "QPushButton:hover { background-color: #45a049; }"
        )
        save_btn.clicked.connect(self.save_all_fuel_types)
        button_layout.addWidget(save_btn)
        
        view_btn = QPushButton("View Records")
        view_btn.setStyleSheet(
            "QPushButton { background-color: #2196F3; color: white; padding: 8px 20px; border-radius: 5px; }"
            "QPushButton:hover { background-color: #0b7dda; }"
        )
        view_btn.clicked.connect(self.view_fuel_types_list)
        button_layout.addWidget(view_btn)
        
        cancel_btn = QPushButton("Close")
        cancel_btn.setStyleSheet(
            "QPushButton { background-color: #f44336; color: white; padding: 8px 20px; border-radius: 5px; }"
            "QPushButton:hover { background-color: #da190b; }"
        )
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(cancel_btn)
        
        layout.addLayout(button_layout)
        self.setLayout(layout)

    def add_empty_rows(self, count=1):
        """Add empty rows to the table."""
        current_rows = self.table.rowCount()
        self.table.setRowCount(current_rows + count)
        
        for i in range(current_rows, current_rows + count):
            # Name
            self.table.setItem(i, 0, QTableWidgetItem(""))
            # Price
            price_item = QTableWidgetItem("0.00")
            price_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            self.table.setItem(i, 1, price_item)
            # Tax
            tax_item = QTableWidgetItem("10.00")
            tax_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            self.table.setItem(i, 2, tax_item)
            # Delete button
            delete_btn = QPushButton("Delete")
            delete_btn.setStyleSheet(
                "QPushButton { background-color: #f44336; color: white; padding: 4px 10px; border-radius: 3px; font-size: 11px; }"
                "QPushButton:hover { background-color: #da190b; }"
            )
            delete_btn.clicked.connect(lambda: self.delete_row(i))
            self.table.setCellWidget(i, 3, delete_btn)

    def delete_row(self, row):
        """Delete a row from the table."""
        self.table.removeRow(row)

    def save_all_fuel_types(self):
        """Save all fuel types from the table."""
        try:
            saved_count = 0
            errors = []
            
            for row in range(self.table.rowCount()):
                name = self.table.item(row, 0).text().strip()
                
                # Skip empty rows
                if not name:
                    continue
                
                try:
                    price = float(self.table.item(row, 1).text())
                    tax = float(self.table.item(row, 2).text())
                    
                    if price <= 0:
                        errors.append(f"Row {row + 1}: Price must be greater than 0")
                        continue
                    
                    success, msg, _ = self.fuel_service.create_fuel_type(
                        name=name,
                        unit_price=price,
                        tax_percentage=tax
                    )
                    
                    if success:
                        saved_count += 1
                        self.table.item(row, 0).setText("")
                        self.table.item(row, 1).setText("0.00")
                        self.table.item(row, 2).setText("10.00")
                    else:
                        errors.append(f"Row {row + 1}: {msg}")
                except ValueError:
                    errors.append(f"Row {row + 1}: Invalid number format")
            
            if saved_count > 0:
                QMessageBox.information(self, "Success", f"Successfully saved {saved_count} fuel type(s)")
                # Reset grid to 1 empty row
                self.table.setRowCount(0)
                self.add_empty_rows(1)
                self.view_fuel_types_list()
            
            if errors:
                error_msg = "\n".join(errors)
                QMessageBox.warning(self, "Errors", f"Errors encountered:\n\n{error_msg}")
                
        except Exception as e:
            QMessageBox.critical(self, "Error", f"An error occurred: {str(e)}")

    def view_fuel_types_list(self):
        """View fuel types list in grid."""
        try:
            fuel_types = self.fuel_service.list_fuel_types()
            columns = ["Name", "Unit Price (Rs)", "Tax %"]
            data = []
            
            for fuel in fuel_types:
                data.append([
                    fuel.name,
                    f"{float(fuel.unit_price):.2f}",
                    f"{float(fuel.tax_percentage):.2f}"
                ])
            
            if not data:
                data = [["No fuel types found", "", ""]]
            
            dialog = DataViewDialog("Fuel Types", columns, data, self)
            dialog.exec_()
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Failed to load fuel types: {str(e)}")


class AddTankDialog(QDialog):
    """Dialog for adding multiple tanks in grid format."""

    def __init__(self, tank_service, fuel_service, parent=None):
        """Initialize dialog."""
        super().__init__(parent)
        self.tank_service = tank_service
        self.fuel_service = fuel_service
        
        self.setWindowTitle("Add Tanks")
        self.resize(1050, 600)
        self._center_on_screen()
        self.init_ui()

    def _center_on_screen(self):
        """Center dialog on screen."""
        from PyQt5.QtWidgets import QDesktopWidget
        screen = QDesktopWidget().screenGeometry()
        size = self.geometry()
        self.move((screen.width() - size.width()) // 2, (screen.height() - size.height()) // 2)

    def init_ui(self):
        """Initialize UI components with grid-based entry."""
        layout = QVBoxLayout()
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(10)

        # Title
        title_label = QLabel("Add Multiple Tanks")
        title_label.setFont(QFont("Arial", 12, QFont.Bold))
        layout.addWidget(title_label)

        # Create table for data entry
        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels(["Name", "Fuel Type", "Capacity (L)", "Min Stock (L)", "Location", "Actions"])
        self.table.setColumnCount(6)
        self.table.setAlternatingRowColors(True)
        self.table.setMinimumHeight(300)
        self.table.setStyleSheet(
            "QTableWidget { background-color: white; alternate-background-color: #f9f9f9; border: 1px solid #ddd; }"
            "QHeaderView::section { background-color: #2196F3; color: white; padding: 5px; border: none; font-weight: bold; }"
            "QTableWidget::item { padding: 5px; border-bottom: 1px solid #e0e0e0; }"
        )
        # Set column widths - Name/Location wider, numeric fields narrower
        self.table.setColumnWidth(0, 160)  # Name
        self.table.setColumnWidth(1, 130)  # Fuel Type
        self.table.setColumnWidth(2, 110)  # Capacity
        self.table.setColumnWidth(3, 110)  # Min Stock
        self.table.setColumnWidth(4, 150)  # Location
        self.table.setColumnWidth(5, 100)  # Actions
        self.table.horizontalHeader().setStretchLastSection(False)
        self.table.verticalHeader().setDefaultSectionSize(40)
        
        # Store fuel types for combo boxes
        self.fuel_types_dict = {}
        try:
            fuel_types = self.fuel_service.list_fuel_types()
            for fuel in fuel_types:
                self.fuel_types_dict[fuel.name] = fuel.id
        except:
            pass
        
        # Add initial single empty row
        self.add_empty_rows(1)
        
        layout.addWidget(self.table)

        # Buttons
        button_layout = QHBoxLayout()
        
        add_row_btn = QPushButton("+ Add Row")
        add_row_btn.setStyleSheet(
            "QPushButton { background-color: #FF9800; color: white; padding: 8px 20px; border-radius: 5px; }"
            "QPushButton:hover { background-color: #F57C00; }"
        )
        add_row_btn.clicked.connect(lambda: self.add_empty_rows(1))
        button_layout.addWidget(add_row_btn)
        
        save_btn = QPushButton("Save All")
        save_btn.setStyleSheet(
            "QPushButton { background-color: #4CAF50; color: white; padding: 8px 20px; border-radius: 5px; }"
            "QPushButton:hover { background-color: #45a049; }"
        )
        save_btn.clicked.connect(self.save_all_tanks)
        button_layout.addWidget(save_btn)
        
        view_btn = QPushButton("View Records")
        view_btn.setStyleSheet(
            "QPushButton { background-color: #2196F3; color: white; padding: 8px 20px; border-radius: 5px; }"
            "QPushButton:hover { background-color: #0b7dda; }"
        )
        view_btn.clicked.connect(self.view_tanks_list)
        button_layout.addWidget(view_btn)
        
        cancel_btn = QPushButton("Close")
        cancel_btn.setStyleSheet(
            "QPushButton { background-color: #f44336; color: white; padding: 8px 20px; border-radius: 5px; }"
            "QPushButton:hover { background-color: #da190b; }"
        )
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(cancel_btn)
        
        layout.addLayout(button_layout)
        self.setLayout(layout)

    def add_empty_rows(self, count=1):
        """Add empty rows to the table."""
        current_rows = self.table.rowCount()
        self.table.setRowCount(current_rows + count)
        
        for i in range(current_rows, current_rows + count):
            # Name
            self.table.setItem(i, 0, QTableWidgetItem(""))
            # Fuel Type (combo)
            fuel_combo = QComboBox()
            fuel_combo.addItems(list(self.fuel_types_dict.keys()))
            self.table.setCellWidget(i, 1, fuel_combo)
            # Capacity
            cap_item = QTableWidgetItem("0.00")
            cap_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            self.table.setItem(i, 2, cap_item)
            # Min Stock
            min_item = QTableWidgetItem("0.00")
            min_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            self.table.setItem(i, 3, min_item)
            # Location
            self.table.setItem(i, 4, QTableWidgetItem(""))
            # Delete button
            delete_btn = QPushButton("Delete")
            delete_btn.setStyleSheet(
                "QPushButton { background-color: #f44336; color: white; padding: 4px 10px; border-radius: 3px; font-size: 11px; }"
                "QPushButton:hover { background-color: #da190b; }"
            )
            delete_btn.clicked.connect(lambda: self.delete_row(i))
            self.table.setCellWidget(i, 5, delete_btn)

    def delete_row(self, row):
        """Delete a row from the table."""
        self.table.removeRow(row)

    def save_all_tanks(self):
        """Save all tanks from the table."""
        try:
            saved_count = 0
            errors = []
            
            for row in range(self.table.rowCount()):
                name = self.table.item(row, 0).text().strip()
                
                # Skip empty rows
                if not name:
                    continue
                
                try:
                    fuel_combo = self.table.cellWidget(row, 1)
                    fuel_name = fuel_combo.currentText()
                    fuel_type_id = self.fuel_types_dict.get(fuel_name)
                    
                    if not fuel_type_id:
                        errors.append(f"Row {row + 1}: Fuel type not found")
                        continue
                    
                    capacity = float(self.table.item(row, 2).text())
                    min_stock = float(self.table.item(row, 3).text())
                    location = self.table.item(row, 4).text().strip()
                    
                    if capacity <= 0:
                        errors.append(f"Row {row + 1}: Capacity must be greater than 0")
                        continue
                    
                    success, msg, _ = self.tank_service.create_tank(
                        name=name,
                        fuel_type_id=fuel_type_id,
                        capacity=capacity,
                        minimum_stock=min_stock
                    )
                    
                    if success:
                        saved_count += 1
                        self.table.item(row, 0).setText("")
                        self.table.item(row, 2).setText("0.00")
                        self.table.item(row, 3).setText("0.00")
                        self.table.item(row, 4).setText("")
                    else:
                        errors.append(f"Row {row + 1}: {msg}")
                except ValueError:
                    errors.append(f"Row {row + 1}: Invalid number format")
            
            if saved_count > 0:
                QMessageBox.information(self, "Success", f"Successfully saved {saved_count} tank(s)")
                # Reset grid to 1 empty row
                self.table.setRowCount(0)
                self.add_empty_rows(1)
                self.view_tanks_list()
            
            if errors:
                error_msg = "\n".join(errors)
                QMessageBox.warning(self, "Errors", f"Errors encountered:\n\n{error_msg}")
                
        except Exception as e:
            QMessageBox.critical(self, "Error", f"An error occurred: {str(e)}")

    def view_tanks_list(self):
        """View tanks list in grid."""
        try:
            tanks = self.tank_service.list_tanks()
            # Build lookup map for fuel type names
            fuel_types = self.fuel_service.list_fuel_types()
            fuel_map = {f.id: f.name for f in fuel_types}
            
            columns = ["Name", "Fuel Type", "Capacity (L)", "Min Stock (L)", "Location"]
            data = []
            
            for tank in tanks:
                fuel_name = fuel_map.get(tank.fuel_type_id, tank.fuel_type_id)
                data.append([
                    tank.name,
                    fuel_name,
                    f"{float(tank.capacity):.0f}",
                    f"{float(tank.minimum_stock):.0f}",
                    tank.location
                ])
            
            if not data:
                data = [["No tanks found", "", "", "", ""]]
            
            dialog = DataViewDialog("Tanks", columns, data, self)
            dialog.exec_()
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Failed to load tanks: {str(e)}")


class AddAccountHeadsDialog(QDialog):
    """Dialog for adding multiple account heads with grid interface."""

    def __init__(self, db_service, parent=None):
        """Initialize dialog."""
        super().__init__(parent)
        self.db_service = db_service
        if not self.db_service and parent:
            self.db_service = getattr(parent, 'db_service', None)
        
        self.setWindowTitle("Add Account Heads")
        self.resize(1050, 600)
        self._center_on_screen()
        self.account_types = ["Revenue", "Expense", "Asset", "Liability", "Equity"]
        self.init_ui()

    def _center_on_screen(self):
        """Center dialog on screen."""
        from PyQt5.QtWidgets import QDesktopWidget
        screen = QDesktopWidget().screenGeometry()
        size = self.geometry()
        self.move((screen.width() - size.width()) // 2, (screen.height() - size.height()) // 2)

    def init_ui(self):
        """Initialize UI components."""
        layout = QVBoxLayout()
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(12)

        # Title label
        title_label = QLabel("Add Account Heads")
        title_label.setFont(QFont("Arial", 14, QFont.Bold))
        layout.addWidget(title_label)

        # Create table widget
        self.table = QTableWidget()
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels(["Name", "Account Type", "Code", "Opening Balance (Rs)", "Outstanding (Rs)", "Description", "Actions"])
        self.table.setColumnCount(7)
        self.table.setAlternatingRowColors(True)
        self.table.setStyleSheet(
            "QTableWidget { background-color: white; alternate-background-color: #f9f9f9; border: 1px solid #ddd; }"
            "QHeaderView::section { background-color: #2196F3; color: white; padding: 5px; border: none; font-weight: bold; }"
            "QTableWidget::item { padding: 5px; border-bottom: 1px solid #e0e0e0; }"
        )
        # Set column widths
        self.table.setColumnCount(7)
        self.table.setColumnWidth(0, 130)  # Name
        self.table.setColumnWidth(1, 110)  # Account Type
        self.table.setColumnWidth(2, 90)   # Code
        self.table.setColumnWidth(3, 120)  # Opening Balance
        self.table.setColumnWidth(4, 120)  # Outstanding
        self.table.setColumnWidth(5, 140)  # Description
        self.table.setColumnWidth(6, 100)  # Actions
        self.table.horizontalHeader().setStretchLastSection(False)
        self.table.verticalHeader().setDefaultSectionSize(40)
        layout.addWidget(self.table)
        
        # Add initial empty row
        self.add_empty_rows(1)

        # Buttons
        button_layout = QHBoxLayout()
        
        add_row_btn = QPushButton("+ Add Row")
        add_row_btn.setStyleSheet(
            "QPushButton { background-color: #FF9800; color: white; padding: 8px 20px; border-radius: 5px; font-weight: bold; }"
            "QPushButton:hover { background-color: #F57C00; }"
        )
        add_row_btn.clicked.connect(lambda: self.add_empty_rows(1))
        button_layout.addWidget(add_row_btn)
        
        save_btn = QPushButton("Save All")
        save_btn.setStyleSheet(
            "QPushButton { background-color: #4CAF50; color: white; padding: 8px 20px; border-radius: 5px; font-weight: bold; }"
            "QPushButton:hover { background-color: #45a049; }"
        )
        save_btn.clicked.connect(self.save_all_account_heads)
        button_layout.addWidget(save_btn)
        
        view_btn = QPushButton("View Records")
        view_btn.setStyleSheet(
            "QPushButton { background-color: #2196F3; color: white; padding: 8px 20px; border-radius: 5px; font-weight: bold; }"
            "QPushButton:hover { background-color: #0b7dda; }"
        )
        view_btn.clicked.connect(self.view_account_heads_list)
        button_layout.addWidget(view_btn)
        
        close_btn = QPushButton("Close")
        close_btn.setStyleSheet(
            "QPushButton { background-color: #f44336; color: white; padding: 8px 20px; border-radius: 5px; font-weight: bold; }"
            "QPushButton:hover { background-color: #da190b; }"
        )
        close_btn.clicked.connect(self.reject)
        button_layout.addWidget(close_btn)
        
        layout.addLayout(button_layout)
        self.setLayout(layout)

    def add_empty_rows(self, count=1):
        """Add empty rows to table."""
        for _ in range(count):
            row = self.table.rowCount()
            self.table.insertRow(row)
            
            # Name cell
            self.table.setItem(row, 0, QTableWidgetItem(""))
            
            # Account Type combo
            type_combo = QComboBox()
            type_combo.addItems(self.account_types)
            self.table.setCellWidget(row, 1, type_combo)
            
            # Code cell
            self.table.setItem(row, 2, QTableWidgetItem(""))
            
            # Opening Balance cell
            self.table.setItem(row, 3, QTableWidgetItem("0.00"))
            
            # Outstanding Balance cell
            self.table.setItem(row, 4, QTableWidgetItem("0.00"))
            
            # Description cell
            self.table.setItem(row, 5, QTableWidgetItem(""))
            # Delete button
            delete_btn = QPushButton("Delete")
            delete_btn.setStyleSheet(
                "QPushButton { background-color: #f44336; color: white; padding: 4px 10px; border-radius: 3px; font-size: 11px; }"
                "QPushButton:hover { background-color: #da190b; }"
            )
            delete_btn.clicked.connect(lambda: self.delete_row(row))
            self.table.setCellWidget(row, 6, delete_btn)

    def delete_row(self, row):
        """Delete a row from the table."""
        self.table.removeRow(row)

    def save_all_account_heads(self):
        """Save all non-empty account heads to database."""
        try:
            errors = {}
            saved_rows = []
            
            for row in range(self.table.rowCount()):
                # Get row data
                name = self.table.item(row, 0)
                type_widget = self.table.cellWidget(row, 1)
                code = self.table.item(row, 2)
                opening_balance = self.table.item(row, 3)
                outstanding_balance = self.table.item(row, 4)
                desc = self.table.item(row, 5)
                
                name_text = name.text().strip() if name else ""
                account_type = type_widget.currentText() if type_widget else ""
                code_text = code.text().strip() if code else ""
                opening_bal_text = opening_balance.text().strip() if opening_balance else "0.00"
                outstanding_bal_text = outstanding_balance.text().strip() if outstanding_balance else "0.00"
                desc_text = desc.text().strip() if desc else ""
                
                # Skip empty rows
                if not name_text and not code_text:
                    continue
                
                # Validate required fields
                if not name_text:
                    errors[row + 1] = "Account Head Name is required"
                    continue
                
                if not code_text:
                    errors[row + 1] = "Account Code is required"
                    continue
                
                # Validate balance fields
                try:
                    opening_bal = float(opening_bal_text) if opening_bal_text else 0.0
                    outstanding_bal = float(outstanding_bal_text) if outstanding_bal_text else 0.0
                except ValueError:
                    errors[row + 1] = "Opening and Outstanding balances must be valid numbers"
                    continue
                
                # Create account head
                try:
                    account_id = self.db_service.firestore.collection('account_heads').document().id
                    data = {
                        'id': account_id,
                        'name': name_text,
                        'head_type': account_type,  # Save the selected account type (Revenue, Expense, Asset, Liability, Equity)
                        'account_type': account_type,  # Also save as account_type for backward compatibility
                        'code': code_text,
                        'description': desc_text,
                        'opening_balance': opening_bal,
                        'outstanding_balance': outstanding_bal,
                        'status': 'active',
                        'is_active': True
                    }
                    
                    success, msg = self.db_service.create_document('account_heads', account_id, data)
                    
                    if success:
                        saved_rows.append(row)
                    else:
                        errors[row + 1] = msg
                except Exception as e:
                    errors[row + 1] = str(e)
            
            # Display results
            if errors:
                error_msg = "Errors occurred:\n\n"
                for row, error in errors.items():
                    error_msg += f"Row {row}: {error}\n"
                if saved_rows:
                    error_msg += f"\n{len(saved_rows)} account head(s) saved successfully."
                QMessageBox.warning(self, "Validation Errors", error_msg)
            else:
                QMessageBox.information(self, "Success", f"All {len(saved_rows)} account head(s) saved successfully!")
                # Reset grid to 1 empty row
                self.table.setRowCount(0)
                self.add_empty_rows(1)
                self.view_account_heads_list()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"An error occurred: {str(e)}")

    def view_account_heads_list(self):
        """View account heads list in grid."""
        try:
            accounts = self.db_service.list_documents('account_heads')
            columns = ["Name", "Type", "Code", "Description"]
            data = []
            
            for account in accounts:
                data.append([
                    account.get('name', ''),
                    account.get('account_type', ''),
                    account.get('code', ''),
                    account.get('description', '')
                ])
            
            if not data:
                data = [["No account heads found", "", "", ""]]
            
            dialog = DataViewDialog("Account Heads", columns, data, self)
            dialog.exec_()
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Failed to load account heads: {str(e)}")


class AddNozzleDialog(QDialog):
    """Dialog for adding multiple nozzles with grid interface."""

    def __init__(self, fuel_service, nozzle_service, parent=None):
        """Initialize dialog."""
        super().__init__(parent)
        self.fuel_service = fuel_service
        self.nozzle_service = nozzle_service
        if parent:
            self.db_service = getattr(parent, 'db_service', None)
        
        self.setWindowTitle("Add Nozzles")
        self.resize(1050, 600)
        self._center_on_screen()
        self.fuel_types = []
        self.load_fuel_types()
        self.init_ui()

    def _center_on_screen(self):
        """Center dialog on screen."""
        from PyQt5.QtWidgets import QDesktopWidget
        screen = QDesktopWidget().screenGeometry()
        size = self.geometry()
        self.move((screen.width() - size.width()) // 2, (screen.height() - size.height()) // 2)

    def init_ui(self):
        """Initialize UI components."""
        layout = QVBoxLayout()
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(12)

        # Title label
        title_label = QLabel("Add Nozzles")
        title_label.setFont(QFont("Arial", 14, QFont.Bold))
        layout.addWidget(title_label)

        # Create table widget
        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels(["Machine ID", "Nozzle Number", "Fuel Type", "Opening Reading (L)", "Current Reading (L)", "Actions"])
        self.table.setColumnCount(6)
        self.table.setAlternatingRowColors(True)
        self.table.setStyleSheet(
            "QTableWidget { background-color: white; alternate-background-color: #f9f9f9; border: 1px solid #ddd; }"
            "QHeaderView::section { background-color: #2196F3; color: white; padding: 5px; border: none; font-weight: bold; }"
            "QTableWidget::item { padding: 5px; border-bottom: 1px solid #e0e0e0; }"
        )
        # Set column widths
        self.table.setColumnCount(6)
        self.table.setColumnWidth(0, 160)  # Machine ID
        self.table.setColumnWidth(1, 110)  # Nozzle Number
        self.table.setColumnWidth(2, 150)  # Fuel Type
        self.table.setColumnWidth(3, 130)  # Opening Reading
        self.table.setColumnWidth(4, 130)  # Current Reading
        self.table.setColumnWidth(5, 100)  # Actions
        self.table.horizontalHeader().setStretchLastSection(False)
        self.table.verticalHeader().setDefaultSectionSize(40)
        layout.addWidget(self.table)
        
        # Add initial empty row
        self.add_empty_rows(1)

        # Buttons
        button_layout = QHBoxLayout()
        
        add_row_btn = QPushButton("+ Add Row")
        add_row_btn.setStyleSheet(
            "QPushButton { background-color: #FF9800; color: white; padding: 8px 20px; border-radius: 5px; font-weight: bold; }"
            "QPushButton:hover { background-color: #F57C00; }"
        )
        add_row_btn.clicked.connect(lambda: self.add_empty_rows(1))
        button_layout.addWidget(add_row_btn)
        
        save_btn = QPushButton("Save All")
        save_btn.setStyleSheet(
            "QPushButton { background-color: #4CAF50; color: white; padding: 8px 20px; border-radius: 5px; font-weight: bold; }"
            "QPushButton:hover { background-color: #45a049; }"
        )
        save_btn.clicked.connect(self.save_all_nozzles)
        button_layout.addWidget(save_btn)
        
        view_btn = QPushButton("View Records")
        view_btn.setStyleSheet(
            "QPushButton { background-color: #2196F3; color: white; padding: 8px 20px; border-radius: 5px; font-weight: bold; }"
            "QPushButton:hover { background-color: #0b7dda; }"
        )
        view_btn.clicked.connect(self.view_nozzles_list)
        button_layout.addWidget(view_btn)
        
        close_btn = QPushButton("Close")
        close_btn.setStyleSheet(
            "QPushButton { background-color: #f44336; color: white; padding: 8px 20px; border-radius: 5px; font-weight: bold; }"
            "QPushButton:hover { background-color: #da190b; }"
        )
        close_btn.clicked.connect(self.reject)
        button_layout.addWidget(close_btn)
        
        layout.addLayout(button_layout)
        self.setLayout(layout)

    def add_empty_rows(self, count=1):
        """Add empty rows to table."""
        for _ in range(count):
            row = self.table.rowCount()
            self.table.insertRow(row)
            
            # Machine ID cell
            self.table.setItem(row, 0, QTableWidgetItem(""))
            
            # Nozzle Number cell (numeric)
            nozzle_num_item = QTableWidgetItem("")
            self.table.setItem(row, 1, nozzle_num_item)
            
            # Fuel Type combo
            fuel_combo = QComboBox()
            fuel_combo.addItem("-- Select Fuel Type --", "")
            for fuel in self.fuel_types:
                fuel_combo.addItem(fuel.name, fuel.id)
            self.table.setCellWidget(row, 2, fuel_combo)
            
            # Opening Reading cell (numeric)
            opening_item = QTableWidgetItem("")
            self.table.setItem(row, 3, opening_item)
            
            # Current Reading cell (read-only, starts same as opening)
            current_item = QTableWidgetItem("")
            current_item.setFlags(current_item.flags() & ~Qt.ItemIsEditable)  # Make read-only
            current_item.setBackground(QColor(240, 240, 240))  # Light gray background
            self.table.setItem(row, 4, current_item)
            # Delete button
            delete_btn = QPushButton("Delete")
            delete_btn.setStyleSheet(
                "QPushButton { background-color: #f44336; color: white; padding: 4px 10px; border-radius: 3px; font-size: 11px; }"
                "QPushButton:hover { background-color: #da190b; }"
            )
            delete_btn.clicked.connect(lambda: self.delete_row(row))
            self.table.setCellWidget(row, 5, delete_btn)

    def delete_row(self, row):
        """Delete a row from the table."""
        self.table.removeRow(row)

    def load_fuel_types(self):
        """Load fuel types into memory."""
        try:
            self.fuel_types = self.fuel_service.list_fuel_types()
        except Exception as e:
            print(f"Error loading fuel types: {str(e)}")

    def save_all_nozzles(self):
        """Save all non-empty nozzles to database."""
        try:
            errors = {}
            saved_rows = []
            
            for row in range(self.table.rowCount()):
                # Get row data
                machine_id_item = self.table.item(row, 0)
                nozzle_num_item = self.table.item(row, 1)
                fuel_widget = self.table.cellWidget(row, 2)
                opening_item = self.table.item(row, 3)
                
                machine_id = machine_id_item.text().strip() if machine_id_item else ""
                nozzle_number_text = nozzle_num_item.text().strip() if nozzle_num_item else ""
                fuel_type_id = fuel_widget.currentData() if fuel_widget else ""
                opening_text = opening_item.text().strip() if opening_item else ""
                
                # Skip empty rows
                if not machine_id and not nozzle_number_text:
                    continue
                
                # Validate required fields
                if not machine_id:
                    errors[row + 1] = "Machine ID is required"
                    continue
                
                if not nozzle_number_text:
                    errors[row + 1] = "Nozzle Number is required"
                    continue
                
                if not fuel_type_id:
                    errors[row + 1] = "Fuel Type is required"
                    continue
                
                # Try to convert nozzle number to int
                try:
                    nozzle_number = int(nozzle_number_text)
                except ValueError:
                    errors[row + 1] = "Nozzle Number must be a number"
                    continue
                
                # Try to convert opening reading to float
                try:
                    opening_reading = float(opening_text) if opening_text else 0.0
                except ValueError:
                    errors[row + 1] = "Opening Reading must be a number"
                    continue
                
                # Create nozzle
                try:
                    success, msg, nozzle_id = self.nozzle_service.create_nozzle(
                        machine_id=machine_id,
                        nozzle_number=nozzle_number,
                        fuel_type_id=fuel_type_id,
                        opening_reading=opening_reading
                    )
                    
                    if success:
                        saved_rows.append(row)
                    else:
                        errors[row + 1] = msg
                except Exception as e:
                    errors[row + 1] = str(e)
            
            # Display results
            if errors:
                error_msg = "Errors occurred:\n\n"
                for row, error in errors.items():
                    error_msg += f"Row {row}: {error}\n"
                if saved_rows:
                    error_msg += f"\n{len(saved_rows)} nozzle(s) saved successfully."
                QMessageBox.warning(self, "Validation Errors", error_msg)
            else:
                QMessageBox.information(self, "Success", f"All {len(saved_rows)} nozzle(s) saved successfully!")
                # Reset grid to 1 empty row
                self.table.setRowCount(0)
                self.add_empty_rows(1)
                self.view_nozzles_list()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"An error occurred: {str(e)}")

    def view_nozzles_list(self):
        """View nozzles list in grid."""
        try:
            nozzles = self.nozzle_service.list_nozzles()
            # Build lookup map for fuel type names
            fuel_types = self.fuel_service.list_fuel_types()
            fuel_map = {f.id: f.name for f in fuel_types}
            
            columns = ["Machine ID", "Nozzle Number", "Fuel Type", "Opening Reading", "Current Reading"]
            data = []
            
            for nozzle in nozzles:
                fuel_name = fuel_map.get(nozzle.fuel_type_id, nozzle.fuel_type_id)
                current_reading = nozzle.closing_reading if nozzle.closing_reading > 0 else nozzle.opening_reading
                data.append([
                    nozzle.machine_id,
                    str(nozzle.nozzle_number),
                    fuel_name,
                    f"{float(nozzle.opening_reading):.2f}",
                    f"{float(current_reading):.2f}"
                ])
            
            if not data:
                data = [["No nozzles found", "", "", "", ""]]
            
            dialog = DataViewDialog("Nozzles", columns, data, self)
            dialog.exec_()
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Failed to load nozzles: {str(e)}")

    def _darken_color(self, hex_color: str) -> str:
        """Darken a hex color."""
        # Simple darkening - in production, use proper color math
        return hex_color  # Placeholder


class RecordSaleDialog(QDialog):
    """Dialog for recording multiple fuel sales with grid interface."""

    def __init__(self, fuel_service, nozzle_service, sales_service, db_service, tank_service=None, account_head_service=None, payment_methods=None, parent=None):
        """Initialize dialog."""
        super().__init__(parent)
        self.fuel_service = fuel_service
        self.nozzle_service = nozzle_service
        self.sales_service = sales_service
        self.db_service = db_service
        self.tank_service = tank_service
        self.account_head_service = account_head_service
        self.nozzles = []
        self.fuel_types = []
        self.tanks = []
        self.account_heads = []
        self.nozzle_fuel_map = {}
        self.payment_methods = payment_methods if payment_methods is not None else []
        
        self.setWindowTitle("Record Sales")
        self.resize(1280, 650)
        self._center_on_screen()
        self.load_data()
        self.init_ui()
        
        # Apply dialog styling
        from src.ui.widgets.custom_widgets import apply_dialog_styling
        apply_dialog_styling(self)

    def _center_on_screen(self):
        """Center dialog on screen."""
        from PyQt5.QtWidgets import QDesktopWidget
        screen = QDesktopWidget().screenGeometry()
        size = self.geometry()
        self.move((screen.width() - size.width()) // 2, (screen.height() - size.height()) // 2)

    def init_ui(self):
        """Initialize UI components."""
        layout = QVBoxLayout()
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(12)

        # Title label
        title_label = QLabel("Record Sales")
        title_label.setFont(QFont("Arial", 14, QFont.Bold))
        layout.addWidget(title_label)

        # Create table widget
        self.table = QTableWidget()
        self.table.setColumnCount(9)
        self.table.setHorizontalHeaderLabels(["Nozzle", "Fuel Type", "Opening Reading (L)", "Quantity (L)", "Closing Reading (L)", "Unit Price (Rs)", "Total (Rs)", "Account Head", "Actions"])
        self.table.setAlternatingRowColors(True)
        self.table.setStyleSheet(
            "QTableWidget { background-color: white; alternate-background-color: #f9f9f9; border: 1px solid #ddd; }"
            "QHeaderView::section { background-color: #2196F3; color: white; padding: 5px; border: none; font-weight: bold; }"
            "QTableWidget::item { padding: 5px; border-bottom: 1px solid #e0e0e0; color: black; background-color: white; }"
            "QTableWidget::item:focus { background-color: #e3f2fd; color: black; border: 2px solid #2196F3; }"
            "QLineEdit { color: black; background-color: white; border: 1px solid #ccc; padding: 2px; }"
            "QLineEdit:focus { background-color: white; color: black; border: 2px solid #2196F3; }"
            "QDoubleSpinBox { color: black; background-color: white; border: 1px solid #ccc; }"
            "QDoubleSpinBox:focus { background-color: white; color: black; border: 2px solid #2196F3; }"
            "QComboBox { color: black; background-color: white; border: 1px solid #ccc; }"
            "QComboBox:focus { background-color: white; color: black; border: 2px solid #2196F3; }"
        )
        # Set column widths
        self.table.setColumnWidth(0, 140)  # Nozzle
        self.table.setColumnWidth(1, 120)  # Fuel Type
        self.table.setColumnWidth(2, 120)  # Opening Reading
        self.table.setColumnWidth(3, 110)  # Quantity
        self.table.setColumnWidth(4, 120)  # Closing Reading
        self.table.setColumnWidth(5, 110)  # Unit Price
        self.table.setColumnWidth(6, 110)  # Total
        self.table.setColumnWidth(7, 180)  # Account Head
        self.table.setColumnWidth(8, 100)  # Actions
        self.table.horizontalHeader().setStretchLastSection(False)
        
        # Set row height for better visibility
        self.table.verticalHeader().setDefaultSectionSize(40)
        layout.addWidget(self.table)
        
        # Add initial empty row
        self.add_empty_rows(1)

        # Buttons
        button_layout = QHBoxLayout()
        
        add_row_btn = QPushButton("+ Add Row")
        add_row_btn.setStyleSheet(
            "QPushButton { background-color: #FF9800; color: white; padding: 8px 20px; border-radius: 5px; font-weight: bold; }"
            "QPushButton:hover { background-color: #F57C00; }"
        )
        add_row_btn.clicked.connect(lambda: self.add_empty_rows(1))
        button_layout.addWidget(add_row_btn)
        
        save_btn = QPushButton("Save All")
        save_btn.setStyleSheet(
            "QPushButton { background-color: #4CAF50; color: white; padding: 8px 20px; border-radius: 5px; font-weight: bold; }"
            "QPushButton:hover { background-color: #45a049; }"
        )
        save_btn.clicked.connect(self.save_all_sales)
        button_layout.addWidget(save_btn)
        
        view_btn = QPushButton("View Records")
        view_btn.setStyleSheet(
            "QPushButton { background-color: #2196F3; color: white; padding: 8px 20px; border-radius: 5px; font-weight: bold; }"
            "QPushButton:hover { background-color: #0b7dda; }"
        )
        view_btn.clicked.connect(self.view_sales)
        button_layout.addWidget(view_btn)
        
        close_btn = QPushButton("Close")
        close_btn.setStyleSheet(
            "QPushButton { background-color: #f44336; color: white; padding: 8px 20px; border-radius: 5px; font-weight: bold; }"
            "QPushButton:hover { background-color: #da190b; }"
        )
        close_btn.clicked.connect(self.reject)
        button_layout.addWidget(close_btn)
        
        layout.addLayout(button_layout)
        self.setLayout(layout)
        
        # Connect signal for calculations
        self.table.itemChanged.connect(self.on_cell_changed)

    def load_data(self):
        """Load nozzles, fuel types, tanks, and asset type account heads."""
        try:
            self.nozzles = self.nozzle_service.list_nozzles()
            self.fuel_types = self.fuel_service.list_fuel_types()
            if self.tank_service:
                self.tanks = self.tank_service.list_tanks()
            # Load only Asset type account heads for sales
            if self.account_head_service:
                self.account_heads = self.account_head_service.list_account_heads(head_type='Asset', active_only=True)
            
            # Build nozzle to fuel type map
            for nozzle in self.nozzles:
                self.nozzle_fuel_map[nozzle.id] = nozzle.fuel_type_id
        except Exception as e:
            print(f"Error loading data: {str(e)}")

    def add_empty_rows(self, count=1):
        """Add empty rows to table."""
        for _ in range(count):
            row = self.table.rowCount()
            self.table.insertRow(row)
            
            # Nozzle combo
            nozzle_combo = QComboBox()
            nozzle_combo.addItem("-- Select Nozzle --", "")
            for nozzle in self.nozzles:
                nozzle_combo.addItem(f"Nozzle {nozzle.nozzle_number} - {nozzle.machine_id}", nozzle.id)
            nozzle_combo.setStyleSheet("QComboBox { padding: 4px; font-size: 11px; }")
            nozzle_combo.currentIndexChanged.connect(lambda idx, r=row: self.on_nozzle_changed(r))
            self.table.setCellWidget(row, 0, nozzle_combo)
            
            # Fuel Type combo (auto-populated from nozzle)
            fuel_combo = QComboBox()
            fuel_combo.addItem("-- Auto-populated --", "")
            for fuel in self.fuel_types:
                fuel_combo.addItem(fuel.name, fuel.id)
            fuel_combo.setEnabled(False)
            fuel_combo.setStyleSheet("QComboBox { padding: 4px; font-size: 11px; }")
            self.table.setCellWidget(row, 1, fuel_combo)
            
            # Opening Reading cell (read-only, auto-fetched from nozzle)
            opening_item = QTableWidgetItem("0.00")
            opening_item.setFlags(opening_item.flags() & ~Qt.ItemIsEditable)
            opening_item.setBackground(QColor(240, 240, 240))  # Light gray background
            self.table.setItem(row, 2, opening_item)
            
            # Quantity cell - use spin box for better input
            qty_spin = QDoubleSpinBox()
            qty_spin.setRange(0, 100000)
            qty_spin.setDecimals(2)
            qty_spin.setStyleSheet("QDoubleSpinBox { padding: 2px; margin: 2px; font-size: 11px; }")
            qty_spin.valueChanged.connect(lambda: self.on_cell_changed(None))
            self.table.setCellWidget(row, 3, qty_spin)
            
            # Closing Reading cell (read-only, auto-calculated)
            closing_item = QTableWidgetItem("0.00")
            closing_item.setFlags(closing_item.flags() & ~Qt.ItemIsEditable)
            closing_item.setBackground(QColor(240, 240, 240))  # Light gray background
            self.table.setItem(row, 4, closing_item)
            
            # Unit Price cell - use spin box for better input
            price_spin = QDoubleSpinBox()
            price_spin.setRange(0, 100000)
            price_spin.setDecimals(2)
            price_spin.setStyleSheet("QDoubleSpinBox { padding: 2px; margin: 2px; font-size: 11px; }")
            price_spin.valueChanged.connect(lambda: self.on_cell_changed(None))
            self.table.setCellWidget(row, 5, price_spin)
            
            # Total cell (read-only, calculated)
            total_item = QTableWidgetItem("0.00")
            total_item.setFlags(total_item.flags() & ~Qt.ItemIsEditable)
            self.table.setItem(row, 6, total_item)
            
            # Account Head combo (LOV) - populated from database
            account_head_combo = QComboBox()
            account_head_combo.addItem("-- Select Account Head --", "")
            for head in self.account_heads:
                head_id = head.get('id', '')
                head_name = head.get('name', '')
                account_head_combo.addItem(head_name, head_id)
            account_head_combo.setStyleSheet("QComboBox { padding: 4px; font-size: 11px; }")
            self.table.setCellWidget(row, 7, account_head_combo)
            
            # Delete button for the row
            delete_btn = QPushButton("Delete")
            delete_btn.setStyleSheet(
                "QPushButton { background-color: #f44336; color: white; padding: 4px 10px; border-radius: 3px; font-size: 11px; }"
                "QPushButton:hover { background-color: #da190b; }"
            )
            delete_btn.clicked.connect(lambda: self.delete_row(row))
            self.table.setCellWidget(row, 8, delete_btn)

    def on_nozzle_changed(self, row):
        """Update fuel type and opening reading when nozzle changes."""
        nozzle_combo = self.table.cellWidget(row, 0)
        fuel_combo = self.table.cellWidget(row, 1)
        opening_item = self.table.item(row, 2)
        
        if nozzle_combo and fuel_combo:
            nozzle_id = nozzle_combo.currentData()
            if nozzle_id and nozzle_id in self.nozzle_fuel_map:
                fuel_type_id = self.nozzle_fuel_map[nozzle_id]
                index = fuel_combo.findData(fuel_type_id)
                if index >= 0:
                    fuel_combo.setCurrentIndex(index)
                
                # Fetch and display opening reading from nozzle
                try:
                    nozzle = self.nozzle_service.get_nozzle(nozzle_id)
                    if nozzle and opening_item:
                        # Check if there's a previous row with the same nozzle
                        previous_row = row - 1
                        opening_reading = nozzle.closing_reading if nozzle.closing_reading > 0 else nozzle.opening_reading
                        
                        # If there's a previous row, use its closing reading as this row's opening reading
                        if previous_row >= 0:
                            prev_nozzle_combo = self.table.cellWidget(previous_row, 0)
                            prev_closing_item = self.table.item(previous_row, 4)
                            if prev_nozzle_combo and prev_nozzle_combo.currentData() == nozzle_id and prev_closing_item:
                                prev_closing_text = prev_closing_item.text().strip()
                                if prev_closing_text and prev_closing_text != "0.00":
                                    try:
                                        opening_reading = float(prev_closing_text)
                                    except ValueError:
                                        pass
                        
                        opening_item.setText(f"{float(opening_reading):.2f}")
                except Exception as e:
                    print(f"Error fetching nozzle reading: {str(e)}")

    def delete_row(self, row):
        """Delete a row from the table and recalculate opening readings for remaining rows."""
        self.table.removeRow(row)
        # Recalculate opening readings for all rows after deletion
        self.recalculate_all_opening_readings()

    def recalculate_all_opening_readings(self):
        """Recalculate opening readings for all rows after a row is deleted."""
        for row in range(self.table.rowCount()):
            nozzle_combo = self.table.cellWidget(row, 0)
            opening_item = self.table.item(row, 2)
            
            if nozzle_combo and opening_item:
                nozzle_id = nozzle_combo.currentData()
                if nozzle_id and nozzle_id in self.nozzle_fuel_map:
                    try:
                        nozzle = self.nozzle_service.get_nozzle(nozzle_id)
                        if nozzle:
                            # Start with nozzle's current reading
                            opening_reading = nozzle.closing_reading if nozzle.closing_reading > 0 else nozzle.opening_reading
                            
                            # If there's a previous row with the same nozzle, use its closing reading
                            previous_row = row - 1
                            if previous_row >= 0:
                                prev_nozzle_combo = self.table.cellWidget(previous_row, 0)
                                prev_closing_item = self.table.item(previous_row, 4)
                                if prev_nozzle_combo and prev_nozzle_combo.currentData() == nozzle_id and prev_closing_item:
                                    prev_closing_text = prev_closing_item.text().strip()
                                    if prev_closing_text and prev_closing_text != "0.00":
                                        try:
                                            opening_reading = float(prev_closing_text)
                                        except ValueError:
                                            pass
                            
                            opening_item.setText(f"{float(opening_reading):.2f}")
                    except Exception as e:
                        print(f"Error recalculating opening reading: {str(e)}")

    def on_cell_changed(self, item):
        """Handle cell changes for calculations."""
        try:
            self.table.itemChanged.disconnect(self.on_cell_changed)
        except:
            pass
        
        # Calculate totals and closing readings for all rows
        for row in range(self.table.rowCount()):
            opening_item = self.table.item(row, 2)
            qty_widget = self.table.cellWidget(row, 3)
            closing_item = self.table.item(row, 4)
            price_widget = self.table.cellWidget(row, 5)
            total_item = self.table.item(row, 6)
            
            try:
                opening = float(opening_item.text()) if opening_item and opening_item.text() else 0
                qty = qty_widget.value() if qty_widget and isinstance(qty_widget, QDoubleSpinBox) else 0
                price = price_widget.value() if price_widget and isinstance(price_widget, QDoubleSpinBox) else 0
                
                # Calculate closing reading = opening + quantity
                closing = opening + qty
                if closing_item:
                    closing_item.setText(f"{closing:.2f}")
                
                # Calculate total = quantity * price
                total = qty * price
                if total_item:
                    total_item.setText(f"{total:.2f}")
            except ValueError:
                pass
        
        try:
            self.table.itemChanged.connect(self.on_cell_changed)
        except:
            pass

    def save_all_sales(self):
        """Save all non-empty sales to database."""
        try:
            errors = {}
            saved_rows = []
            nozzles_to_update = []  # Track nozzles to update after successful saves
            
            for row in range(self.table.rowCount()):
                # Get row data
                nozzle_combo = self.table.cellWidget(row, 0)
                fuel_combo = self.table.cellWidget(row, 1)
                opening_item = self.table.item(row, 2)
                qty_widget = self.table.cellWidget(row, 3)
                closing_item = self.table.item(row, 4)
                price_widget = self.table.cellWidget(row, 5)
                account_head_combo = self.table.cellWidget(row, 7)
                
                nozzle_id = nozzle_combo.currentData() if nozzle_combo else ""
                opening_text = opening_item.text().strip() if opening_item else ""
                qty_text = str(qty_widget.value()) if qty_widget and isinstance(qty_widget, QDoubleSpinBox) else ""
                closing_text = closing_item.text().strip() if closing_item else ""
                price_text = str(price_widget.value()) if price_widget and isinstance(price_widget, QDoubleSpinBox) else ""
                account_head_id = account_head_combo.currentData() if account_head_combo else ""
                
                # Skip empty rows
                if not nozzle_id and not qty_text:
                    continue
                
                # Validate required fields
                if not nozzle_id:
                    errors[row + 1] = "Nozzle is required"
                    continue
                
                if not qty_text:
                    errors[row + 1] = "Quantity is required"
                    continue
                
                if not price_text:
                    errors[row + 1] = "Unit Price is required"
                    continue
                
                if not account_head_id or account_head_id == "":
                    errors[row + 1] = "Account Head is required"
                    continue
                
                # Try to convert to numbers
                try:
                    opening_reading = float(opening_text) if opening_text else 0.0
                    quantity = float(qty_text)
                    closing_reading = float(closing_text) if closing_text else 0.0
                    unit_price = float(price_text)
                except ValueError:
                    errors[row + 1] = "Quantity, Price, and Readings must be numbers"
                    continue
                
                if quantity <= 0:
                    errors[row + 1] = "Quantity must be greater than 0"
                    continue
                
                # Validate closing > opening
                if closing_reading <= opening_reading:
                    errors[row + 1] = f"Closing reading ({closing_reading:.2f}L) must be greater than opening reading ({opening_reading:.2f}L)"
                    continue
                
                # Get account head details
                account_head_data = None
                for head in self.account_heads:
                    if head.get('id') == account_head_id:
                        account_head_data = head
                        break
                account_head_name = account_head_data.get('name', '') if account_head_data else ''
                payment_method = account_head_data.get('head_type', 'Other') if account_head_data else 'Other'
                
                # Create sale record
                try:
                    # Get nozzle and fuel details
                    nozzle = next((n for n in self.nozzles if n.id == nozzle_id), None)
                    if not nozzle:
                        errors[row + 1] = "Nozzle not found"
                        continue
                    
                    fuel = next((f for f in self.fuel_types if f.id == nozzle.fuel_type_id), None)
                    if not fuel:
                        errors[row + 1] = "Fuel type not found"
                        continue
                    
                    # Check inventory
                    tank = next((t for t in self.tanks if t.fuel_type_id == fuel.id), None)
                    if not tank:
                        errors[row + 1] = f"No tank configured for {fuel.name}"
                        continue
                    
                    if tank.current_stock < quantity:
                        errors[row + 1] = f"Insufficient {fuel.name} inventory. Available: {tank.current_stock:.2f}L, Required: {quantity:.2f}L"
                        continue
                    
                    # Calculate amounts
                    base_amount = quantity * unit_price
                    tax_amount = (base_amount * fuel.tax_percentage) / 100 if hasattr(fuel, 'tax_percentage') else 0
                    total_amount = base_amount + tax_amount
                    
                    import uuid
                    sale_id = str(uuid.uuid4())
                    
                    data = {
                        'id': sale_id,
                        'date': datetime.now().isoformat(),
                        'nozzle_id': nozzle_id,
                        'fuel_type_id': nozzle.fuel_type_id,
                        'quantity': quantity,
                        'unit_price': unit_price,
                        'base_amount': base_amount,
                        'tax_amount': tax_amount,
                        'total_amount': total_amount,
                        'opening_reading': opening_reading,
                        'closing_reading': closing_reading,
                        'account_head_id': account_head_id,
                        'account_head_name': account_head_name,
                        'payment_method': payment_method,
                        'status': 'completed'
                    }
                    
                    success, msg = self.db_service.create_document('sales', sale_id, data)
                    
                    if success:
                        # Update tank inventory after successful sale
                        new_stock = tank.current_stock - quantity
                        stock_success, stock_msg = self.tank_service.update_tank_stock(tank.id, new_stock)
                        if stock_success:
                            tank.current_stock = new_stock  # Update in-memory tank object
                            saved_rows.append(row)
                            # Track nozzle for update - update current_reading to closing_reading
                            nozzles_to_update.append((nozzle_id, closing_reading))
                        else:
                            errors[row + 1] = f"Sale saved but inventory update failed: {stock_msg}"
                    else:
                        errors[row + 1] = msg
                except Exception as e:
                    errors[row + 1] = str(e)
            
            # Update nozzle current_reading after all sales are successfully saved
            for nozzle_id, closing_reading in nozzles_to_update:
                try:
                    nozzle = self.nozzle_service.get_nozzle(nozzle_id)
                    if nozzle:
                        self.db_service.update_document('nozzles', nozzle_id, {
                            'closing_reading': closing_reading,
                            'current_reading': closing_reading
                        })
                except Exception as e:
                    print(f"Warning: Failed to update nozzle {nozzle_id}: {str(e)}")
            
            # Display results
            if errors:
                error_msg = "Errors occurred:\n\n"
                for row, error in errors.items():
                    error_msg += f"Row {row}: {error}\n"
                if saved_rows:
                    error_msg += f"\n{len(saved_rows)} sale(s) saved successfully."
                QMessageBox.warning(self, "Validation Errors", error_msg)
            else:
                QMessageBox.information(self, "Success", f"All {len(saved_rows)} sale(s) saved successfully!")
                # Reset grid to 1 empty row
                self.table.setRowCount(0)
                self.add_empty_rows(1)
                self.view_sales()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"An error occurred: {str(e)}")
            
    def load_nozzles(self):
        """Load nozzles into combo box."""
        try:
            nozzles = self.nozzle_service.list_nozzles()
            for nozzle in nozzles:
                self.nozzle_combo.addItem(f"Nozzle {nozzle.nozzle_number} - {nozzle.machine_id}", nozzle.id)
        except Exception as e:
            print(f"Error loading nozzles: {str(e)}")

    def load_fuel_types(self):
        """Load fuel types into combo box."""
        try:
            fuel_types = self.fuel_service.list_fuel_types()
            for fuel in fuel_types:
                self.fuel_combo.addItem(fuel.name, fuel.id)
        except Exception as e:
            print(f"Error loading fuel types: {str(e)}")

    def load_customers(self):
        """Load customers into combo box."""
        try:
            customers = self.db_service.firestore.collection('customers').stream()
            for customer in customers:
                data = customer.to_dict()
                self.customer_combo.addItem(data.get('name', 'Unknown'), data.get('id'))
        except Exception as e:
            print(f"Error loading customers: {str(e)}")

    def update_fuel_type(self):
        """Update fuel type when nozzle changes."""
        try:
            nozzle_id = self.nozzle_combo.currentData()
            if nozzle_id:
                nozzle = self.nozzle_service.get_nozzle(nozzle_id)
                if nozzle:
                    # Find and select the fuel type from the combo box
                    index = self.fuel_combo.findData(nozzle.fuel_type_id)
                    if index >= 0:
                        self.fuel_combo.setCurrentIndex(index)
                        self.fuel_combo.setEnabled(True)
                        
                        # Get the selected fuel type and update price
                        fuel_types = self.fuel_service.list_fuel_types()
                        for fuel in fuel_types:
                            if fuel.id == nozzle.fuel_type_id:
                                self.price_input.setValue(float(fuel.unit_price))
                                break
                    else:
                        self.fuel_combo.setEnabled(False)
                else:
                    self.fuel_combo.setEnabled(False)
            else:
                self.fuel_combo.setCurrentIndex(0)
                self.fuel_combo.setEnabled(False)
            self.calculate_total()
        except Exception as e:
            print(f"Error updating fuel type: {str(e)}")

    def calculate_total(self):
        """Calculate total amount."""
        quantity = self.qty_input.value()
        price = self.price_input.value()
        total = quantity * price
        self.total_display.setText(f"Rs. {total:,.2f}")

    def record_sale(self):
        """Record the sale."""
        try:
            nozzle_id = self.nozzle_combo.currentData()
            quantity = self.qty_input.value()
            unit_price = self.price_input.value()
            payment_method = self.payment_combo.currentText()
            customer_id = self.customer_combo.currentData()

            if not nozzle_id:
                QMessageBox.warning(self, "Error", "Please select a nozzle")
                return

            if quantity <= 0:
                QMessageBox.warning(self, "Error", "Quantity must be greater than 0")
                return

            # Get nozzle and fuel details
            nozzle = self.nozzle_service.get_nozzle(nozzle_id)
            fuel_types = self.fuel_service.list_fuel_types()
            fuel = None
            for f in fuel_types:
                if f.id == nozzle.fuel_type_id:
                    fuel = f
                    break

            if not fuel:
                QMessageBox.warning(self, "Error", "Fuel type not found")
                return

            # Calculate amounts
            base_amount = quantity * unit_price
            tax_amount = (base_amount * fuel.tax_percentage) / 100
            total_amount = base_amount + tax_amount

            # Create sale record
            from src.models import Sale, PaymentMethod, TransactionStatus
            import uuid
            
            sale = Sale(
                id=str(uuid.uuid4()),
                date=datetime.now(),
                nozzle_id=nozzle_id,
                fuel_type_id=nozzle.fuel_type_id,
                quantity=quantity,
                unit_price=unit_price,
                base_amount=base_amount,
                tax_amount=tax_amount,
                total_amount=total_amount,
                payment_method=PaymentMethod.CASH,
                operator_id=self.db_service.firestore.collection('users').stream()[0].to_dict().get('id', 'system'),
                shift_id="",
                customer_id=customer_id,
                status=TransactionStatus.COMPLETED,
                created_by="system"
            )

            success, msg, sale_id = self.sales_service.record_sale(sale)
            
            if success:
                QMessageBox.information(self, "Success", f"Sale recorded successfully!\nSale ID: {sale_id}\nTotal: Rs. {total_amount:,.2f}")
                # Redirect to view screen with updated records
                self.view_sales()
            else:
                QMessageBox.critical(self, "Error", f"Failed to record sale: {msg}")

        except Exception as e:
            QMessageBox.critical(self, "Error", f"An error occurred: {str(e)}")

    def view_sales(self):
        """View sales records in grid."""
        try:
            sales_data = self.db_service.list_documents('sales')
            # Build lookup map for nozzle names and fuel types
            nozzles = self.nozzle_service.list_nozzles()
            nozzle_map = {n.id: f"Machine {n.machine_id} - Nozzle {n.nozzle_number}" for n in nozzles}
            fuel_types = self.fuel_service.list_fuel_types()
            fuel_map = {f.id: f.name for f in fuel_types}
            # Build account head map
            account_heads = self.db_service.list_documents('account_heads')
            account_head_map = {a.get('id'): a.get('name', '') for a in account_heads}
            
            columns = ["Nozzle", "Fuel Type", "Opening (L)", "Quantity (L)", "Closing (L)", "Unit Price (Rs)", "Total (Rs)", "Account Head"]
            data = []
            
            for sale in sales_data:
                nozzle_id = sale.get('nozzle_id', '')
                nozzle_name = nozzle_map.get(nozzle_id, nozzle_id)
                fuel_type_id = sale.get('fuel_type_id', '')
                fuel_name = fuel_map.get(fuel_type_id, sale.get('fuel_type', ''))
                # Get account head name from map
                account_head_id = sale.get('account_head_id', '')
                account_head_name = account_head_map.get(account_head_id, sale.get('account_head_name', ''))
                
                data.append([
                    nozzle_name,
                    fuel_name,
                    f"{sale.get('opening_reading', 0):.2f}",
                    f"{sale.get('quantity', 0):.2f}",
                    f"{sale.get('closing_reading', 0):.2f}",
                    f"{sale.get('unit_price', sale.get('price', 0)):.2f}",
                    f"{sale.get('total_amount', 0):.2f}",
                    account_head_name
                ])
            
            if not data:
                data = [["No sales records found", "", "", "", "", "", "", ""]]
            
            dialog = DataViewDialog("Sales Records", columns, data, self)
            dialog.exec_()
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Failed to load sales: {str(e)}")


class AddCustomerDialog(QDialog):
    """Dialog for adding multiple customers with grid interface."""

    def __init__(self, db_service, parent=None):
        """Initialize dialog."""
        super().__init__(parent)
        self.db_service = db_service
        self.customer_types = ["Retail", "Wholesale", "Commercial"]
        
        self.setWindowTitle("Add Customers")
        self.resize(1050, 600)
        self._center_on_screen()
        self.init_ui()

    def _center_on_screen(self):
        """Center dialog on screen."""
        from PyQt5.QtWidgets import QDesktopWidget
        screen = QDesktopWidget().screenGeometry()
        size = self.geometry()
        self.move((screen.width() - size.width()) // 2, (screen.height() - size.height()) // 2)

    def init_ui(self):
        """Initialize UI components."""
        layout = QVBoxLayout()
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(12)

        # Title label
        title_label = QLabel("Add Customers")
        title_label.setFont(QFont("Arial", 14, QFont.Bold))
        layout.addWidget(title_label)

        # Create table widget
        self.table = QTableWidget()
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels(["Name", "Phone", "Email", "Address", "Credit Limit (Rs)", "Type", "Actions"])
        self.table.setColumnCount(7)
        self.table.setAlternatingRowColors(True)
        self.table.setStyleSheet(
            "QTableWidget { background-color: white; alternate-background-color: #f9f9f9; border: 1px solid #ddd; }"
            "QHeaderView::section { background-color: #2196F3; color: white; padding: 5px; border: none; font-weight: bold; }"
            "QTableWidget::item { padding: 5px; border-bottom: 1px solid #e0e0e0; }"
        )
        # Set column widths - Name/Address/Email wider, numeric fields narrower
        self.table.setColumnCount(7)
        self.table.setColumnWidth(0, 140)  # Name
        self.table.setColumnWidth(1, 110)  # Phone
        self.table.setColumnWidth(2, 150)  # Email
        self.table.setColumnWidth(3, 160)  # Address
        self.table.setColumnWidth(4, 120)  # Credit Limit
        self.table.setColumnWidth(5, 90)   # Type
        self.table.setColumnWidth(6, 100)  # Actions
        self.table.horizontalHeader().setStretchLastSection(False)
        self.table.verticalHeader().setDefaultSectionSize(40)
        layout.addWidget(self.table)
        
        # Add initial empty row
        self.add_empty_rows(1)

        # Buttons
        button_layout = QHBoxLayout()
        
        add_row_btn = QPushButton("+ Add Row")
        add_row_btn.setStyleSheet(
            "QPushButton { background-color: #FF9800; color: white; padding: 8px 20px; border-radius: 5px; font-weight: bold; }"
            "QPushButton:hover { background-color: #F57C00; }"
        )
        add_row_btn.clicked.connect(lambda: self.add_empty_rows(1))
        button_layout.addWidget(add_row_btn)
        
        save_btn = QPushButton("Save All")
        save_btn.setStyleSheet(
            "QPushButton { background-color: #4CAF50; color: white; padding: 8px 20px; border-radius: 5px; font-weight: bold; }"
            "QPushButton:hover { background-color: #45a049; }"
        )
        save_btn.clicked.connect(self.save_all_customers)
        button_layout.addWidget(save_btn)
        
        view_btn = QPushButton("View Records")
        view_btn.setStyleSheet(
            "QPushButton { background-color: #2196F3; color: white; padding: 8px 20px; border-radius: 5px; font-weight: bold; }"
            "QPushButton:hover { background-color: #0b7dda; }"
        )
        view_btn.clicked.connect(self.view_customers_list)
        button_layout.addWidget(view_btn)
        
        close_btn = QPushButton("Close")
        close_btn.setStyleSheet(
            "QPushButton { background-color: #f44336; color: white; padding: 8px 20px; border-radius: 5px; font-weight: bold; }"
            "QPushButton:hover { background-color: #da190b; }"
        )
        close_btn.clicked.connect(self.reject)
        button_layout.addWidget(close_btn)
        
        layout.addLayout(button_layout)
        self.setLayout(layout)

    def add_empty_rows(self, count=1):
        """Add empty rows to table."""
        for _ in range(count):
            row = self.table.rowCount()
            self.table.insertRow(row)
            
            # Name cell
            self.table.setItem(row, 0, QTableWidgetItem(""))
            
            # Phone cell
            self.table.setItem(row, 1, QTableWidgetItem(""))
            
            # Email cell
            self.table.setItem(row, 2, QTableWidgetItem(""))
            
            # Address cell
            self.table.setItem(row, 3, QTableWidgetItem(""))
            
            # Credit Limit cell
            self.table.setItem(row, 4, QTableWidgetItem(""))
            
            # Type combo
            type_combo = QComboBox()
            type_combo.addItems(self.customer_types)
            self.table.setCellWidget(row, 5, type_combo)
            # Delete button
            delete_btn = QPushButton("Delete")
            delete_btn.setStyleSheet(
                "QPushButton { background-color: #f44336; color: white; padding: 4px 10px; border-radius: 3px; font-size: 11px; }"
                "QPushButton:hover { background-color: #da190b; }"
            )
            delete_btn.clicked.connect(lambda: self.delete_row(row))
            self.table.setCellWidget(row, 6, delete_btn)

    def delete_row(self, row):
        """Delete a row from the table."""
        self.table.removeRow(row)

    def save_all_customers(self):
        """Save all non-empty customers to database."""
        try:
            errors = {}
            saved_rows = []
            
            for row in range(self.table.rowCount()):
                # Get row data
                name_item = self.table.item(row, 0)
                phone_item = self.table.item(row, 1)
                email_item = self.table.item(row, 2)
                address_item = self.table.item(row, 3)
                credit_item = self.table.item(row, 4)
                type_widget = self.table.cellWidget(row, 5)
                
                name = name_item.text().strip() if name_item else ""
                phone = phone_item.text().strip() if phone_item else ""
                email = email_item.text().strip() if email_item else ""
                address = address_item.text().strip() if address_item else ""
                credit_text = credit_item.text().strip() if credit_item else ""
                customer_type = type_widget.currentText() if type_widget else ""
                
                # Skip empty rows
                if not name and not phone:
                    continue
                
                # Validate required fields
                if not name:
                    errors[row + 1] = "Customer Name is required"
                    continue
                
                if not phone:
                    errors[row + 1] = "Phone Number is required"
                    continue
                
                # Try to convert credit limit to float
                try:
                    credit_limit = float(credit_text) if credit_text else 0.0
                except ValueError:
                    errors[row + 1] = "Credit Limit must be a number"
                    continue
                
                # Create customer
                try:
                    import uuid
                    customer_id = str(uuid.uuid4())
                    data = {
                        'id': customer_id,
                        'name': name,
                        'phone': phone,
                        'email': email,
                        'address': address,
                        'credit_limit': credit_limit,
                        'outstanding_balance': 0,
                        'customer_type': customer_type.lower(),
                        'status': 'active'
                    }
                    
                    success, msg = self.db_service.create_document('customers', customer_id, data)
                    
                    if success:
                        saved_rows.append(row)
                    else:
                        errors[row + 1] = msg
                except Exception as e:
                    errors[row + 1] = str(e)
            
            # Display results
            if errors:
                error_msg = "Errors occurred:\n\n"
                for row, error in errors.items():
                    error_msg += f"Row {row}: {error}\n"
                if saved_rows:
                    error_msg += f"\n{len(saved_rows)} customer(s) saved successfully."
                QMessageBox.warning(self, "Validation Errors", error_msg)
            else:
                QMessageBox.information(self, "Success", f"All {len(saved_rows)} customer(s) saved successfully!")
                # Reset grid to 1 empty row
                self.table.setRowCount(0)
                self.add_empty_rows(1)
                self.view_customers_list()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"An error occurred: {str(e)}")

    def view_customers_list(self):
        """View customers records in grid."""
        try:
            customers_data = self.db_service.list_documents('customers')
            columns = ["Name", "Phone", "Email", "Address", "Credit Limit (Rs)", "Type"]
            data = []
            
            for customer in customers_data:
                data.append([
                    customer.get('name', ''),
                    customer.get('phone', ''),
                    customer.get('email', ''),
                    customer.get('address', ''),
                    f"{customer.get('credit_limit', 0):.2f}",
                    customer.get('customer_type', '')
                ])
            
            if not data:
                data = [["No customers found", "", "", "", "", ""]]
            
            dialog = DataViewDialog("Customers", columns, data, self)
            dialog.exec_()
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Failed to load customers: {str(e)}")


class RecordPurchaseDialog(QDialog):
    """Dialog for recording multiple fuel purchases with grid interface."""

    def __init__(self, fuel_service, tank_service, db_service, account_head_service, parent=None):
        """Initialize dialog."""
        super().__init__(parent)
        self.fuel_service = fuel_service
        self.tank_service = tank_service
        self.db_service = db_service
        self.account_head_service = account_head_service
        self.tanks = []
        self.account_heads = []
        self.account_head_balances = {}  # Store current balances for account heads
        
        self.setWindowTitle("Record Purchases")
        self.resize(1180, 650)
        self._center_on_screen()
        self.load_tanks()
        self.load_account_heads()
        self.init_ui()

    def _center_on_screen(self):
        """Center dialog on screen."""
        from PyQt5.QtWidgets import QDesktopWidget
        screen = QDesktopWidget().screenGeometry()
        size = self.geometry()
        self.move((screen.width() - size.width()) // 2, (screen.height() - size.height()) // 2)

    def init_ui(self):
        """Initialize UI components."""
        layout = QVBoxLayout()
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(12)

        # Title label
        title_label = QLabel("Record Purchases")
        title_label.setFont(QFont("Arial", 14, QFont.Bold))
        layout.addWidget(title_label)

        # Create table widget
        self.table = QTableWidget()
        self.table.setColumnCount(7)
        self.table.setHorizontalHeaderLabels(["Tank", "Supplier Name", "Quantity (L)", "Unit Cost (Rs)", "Total (Rs)", "Account Head", "Invoice Number", "Actions"])
        self.table.setColumnCount(8)
        self.table.setAlternatingRowColors(True)
        self.table.setStyleSheet(
            "QTableWidget { background-color: white; alternate-background-color: #f9f9f9; border: 1px solid #ddd; }"
            "QHeaderView::section { background-color: #2196F3; color: white; padding: 5px; border: none; font-weight: bold; }"
            "QTableWidget::item { padding: 5px; border-bottom: 1px solid #e0e0e0; }"
        )
        # Set column widths - Supplier wider, numeric fields narrower
        self.table.setColumnCount(8)
        self.table.setColumnWidth(0, 110)  # Tank
        self.table.setColumnWidth(1, 130)  # Supplier Name
        self.table.setColumnWidth(2, 100)  # Quantity
        self.table.setColumnWidth(3, 100)  # Unit Cost
        self.table.setColumnWidth(4, 100)  # Total
        self.table.setColumnWidth(5, 160)  # Account Head
        self.table.setColumnWidth(6, 110)  # Invoice Number
        self.table.setColumnWidth(7, 100)  # Actions
        self.table.horizontalHeader().setStretchLastSection(False)
        self.table.verticalHeader().setDefaultSectionSize(40)
        layout.addWidget(self.table)
        
        # Add initial empty row
        self.add_empty_rows(1)

        # Buttons
        button_layout = QHBoxLayout()
        
        add_row_btn = QPushButton("+ Add Row")
        add_row_btn.setStyleSheet(
            "QPushButton { background-color: #FF9800; color: white; padding: 8px 20px; border-radius: 5px; font-weight: bold; }"
            "QPushButton:hover { background-color: #F57C00; }"
        )
        add_row_btn.clicked.connect(lambda: self.add_empty_rows(1))
        button_layout.addWidget(add_row_btn)
        
        save_btn = QPushButton("Save All")
        save_btn.setStyleSheet(
            "QPushButton { background-color: #4CAF50; color: white; padding: 8px 20px; border-radius: 5px; font-weight: bold; }"
            "QPushButton:hover { background-color: #45a049; }"
        )
        save_btn.clicked.connect(self.save_all_purchases)
        button_layout.addWidget(save_btn)
        
        view_btn = QPushButton("View Records")
        view_btn.setStyleSheet(
            "QPushButton { background-color: #2196F3; color: white; padding: 8px 20px; border-radius: 5px; font-weight: bold; }"
            "QPushButton:hover { background-color: #0b7dda; }"
        )
        view_btn.clicked.connect(self.view_purchases)
        button_layout.addWidget(view_btn)
        
        close_btn = QPushButton("Close")
        close_btn.setStyleSheet(
            "QPushButton { background-color: #f44336; color: white; padding: 8px 20px; border-radius: 5px; font-weight: bold; }"
            "QPushButton:hover { background-color: #da190b; }"
        )
        close_btn.clicked.connect(self.reject)
        button_layout.addWidget(close_btn)
        
        layout.addLayout(button_layout)
        self.setLayout(layout)
        
        # Connect signal for calculations
        self.table.itemChanged.connect(self.on_cell_changed)

    def load_tanks(self):
        """Load tanks into memory."""
        try:
            self.tanks = self.tank_service.list_tanks()
        except Exception as e:
            print(f"Error loading tanks: {str(e)}")

    def load_account_heads(self):
        """Load account heads from database."""
        try:
            self.account_heads = self.account_head_service.list_account_heads(active_only=True)
            # Initialize balances - in a real scenario, these would come from account balances
            for head in self.account_heads:
                head_id = head.get('id', '')
                # Get current balance from purchases/expenses for this account head
                self.account_head_balances[head_id] = self._calculate_account_head_balance(head_id)
        except Exception as e:
            print(f"Error loading account heads: {str(e)}")
            self.account_heads = []

    def _calculate_account_head_balance(self, head_id: str) -> float:
        """
        Calculate current balance for an account head.
        This would sum up all purchases/expenses for this account head.
        """
        try:
            purchases = self.db_service.list_documents('purchases')
            balance = 0.0
            for purchase in purchases:
                if purchase.get('account_head_id') == head_id:
                    balance += float(purchase.get('total_cost', 0))
            return balance
        except Exception:
            return 0.0

    def add_empty_rows(self, count=1):
        """Add empty rows to table."""
        for _ in range(count):
            row = self.table.rowCount()
            self.table.insertRow(row)
            
            # Tank combo
            tank_combo = QComboBox()
            tank_combo.addItem("-- Select Tank --", "")
            for tank in self.tanks:
                tank_combo.addItem(f"{tank.name} ({tank.current_stock:.2f}L)", tank.id)
            self.table.setCellWidget(row, 0, tank_combo)
            
            # Supplier Name cell
            self.table.setItem(row, 1, QTableWidgetItem(""))
            
            # Quantity cell
            self.table.setItem(row, 2, QTableWidgetItem(""))
            
            # Unit Cost cell
            self.table.setItem(row, 3, QTableWidgetItem(""))
            
            # Total cell (read-only, calculated)
            total_item = QTableWidgetItem("0.00")
            total_item.setFlags(total_item.flags() & ~Qt.ItemIsEditable)
            self.table.setItem(row, 4, total_item)
            
            # Account Head combo (LOV) - Show only account head names from database
            account_head_combo = QComboBox()
            account_head_combo.addItem("-- Select Account Head --", "")
            for head in self.account_heads:
                head_id = head.get('id', '')
                head_name = head.get('name', '')
                # Display: Account Head Name only
                account_head_combo.addItem(head_name, head_id)
            
            # Connect signal to update projected balance on selection
            account_head_combo.currentIndexChanged.connect(lambda idx, r=row: self.on_account_head_changed(r))
            self.table.setCellWidget(row, 5, account_head_combo)
            
            # Invoice Number cell
            self.table.setItem(row, 6, QTableWidgetItem(""))
            # Delete button
            delete_btn = QPushButton("Delete")
            delete_btn.setStyleSheet(
                "QPushButton { background-color: #f44336; color: white; padding: 4px 10px; border-radius: 3px; font-size: 11px; }"
                "QPushButton:hover { background-color: #da190b; }"
            )
            delete_btn.clicked.connect(lambda: self.delete_row(row))
            self.table.setCellWidget(row, 7, delete_btn)

    def delete_row(self, row):
        """Delete a row from the table."""
        self.table.removeRow(row)

    def on_account_head_changed(self, row):
        """Handle account head selection changes and display projected balance."""
        account_head_combo = self.table.cellWidget(row, 5)
        if not account_head_combo:
            return
        
        head_id = account_head_combo.currentData()
        if not head_id:
            return
        
        # Get current and projected balance
        current_balance = self.account_head_balances.get(head_id, 0.0)
        total_item = self.table.item(row, 4)
        total = float(total_item.text()) if total_item else 0.0
        projected_balance = current_balance + total
        
        # Update the combo display to show projected balance
        # This shows real-time impact when amount is entered
        current_text = account_head_combo.currentText()
        if "Projected" in current_text:
            # Already updated, just refresh the projected value
            base_text = current_text.split(" | Projected")[0]
        else:
            base_text = current_text
        
        updated_text = f"{base_text} | Projected: Rs {projected_balance:.2f}"
        account_head_combo.setItemText(account_head_combo.currentIndex(), updated_text)

    def on_cell_changed(self, item):
        """Handle cell changes for calculations."""
        self.table.itemChanged.disconnect(self.on_cell_changed)
        
        # Calculate totals for all rows and update projected balances
        for row in range(self.table.rowCount()):
            qty_item = self.table.item(row, 2)
            cost_item = self.table.item(row, 3)
            total_item = self.table.item(row, 4)
            
            try:
                qty = float(qty_item.text()) if qty_item and qty_item.text() else 0
                cost = float(cost_item.text()) if cost_item and cost_item.text() else 0
                total = qty * cost
                if total_item:
                    total_item.setText(f"{total:.2f}")
                    # Update projected balance display
                    self.on_account_head_changed(row)
            except ValueError:
                pass
        
        self.table.itemChanged.connect(self.on_cell_changed)

    def save_all_purchases(self):
        """Save all non-empty purchases to database."""
        try:
            errors = {}
            saved_rows = []
            
            for row in range(self.table.rowCount()):
                # Get row data
                tank_combo = self.table.cellWidget(row, 0)
                supplier_item = self.table.item(row, 1)
                qty_item = self.table.item(row, 2)
                cost_item = self.table.item(row, 3)
                account_head_combo = self.table.cellWidget(row, 5)
                invoice_item = self.table.item(row, 6)
                
                tank_id = tank_combo.currentData() if tank_combo else ""
                supplier = supplier_item.text().strip() if supplier_item else ""
                qty_text = qty_item.text().strip() if qty_item else ""
                cost_text = cost_item.text().strip() if cost_item else ""
                account_head_id = account_head_combo.currentData() if account_head_combo else ""
                invoice = invoice_item.text().strip() if invoice_item else ""
                
                # Skip empty rows
                if not tank_id and not supplier:
                    continue
                
                # Validate required fields
                if not tank_id:
                    errors[row + 1] = "Tank is required"
                    continue
                
                if not supplier:
                    errors[row + 1] = "Supplier Name is required"
                    continue
                
                if not qty_text:
                    errors[row + 1] = "Quantity is required"
                    continue
                
                if not cost_text:
                    errors[row + 1] = "Unit Cost is required"
                    continue
                
                if not account_head_id or account_head_id == "":
                    errors[row + 1] = "Account Head is required"
                    continue
                
                # Try to convert to numbers
                try:
                    quantity = float(qty_text)
                    unit_cost = float(cost_text)
                except ValueError:
                    errors[row + 1] = "Quantity and Unit Cost must be numbers"
                    continue
                
                if quantity <= 0:
                    errors[row + 1] = "Quantity must be greater than 0"
                    continue
                
                # Get account head details for payment method derivation
                account_head_data = None
                for head in self.account_heads:
                    if head.get('id') == account_head_id:
                        account_head_data = head
                        break
                
                payment_method = account_head_data.get('head_type', 'Other') if account_head_data else 'Other'
                account_head_name = account_head_data.get('name', '') if account_head_data else ''
                
                # Create purchase record
                try:
                    import uuid
                    purchase_id = str(uuid.uuid4())
                    total_cost = quantity * unit_cost
                    
                    data = {
                        'id': purchase_id,
                        'tank_id': tank_id,
                        'supplier_name': supplier,
                        'quantity': quantity,
                        'unit_cost': unit_cost,
                        'total_cost': total_cost,
                        'account_head_id': account_head_id,
                        'account_head_name': account_head_name,
                        'payment_method': payment_method,  # Derived from account head type
                        'invoice_number': invoice,
                        'purchase_date': datetime.now().isoformat(),
                        'status': 'completed'
                    }

                    success, msg = self.db_service.create_document('purchases', purchase_id, data)

                    if success:
                        saved_rows.append(row)
                        # Update account head balance in memory
                        self.account_head_balances[account_head_id] = self.account_head_balances.get(account_head_id, 0.0) + total_cost
                    else:
                        errors[row + 1] = msg
                except Exception as e:
                    errors[row + 1] = str(e)
            
            # Display results
            if errors:
                error_msg = "Errors occurred:\n\n"
                for row, error in errors.items():
                    error_msg += f"Row {row}: {error}\n"
                if saved_rows:
                    error_msg += f"\n{len(saved_rows)} purchase(s) saved successfully."
                QMessageBox.warning(self, "Validation Errors", error_msg)
            else:
                QMessageBox.information(self, "Success", f"All {len(saved_rows)} purchase(s) saved successfully!")
                # Reset grid to 1 empty row
                self.table.setRowCount(0)
                self.add_empty_rows(1)
                self.view_purchases()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"An error occurred: {str(e)}")

    def view_purchases(self):
        """View purchase records in grid."""
        try:
            purchases_data = self.db_service.list_documents('purchases')
            # Build lookup map for tank names
            tanks = self.tank_service.list_tanks()
            tank_map = {t.id: t.name for t in tanks}
            
            columns = ["Tank", "Supplier", "Quantity (L)", "Unit Cost", "Total (Rs)", "Account Head", "Invoice", "Date"]
            data = []
            
            for purchase in purchases_data:
                tank_id = purchase.get('tank_id', '')
                tank_name = tank_map.get(tank_id, tank_id)
                # Get date from 'purchase_date' or 'timestamp' field
                date_str = purchase.get('purchase_date', purchase.get('timestamp', ''))
                date_display = date_str[:10] if date_str else ''
                data.append([
                    tank_name,
                    purchase.get('supplier_name', ''),
                    f"{purchase.get('quantity', 0):.2f}",
                    f"{purchase.get('unit_cost', 0):.2f}",
                    f"{purchase.get('total_cost', 0):.2f}",
                    purchase.get('account_head_name', ''),
                    purchase.get('invoice_number', ''),
                    date_display
                ])
            
            if not data:
                data = [["No purchase records found", "", "", "", "", "", "", ""]]
            
            dialog = DataViewDialog("Purchase Records", columns, data, self)
            dialog.exec_()
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Failed to load purchases: {str(e)}")


class UpdateExchangeRateDialog(QDialog):
    """Dialog for updating exchange rates."""

    def __init__(self, db_service, parent=None):
        """Initialize dialog."""
        super().__init__(parent)
        self.db_service = db_service
        
        self.setWindowTitle("Update Exchange Rate")
        self.resize(500, 300)
        self._center_on_screen()
        self.init_ui()

    def _center_on_screen(self):
        """Center dialog on screen."""
        from PyQt5.QtWidgets import QDesktopWidget
        screen = QDesktopWidget().screenGeometry()
        size = self.geometry()
        self.move((screen.width() - size.width()) // 2, (screen.height() - size.height()) // 2)

    def init_ui(self):
        """Initialize UI components."""
        layout = QFormLayout()
        layout.setSpacing(12)
        layout.setContentsMargins(20, 20, 20, 20)

        # Currency From
        from_label = QLabel("From Currency:")
        self.from_combo = QComboBox()
        self.from_combo.addItems(["USD", "EUR", "GBP", "AED", "SAR"])
        layout.addRow(from_label, self.from_combo)

        # Currency To
        to_label = QLabel("To Currency:")
        self.to_combo = QComboBox()
        self.to_combo.addItems(["PKR", "USD", "EUR", "GBP", "AED"])
        self.to_combo.setCurrentIndex(0)
        layout.addRow(to_label, self.to_combo)

        # Exchange Rate
        rate_label = QLabel("Exchange Rate:")
        self.rate_input = QDoubleSpinBox()
        self.rate_input.setMinimum(0)
        self.rate_input.setMaximum(999999)
        self.rate_input.setDecimals(4)
        layout.addRow(rate_label, self.rate_input)

        # Effective Date
        date_label = QLabel("Effective Date:")
        self.date_input = QLineEdit()
        self.date_input.setText(datetime.now().strftime("%Y-%m-%d"))
        self.date_input.setReadOnly(True)
        layout.addRow(date_label, self.date_input)

        # Buttons
        button_layout = QHBoxLayout()
        
        update_btn = QPushButton("Update Rate")
        update_btn.setStyleSheet(
            "QPushButton { background-color: #4CAF50; color: white; padding: 8px 20px; border-radius: 5px; }"
            "QPushButton:hover { background-color: #45a049; }"
        )
        update_btn.clicked.connect(self.update_rate)
        button_layout.addWidget(update_btn)
        
        view_btn = QPushButton("View Records")
        view_btn.setStyleSheet(
            "QPushButton { background-color: #2196F3; color: white; padding: 8px 20px; border-radius: 5px; }"
            "QPushButton:hover { background-color: #0b7dda; }"
        )
        view_btn.clicked.connect(self.view_rates)
        button_layout.addWidget(view_btn)
        
        cancel_btn = QPushButton("Cancel")
        cancel_btn.setStyleSheet(
            "QPushButton { background-color: #f44336; color: white; padding: 8px 20px; border-radius: 5px; }"
            "QPushButton:hover { background-color: #da190b; }"
        )
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(cancel_btn)
        
        layout.addRow(button_layout)
        self.setLayout(layout)

    def update_rate(self):
        """Update exchange rate."""
        try:
            from_currency = self.from_combo.currentText()
            to_currency = self.to_combo.currentText()
            rate = self.rate_input.value()

            if rate <= 0:
                QMessageBox.warning(self, "Error", "Exchange rate must be greater than 0")
                return

            # Create exchange rate record
            import uuid
            rate_id = str(uuid.uuid4())
            
            data = {
                'id': rate_id,
                'from_currency': from_currency,
                'to_currency': to_currency,
                'rate': rate,
                'effective_date': datetime.now().isoformat(),
                'status': 'active'
            }

            success, msg = self.db_service.create_document('exchange_rates', rate_id, data)

            if success:
                QMessageBox.information(self, "Success", f"Exchange rate updated!\n1 {from_currency} = {rate:,.4f} {to_currency}")
                self.accept()
            else:
                QMessageBox.critical(self, "Error", f"Failed to update rate: {msg}")

        except Exception as e:
            QMessageBox.critical(self, "Error", f"An error occurred: {str(e)}")

    def view_rates(self):
        """View exchange rates in grid."""
        try:
            rates_data = self.db_service.list_documents('exchange_rates')
            columns = ["From Currency", "To Currency", "Rate", "Effective Date"]
            data = []
            
            for rate in rates_data:
                data.append([
                    rate.get('from_currency', ''),
                    rate.get('to_currency', ''),
                    f"{rate.get('rate', 0):.4f}",
                    rate.get('effective_date', '')
                ])
            
            if not data:
                data = [["No exchange rates found", "", "", ""]]
            
            dialog = DataViewDialog("Exchange Rates", columns, data, self)
            dialog.exec_()
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Failed to load exchange rates: {str(e)}")


class RecordExpenseDialog(QDialog):
    """Dialog for recording multiple expenses with grid interface."""

    def __init__(self, db_service, payment_methods=None, parent=None):
        """Initialize dialog."""
        super().__init__(parent)
        self.db_service = db_service
        self.expense_categories = [
            "Utilities",
            "Maintenance",
            "Salaries",
            "Transportation",
            "Office Supplies",
            "Insurance",
            "Equipment",
            "Other"
        ]
        self.payment_methods = payment_methods if payment_methods is not None else []
        
        # Get account heads with expense nature
        all_account_heads = self.db_service.list_documents('account_heads')
        # Filter to only expense account heads
        self.account_heads = [acc for acc in all_account_heads if acc.get('head_type', '').lower() == 'expense']
        self.account_head_map = {acc.get('id', ''): acc.get('name', '') for acc in self.account_heads}
        self.account_head_names = [acc.get('name', '') for acc in self.account_heads]
        
        self.setWindowTitle("Record Expenses")
        self.resize(1000, 650)
        self._center_on_screen()
        self.init_ui()

    def _center_on_screen(self):
        """Center dialog on screen."""
        from PyQt5.QtWidgets import QDesktopWidget
        screen = QDesktopWidget().screenGeometry()
        size = self.geometry()
        self.move((screen.width() - size.width()) // 2, (screen.height() - size.height()) // 2)

    def init_ui(self):
        """Initialize UI components."""
        layout = QVBoxLayout()
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(12)

        # Title label
        title_label = QLabel("Record Expenses")
        title_label.setFont(QFont("Arial", 14, QFont.Bold))
        layout.addWidget(title_label)

        # Create table widget
        self.table = QTableWidget()
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels(["Category", "Description", "Amount (Rs)", "Account Head", "Reference No.", "Notes", "Actions"])
        self.table.setColumnCount(7)
        self.table.setAlternatingRowColors(True)
        self.table.setStyleSheet(
            "QTableWidget { background-color: white; alternate-background-color: #f9f9f9; border: 1px solid #ddd; }"
            "QHeaderView::section { background-color: #2196F3; color: white; padding: 5px; border: none; font-weight: bold; }"
            "QTableWidget::item { padding: 5px; border-bottom: 1px solid #e0e0e0; }"
        )
        # Set column widths
        self.table.setColumnCount(7)
        self.table.setColumnWidth(0, 100)  # Category
        self.table.setColumnWidth(1, 140)  # Description
        self.table.setColumnWidth(2, 100)  # Amount
        self.table.setColumnWidth(3, 160)  # Account Head
        self.table.setColumnWidth(4, 100)  # Reference No.
        self.table.setColumnWidth(5, 140)  # Notes
        self.table.setColumnWidth(6, 100)  # Actions
        self.table.horizontalHeader().setStretchLastSection(False)
        self.table.verticalHeader().setDefaultSectionSize(40)
        layout.addWidget(self.table)
        
        # Add initial empty row
        self.add_empty_rows(1)

        # Buttons
        button_layout = QHBoxLayout()
        
        add_row_btn = QPushButton("+ Add Row")
        add_row_btn.setStyleSheet(
            "QPushButton { background-color: #FF9800; color: white; padding: 8px 20px; border-radius: 5px; font-weight: bold; }"
            "QPushButton:hover { background-color: #F57C00; }"
        )
        add_row_btn.clicked.connect(lambda: self.add_empty_rows(1))
        button_layout.addWidget(add_row_btn)
        
        save_btn = QPushButton("Save All")
        save_btn.setStyleSheet(
            "QPushButton { background-color: #4CAF50; color: white; padding: 8px 20px; border-radius: 5px; font-weight: bold; }"
            "QPushButton:hover { background-color: #45a049; }"
        )
        save_btn.clicked.connect(self.save_all_expenses)
        button_layout.addWidget(save_btn)
        
        view_btn = QPushButton("View Records")
        view_btn.setStyleSheet(
            "QPushButton { background-color: #2196F3; color: white; padding: 8px 20px; border-radius: 5px; font-weight: bold; }"
            "QPushButton:hover { background-color: #0b7dda; }"
        )
        view_btn.clicked.connect(self.view_expenses_list)
        button_layout.addWidget(view_btn)
        
        close_btn = QPushButton("Close")
        close_btn.setStyleSheet(
            "QPushButton { background-color: #f44336; color: white; padding: 8px 20px; border-radius: 5px; font-weight: bold; }"
            "QPushButton:hover { background-color: #da190b; }"
        )
        close_btn.clicked.connect(self.reject)
        button_layout.addWidget(close_btn)
        
        layout.addLayout(button_layout)
        self.setLayout(layout)

    def add_empty_rows(self, count=1):
        """Add empty rows to table."""
        for _ in range(count):
            row = self.table.rowCount()
            self.table.insertRow(row)
            
            # Category combo
            category_combo = QComboBox()
            category_combo.addItems(self.expense_categories)
            self.table.setCellWidget(row, 0, category_combo)
            
            # Description cell
            self.table.setItem(row, 1, QTableWidgetItem(""))
            
            # Amount cell
            self.table.setItem(row, 2, QTableWidgetItem(""))
            
            # Account Head combo
            account_head_combo = QComboBox()
            account_head_combo.addItems(self.account_head_names)
            self.table.setCellWidget(row, 3, account_head_combo)
            
            # Reference Number cell
            self.table.setItem(row, 4, QTableWidgetItem(""))
            
            # Notes cell
            self.table.setItem(row, 5, QTableWidgetItem(""))
            # Delete button
            delete_btn = QPushButton("Delete")
            delete_btn.setStyleSheet(
                "QPushButton { background-color: #f44336; color: white; padding: 4px 10px; border-radius: 3px; font-size: 11px; }"
                "QPushButton:hover { background-color: #da190b; }"
            )
            delete_btn.clicked.connect(lambda: self.delete_row(row))
            self.table.setCellWidget(row, 6, delete_btn)

    def delete_row(self, row):
        """Delete a row from the table."""
        self.table.removeRow(row)

    def save_all_expenses(self):
        """Save all non-empty expenses to database."""
        try:
            import uuid
            errors = {}
            saved_rows = []
            
            for row in range(self.table.rowCount()):
                # Get row data
                category_combo = self.table.cellWidget(row, 0)
                desc_item = self.table.item(row, 1)
                amount_item = self.table.item(row, 2)
                account_head_combo = self.table.cellWidget(row, 3)
                ref_item = self.table.item(row, 4)
                notes_item = self.table.item(row, 5)
                
                category = category_combo.currentText() if category_combo else ""
                description = desc_item.text().strip() if desc_item else ""
                amount_text = amount_item.text().strip() if amount_item else ""
                account_head_name = account_head_combo.currentText() if account_head_combo else ""
                reference = ref_item.text().strip() if ref_item else ""
                notes = notes_item.text().strip() if notes_item else ""
                
                # Skip empty rows
                if not description and not amount_text:
                    continue
                
                # Validate required fields
                if not description:
                    errors[row + 1] = "Description is required"
                    continue
                
                if not amount_text:
                    errors[row + 1] = "Amount is required"
                    continue
                
                try:
                    amount = float(amount_text)
                    if amount <= 0:
                        errors[row + 1] = "Amount must be greater than 0"
                        continue
                except ValueError:
                    errors[row + 1] = "Invalid amount format"
                    continue
                
                # Get account head ID from name
                account_head_id = None
                for acc in self.account_heads:
                    if acc.get('name', '') == account_head_name:
                        account_head_id = acc.get('id', '')
                        break
                
                if not account_head_id:
                    errors[row + 1] = "Account Head must be selected"
                    continue
                
                # Create expense record
                try:
                    expense_id = str(uuid.uuid4())
                    
                    data = {
                        'id': expense_id,
                        'category': category,
                        'description': description,
                        'amount': amount,
                        'account_head_id': account_head_id,
                        'account_head_name': account_head_name,
                        'reference_number': reference,
                        'notes': notes,
                        'expense_date': datetime.now().isoformat(),
                        'status': 'recorded'
                    }

                    success, msg = self.db_service.create_document('expenses', expense_id, data)

                    if success:
                        saved_rows.append(row)
                    else:
                        errors[row + 1] = msg
                except Exception as e:
                    errors[row + 1] = str(e)
            
            # Display results
            if errors:
                error_msg = "Errors occurred:\n\n"
                for row, error in errors.items():
                    error_msg += f"Row {row}: {error}\n"
                if saved_rows:
                    error_msg += f"\n{len(saved_rows)} expense(s) saved successfully."
                QMessageBox.warning(self, "Validation Errors", error_msg)
            else:
                QMessageBox.information(self, "Success", f"All {len(saved_rows)} expense(s) saved successfully!")
                # Reset grid to 1 empty row
                self.table.setRowCount(0)
                self.add_empty_rows(1)
                self.view_expenses_list()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"An error occurred: {str(e)}")

    def view_expenses_list(self):
        """View expenses records in grid."""
        try:
            expenses_data = self.db_service.list_documents('expenses')
            columns = ["Category", "Description", "Amount (Rs)", "Account Head", "Reference", "Date"]
            data = []
            
            for expense in expenses_data:
                # Get date from 'expense_date' or 'timestamp' field
                date_str = expense.get('expense_date', expense.get('timestamp', ''))
                date_display = date_str[:10] if date_str else ''
                data.append([
                    expense.get('category', ''),
                    expense.get('description', ''),
                    f"{expense.get('amount', 0):.2f}",
                    expense.get('account_head_name', ''),
                    expense.get('reference_number', ''),
                    date_display
                ])
            
            if not data:
                data = [["No expenses found", "", "", "", "", ""]]
            
            dialog = DataViewDialog("Expenses", columns, data, self)
            dialog.exec_()
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Failed to load expenses: {str(e)}")
