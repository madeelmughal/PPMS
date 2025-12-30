"""
Dashboard Screen - Main application dashboard
"""

from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QGridLayout, QFrame, QScrollArea, QMenuBar, QMenu, QDialog, QLineEdit,
    QDoubleSpinBox, QSpinBox, QComboBox, QMessageBox, QFormLayout, QTableWidget,
    QTableWidgetItem
)
from PyQt5.QtCore import Qt, QTimer, pyqtSignal
from PyQt5.QtGui import QFont
from src.services.database_service import (
    FuelService, TankService, SalesService, DatabaseService, NozzleService, CustomerService
)
from src.config.firebase_config import AppConfig
from datetime import datetime

import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import numpy as np


class DataViewDialog(QDialog):
    """Professional data view dialog with table grid."""

    def __init__(self, title, columns, data, parent=None):
        """Initialize data view dialog."""
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setGeometry(100, 100, 1000, 600)
        self.setStyleSheet(
            "QDialog { background-color: #f5f5f5; }"
            "QTableWidget { background-color: white; alternate-background-color: #f9f9f9; border: 1px solid #ddd; }"
            "QHeaderView::section { background-color: #2196F3; color: white; padding: 5px; border: none; font-weight: bold; }"
            "QTableWidget::item { padding: 5px; border-bottom: 1px solid #e0e0e0; }"
            "QPushButton { background-color: #4CAF50; color: white; padding: 8px 20px; border-radius: 5px; font-weight: bold; }"
            "QPushButton:hover { background-color: #45a049; }"
        )
        
        # Layout
        layout = QVBoxLayout()
        
        # Title label
        title_label = QLabel(title)
        title_label.setFont(QFont("Arial", 14, QFont.Bold))
        layout.addWidget(title_label)
        
        # Create table
        self.table = QTableWidget()
        self.table.setColumnCount(len(columns))
        self.table.setHorizontalHeaderLabels(columns)
        self.table.setAlternatingRowColors(True)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.horizontalHeader().setStretchLastSection(True)
        
        # Add data to table
        self.table.setRowCount(len(data))
        for row_idx, row_data in enumerate(data):
            for col_idx, cell_value in enumerate(row_data):
                item = QTableWidgetItem(str(cell_value))
                item.setFlags(item.flags() & ~Qt.ItemIsEditable)
                self.table.setItem(row_idx, col_idx, item)
        
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
        
        # KPI card label references for dynamic updates
        self.kpi_labels = {}

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
        
        # Data Entry Menu
        daily_menu = menubar.addMenu("Data Entry")
        daily_menu.addAction("Record Fuel Sale", self.record_sale_dialog)
        daily_menu.addAction("Record Fuel Purchase", self.record_purchase_dialog)
        daily_menu.addAction("Update Exchange Rate", self.update_exchange_rate_dialog)
        daily_menu.addAction("Record Expense", self.record_expense_dialog)
        daily_menu.addSeparator()
        daily_menu.addAction("Add New Customer", self.add_customer_dialog)
        daily_menu.addAction("Record Customer Payment", self.customer_payments_dialog)
        daily_menu.addSeparator()
        daily_menu.addAction("View Daily Summary", self.view_daily_summary)
        daily_menu.addAction("Daily Transactions Report", self.daily_transactions_report)
        
        # Setup Menu (One-time settings)
        setup_menu = menubar.addMenu("Setup")
        setup_menu.addAction("Add Fuel Types", self.add_fuel_type_settings)
        setup_menu.addAction("Add Tanks", self.add_tank)
        setup_menu.addAction("Add Nozzles", self.add_nozzles_settings)
        setup_menu.addAction("Add Account Heads", self.add_account_heads)
        setup_menu.addSeparator()
        setup_menu.addAction("Configure System", self.configure_system)
        
        # Inventory Menu
        inventory_menu = menubar.addMenu("Inventory")
        inventory_menu.addAction("Update Stock Levels", self.update_stock_levels)
        inventory_menu.addAction("View Inventory Report", self.view_inventory_report)
        inventory_menu.addSeparator()
        inventory_menu.addAction("Manage Nozzles", self.manage_nozzles)
        
        # View Menu
        view_menu = menubar.addMenu("View")
        view_menu.addAction("View Sales Records", self.view_sales_records)
        view_menu.addAction("View Purchase Records", self.view_purchase_records)
        view_menu.addAction("View Customers", self.view_customers)
        view_menu.addAction("View Expenses", self.view_expenses)
        view_menu.addSeparator()
        view_menu.addAction("View Fuel Types", self.view_fuel_types)
        view_menu.addAction("View Tanks", self.view_tanks)
        view_menu.addAction("View Nozzles", self.view_nozzles)
        view_menu.addSeparator()
        view_menu.addAction("View Exchange Rates", self.view_exchange_rates)
        view_menu.addAction("View Account Heads", self.view_account_heads)
        
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
        dialog = RecordSaleDialog(self.fuel_service, self.nozzle_service, self.sales_service, self.db_service)
        if dialog.exec_() == QDialog.Accepted:
            QMessageBox.information(self, "Success", "Sale recorded successfully!")

    def record_purchase_dialog(self):
        """Open dialog to record a fuel purchase."""
        dialog = RecordPurchaseDialog(self.fuel_service, self.tank_service, self.db_service)
        if dialog.exec_() == QDialog.Accepted:
            QMessageBox.information(self, "Success", "Fuel purchase recorded successfully!")

    def update_exchange_rate_dialog(self):
        """Open dialog to update exchange rate."""
        dialog = UpdateExchangeRateDialog(self.db_service)
        if dialog.exec_() == QDialog.Accepted:
            QMessageBox.information(self, "Success", "Exchange rate updated successfully!")

    def record_expense_dialog(self):
        """Open dialog to record an expense."""
        dialog = RecordExpenseDialog(self.db_service)
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
        """Daily transactions report."""
        QMessageBox.information(self, "Daily Transactions", "Daily transactions report coming soon!")

    def view_sales_records(self):
        """View sales records."""
        try:
            sales_data = self.db_service.list_documents('sales')
            columns = ["ID", "Nozzle", "Fuel Type", "Quantity (L)", "Price", "Total (Rs)", "Payment", "Date"]
            data = []
            
            for sale in sales_data:
                data.append([
                    sale.get('id', '')[:8],
                    sale.get('nozzle_id', ''),
                    sale.get('fuel_type', ''),
                    f"{sale.get('quantity', 0):.2f}",
                    f"{sale.get('price', 0):.2f}",
                    f"{sale.get('total_amount', 0):.2f}",
                    sale.get('payment_method', ''),
                    sale.get('timestamp', '')[:10]
                ])
            
            if not data:
                data = [["No sales records found", "", "", "", "", "", "", ""]]
            
            dialog = DataViewDialog("Sales Records", columns, data, self)
            dialog.exec_()
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Failed to load sales: {str(e)}")

    def view_purchase_records(self):
        """View purchase records."""
        try:
            purchases_data = self.db_service.list_documents('purchases')
            columns = ["ID", "Tank", "Supplier", "Quantity (L)", "Unit Cost", "Total (Rs)", "Invoice", "Date"]
            data = []
            
            for purchase in purchases_data:
                data.append([
                    purchase.get('id', '')[:8],
                    purchase.get('tank_id', ''),
                    purchase.get('supplier_name', ''),
                    f"{purchase.get('quantity', 0):.2f}",
                    f"{purchase.get('unit_cost', 0):.2f}",
                    f"{purchase.get('total_cost', 0):.2f}",
                    purchase.get('invoice_number', ''),
                    purchase.get('timestamp', '')[:10]
                ])
            
            if not data:
                data = [["No purchase records found", "", "", "", "", "", "", ""]]
            
            dialog = DataViewDialog("Purchase Records", columns, data, self)
            dialog.exec_()
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Failed to load purchases: {str(e)}")

    def view_customers(self):
        """View customers."""
        try:
            customers_data = self.db_service.list_documents('customers')
            columns = ["ID", "Name", "Phone", "Email", "Address", "Credit Limit (Rs)", "Type"]
            data = []
            
            for customer in customers_data:
                data.append([
                    customer.get('id', '')[:8],
                    customer.get('name', ''),
                    customer.get('phone', ''),
                    customer.get('email', ''),
                    customer.get('address', ''),
                    f"{customer.get('credit_limit', 0):.2f}",
                    customer.get('customer_type', '')
                ])
            
            if not data:
                data = [["No customers found", "", "", "", "", "", ""]]
            
            dialog = DataViewDialog("Customers", columns, data, self)
            dialog.exec_()
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Failed to load customers: {str(e)}")

    def view_expenses(self):
        """View expenses."""
        try:
            expenses_data = self.db_service.list_documents('expenses')
            columns = ["ID", "Category", "Description", "Amount (Rs)", "Payment Method", "Reference", "Date"]
            data = []
            
            for expense in expenses_data:
                data.append([
                    expense.get('id', '')[:8],
                    expense.get('category', ''),
                    expense.get('description', ''),
                    f"{expense.get('amount', 0):.2f}",
                    expense.get('payment_method', ''),
                    expense.get('reference_number', ''),
                    expense.get('timestamp', '')[:10]
                ])
            
            if not data:
                data = [["No expenses found", "", "", "", "", "", ""]]
            
            dialog = DataViewDialog("Expenses", columns, data, self)
            dialog.exec_()
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Failed to load expenses: {str(e)}")

    def view_fuel_types(self):
        """View fuel types."""
        try:
            fuel_types = self.fuel_service.list_fuel_types()
            columns = ["ID", "Name", "Unit Price (Rs)", "Tax %"]
            data = []
            
            for fuel in fuel_types:
                data.append([
                    fuel.id[:8] if fuel.id else '',
                    fuel.name,
                    f"{float(fuel.unit_price):.2f}",
                    f"{float(fuel.tax_percentage):.2f}"
                ])
            
            if not data:
                data = [["No fuel types found", "", "", ""]]
            
            dialog = DataViewDialog("Fuel Types", columns, data, self)
            dialog.exec_()
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Failed to load fuel types: {str(e)}")

    def view_tanks(self):
        """View tanks."""
        try:
            tanks = self.tank_service.list_tanks()
            columns = ["ID", "Name", "Fuel Type", "Capacity (L)", "Min Stock (L)", "Location"]
            data = []
            
            for tank in tanks:
                data.append([
                    tank.id[:8] if tank.id else '',
                    tank.name,
                    tank.fuel_type_id,
                    f"{float(tank.capacity):.0f}",
                    f"{float(tank.minimum_stock):.0f}",
                    tank.location
                ])
            
            if not data:
                data = [["No tanks found", "", "", "", "", ""]]
            
            dialog = DataViewDialog("Tanks", columns, data, self)
            dialog.exec_()
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Failed to load tanks: {str(e)}")

    def view_nozzles(self):
        """View nozzles."""
        try:
            nozzles = self.nozzle_service.list_nozzles()
            columns = ["ID", "Machine ID", "Nozzle Number", "Fuel Type", "Opening Reading"]
            data = []
            
            for nozzle in nozzles:
                data.append([
                    nozzle.id[:8] if nozzle.id else '',
                    nozzle.machine_id,
                    str(nozzle.nozzle_number),
                    nozzle.fuel_type_id,
                    f"{float(nozzle.opening_reading):.2f}"
                ])
            
            if not data:
                data = [["No nozzles found", "", "", "", ""]]
            
            dialog = DataViewDialog("Nozzles", columns, data, self)
            dialog.exec_()
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Failed to load nozzles: {str(e)}")

    def view_exchange_rates(self):
        """View exchange rates."""
        try:
            rates_data = self.db_service.list_documents('exchange_rates')
            columns = ["ID", "From Currency", "To Currency", "Rate", "Effective Date"]
            data = []
            
            for rate in rates_data:
                data.append([
                    rate.get('id', '')[:8],
                    rate.get('from_currency', ''),
                    rate.get('to_currency', ''),
                    f"{rate.get('rate', 0):.4f}",
                    rate.get('effective_date', '')
                ])
            
            if not data:
                data = [["No exchange rates found", "", "", "", ""]]
            
            dialog = DataViewDialog("Exchange Rates", columns, data, self)
            dialog.exec_()
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Failed to load exchange rates: {str(e)}")

    def view_account_heads(self):
        """View account heads."""
        try:
            accounts = self.db_service.list_documents('account_heads')
            columns = ["ID", "Name", "Type", "Code", "Description"]
            data = []
            
            for account in accounts:
                data.append([
                    account.get('id', '')[:8],
                    account.get('name', ''),
                    account.get('account_type', ''),
                    account.get('code', ''),
                    account.get('description', '')
                ])
            
            if not data:
                data = [["No account heads found", "", "", "", ""]]
            
            dialog = DataViewDialog("Account Heads", columns, data, self)
            dialog.exec_()
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Failed to load account heads: {str(e)}")

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
        print("Update Stock Levels clicked")

    def view_inventory_report(self):
        """View inventory report."""
        print("View Inventory Report clicked")

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
            # Get all sales records
            sales_data = self.db_service.list_documents('sales')
            
            # Get all purchase records
            purchase_data = self.db_service.list_documents('purchases')
            
            # Get all customers
            customers_data = self.db_service.list_documents('customers')
            
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
            
            # Net Revenue = Sales Revenue - Purchase Cost
            net_revenue = total_sales_revenue - total_purchase_cost
            
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
            
            # Now showing Net Revenue (Sales - Purchases)
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
        self.setGeometry(300, 200, 800, 500)
        self.init_ui()

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
        self.table.setColumnCount(3)
        self.table.setHorizontalHeaderLabels(["Name", "Unit Price (Rs)", "Tax %"])
        self.table.setAlternatingRowColors(True)
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.setMinimumHeight(300)
        
        # Connect to item changed signal for auto-add rows
        self.table.itemChanged.connect(self.on_cell_changed)
        
        # Add initial single empty row
        self.add_empty_rows(1)
        
        layout.addWidget(self.table)

        # Buttons
        button_layout = QHBoxLayout()
        
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

    def on_cell_changed(self, item):
        """Auto-add new row when last row gets data."""
        if self.table.rowCount() == 0:
            return
            
        last_row = self.table.rowCount() - 1
        
        # Check if we're editing the last row
        if item.row() == last_row:
            # Check if last row has any data
            has_data = False
            for col in range(self.table.columnCount()):
                cell = self.table.item(last_row, col)
                if cell and cell.text().strip():
                    has_data = True
                    break
            
            # If last row has data, add new empty row
            if has_data:
                # Disconnect signal before adding row to prevent recursion
                self.table.itemChanged.disconnect(self.on_cell_changed)
                self.add_empty_rows(1)
                # Reconnect signal
                self.table.itemChanged.connect(self.on_cell_changed)

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
            columns = ["ID", "Name", "Unit Price (Rs)", "Tax %"]
            data = []
            
            for fuel in fuel_types:
                data.append([
                    fuel.id[:8] if fuel.id else '',
                    fuel.name,
                    f"{float(fuel.unit_price):.2f}",
                    f"{float(fuel.tax_percentage):.2f}"
                ])
            
            if not data:
                data = [["No fuel types found", "", "", ""]]
            
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
        self.setGeometry(300, 200, 1000, 500)
        self.init_ui()

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
        self.table.setHorizontalHeaderLabels(["Name", "Fuel Type", "Capacity (L)", "Min Stock (L)", "Location"])
        self.table.setAlternatingRowColors(True)
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.setMinimumHeight(300)
        
        # Connect to item changed signal for auto-add rows
        self.table.itemChanged.connect(self.on_cell_changed)
        
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

    def on_cell_changed(self, item):
        """Auto-add new row when last row gets data."""
        if self.table.rowCount() == 0:
            return
            
        last_row = self.table.rowCount() - 1
        
        # Check if we're editing the last row
        if item.row() == last_row:
            # Check if last row has any data
            has_data = False
            for col in range(self.table.columnCount()):
                if col == 1:  # Skip fuel type combo
                    widget = self.table.cellWidget(last_row, col)
                    if widget:
                        combo = widget
                        if combo.currentText().strip():
                            has_data = True
                            break
                else:
                    cell = self.table.item(last_row, col)
                    if cell and cell.text().strip():
                        has_data = True
                        break
            
            # If last row has data, add new empty row
            if has_data:
                # Disconnect signal before adding row to prevent recursion
                self.table.itemChanged.disconnect(self.on_cell_changed)
                self.add_empty_rows(1)
                # Reconnect signal
                self.table.itemChanged.connect(self.on_cell_changed)

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
            columns = ["ID", "Name", "Fuel Type", "Capacity (L)", "Min Stock (L)", "Location"]
            data = []
            
            for tank in tanks:
                data.append([
                    tank.id[:8] if tank.id else '',
                    tank.name,
                    tank.fuel_type_id,
                    f"{float(tank.capacity):.0f}",
                    f"{float(tank.minimum_stock):.0f}",
                    tank.location
                ])
            
            if not data:
                data = [["No tanks found", "", "", "", "", ""]]
            
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
        self.setGeometry(300, 200, 1000, 500)
        self.account_types = ["Revenue", "Expense", "Asset", "Liability", "Equity"]
        self.init_ui()

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
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels(["Name", "Account Type", "Code", "Description"])
        self.table.setAlternatingRowColors(True)
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.setStyleSheet(
            "QTableWidget { background-color: white; alternate-background-color: #f9f9f9; border: 1px solid #ddd; }"
            "QHeaderView::section { background-color: #2196F3; color: white; padding: 5px; border: none; font-weight: bold; }"
            "QTableWidget::item { padding: 5px; border-bottom: 1px solid #e0e0e0; }"
        )
        layout.addWidget(self.table)

        # Buttons
        button_layout = QHBoxLayout()
        
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

        # Add empty rows and connect signal
        self.add_empty_rows(1)
        self.table.itemChanged.connect(self.on_cell_changed)

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
            
            # Description cell
            self.table.setItem(row, 3, QTableWidgetItem(""))

    def on_cell_changed(self, item):
        """Handle cell changes for auto-expand."""
        self.table.itemChanged.disconnect(self.on_cell_changed)
        
        # Check if last row has data
        last_row = self.table.rowCount() - 1
        if last_row >= 0:
            last_row_data = []
            for col in range(4):
                if col == 1:
                    widget = self.table.cellWidget(last_row, col)
                    if widget:
                        last_row_data.append(widget.currentText())
                else:
                    cell = self.table.item(last_row, col)
                    if cell:
                        last_row_data.append(cell.text())
            
            # If last row has any data, add a new empty row
            if any(last_row_data):
                self.add_empty_rows(1)
        
        self.table.itemChanged.connect(self.on_cell_changed)

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
                desc = self.table.item(row, 3)
                
                name_text = name.text().strip() if name else ""
                account_type = type_widget.currentText() if type_widget else ""
                code_text = code.text().strip() if code else ""
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
                
                # Create account head
                try:
                    account_id = self.db_service.firestore.collection('account_heads').document().id
                    data = {
                        'id': account_id,
                        'name': name_text,
                        'account_type': account_type,
                        'code': code_text,
                        'description': desc_text,
                        'status': 'active'
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
            
            # Clear saved rows
            for row in sorted(saved_rows, reverse=True):
                self.table.removeRow(row)
            
            if not self.table.rowCount():
                self.add_empty_rows(1)
            
            if not errors:
                self.view_account_heads_list()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"An error occurred: {str(e)}")

    def view_account_heads_list(self):
        """View account heads list in grid."""
        try:
            accounts = self.db_service.list_documents('account_heads')
            columns = ["ID", "Name", "Type", "Code", "Description"]
            data = []
            
            for account in accounts:
                data.append([
                    account.get('id', '')[:8],
                    account.get('name', ''),
                    account.get('account_type', ''),
                    account.get('code', ''),
                    account.get('description', '')
                ])
            
            if not data:
                data = [["No account heads found", "", "", "", ""]]
            
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
        self.setGeometry(300, 200, 1000, 500)
        self.fuel_types = []
        self.load_fuel_types()
        self.init_ui()

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
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels(["Machine ID", "Nozzle Number", "Fuel Type", "Opening Reading (L)"])
        self.table.setAlternatingRowColors(True)
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.setStyleSheet(
            "QTableWidget { background-color: white; alternate-background-color: #f9f9f9; border: 1px solid #ddd; }"
            "QHeaderView::section { background-color: #2196F3; color: white; padding: 5px; border: none; font-weight: bold; }"
            "QTableWidget::item { padding: 5px; border-bottom: 1px solid #e0e0e0; }"
        )
        layout.addWidget(self.table)

        # Buttons
        button_layout = QHBoxLayout()
        
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

        # Add empty rows and connect signal
        self.add_empty_rows(1)
        self.table.itemChanged.connect(self.on_cell_changed)

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

    def load_fuel_types(self):
        """Load fuel types into memory."""
        try:
            self.fuel_types = self.fuel_service.list_fuel_types()
        except Exception as e:
            print(f"Error loading fuel types: {str(e)}")

    def on_cell_changed(self, item):
        """Handle cell changes for auto-expand."""
        self.table.itemChanged.disconnect(self.on_cell_changed)
        
        # Check if last row has data
        last_row = self.table.rowCount() - 1
        if last_row >= 0:
            last_row_data = []
            for col in range(4):
                if col == 2:
                    widget = self.table.cellWidget(last_row, col)
                    if widget:
                        last_row_data.append(widget.currentData())
                else:
                    cell = self.table.item(last_row, col)
                    if cell:
                        last_row_data.append(cell.text())
            
            # If last row has any data, add a new empty row
            if any(last_row_data):
                self.add_empty_rows(1)
        
        self.table.itemChanged.connect(self.on_cell_changed)

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
            
            # Clear saved rows
            for row in sorted(saved_rows, reverse=True):
                self.table.removeRow(row)
            
            if not self.table.rowCount():
                self.add_empty_rows(1)
            
            if not errors:
                self.view_nozzles_list()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"An error occurred: {str(e)}")

    def view_nozzles_list(self):
        """View nozzles list in grid."""
        try:
            nozzles = self.nozzle_service.list_nozzles()
            columns = ["ID", "Machine ID", "Nozzle Number", "Fuel Type", "Opening Reading"]
            data = []
            
            for nozzle in nozzles:
                data.append([
                    nozzle.id[:8] if nozzle.id else '',
                    nozzle.machine_id,
                    str(nozzle.nozzle_number),
                    nozzle.fuel_type_id,
                    f"{float(nozzle.opening_reading):.2f}"
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

    def __init__(self, fuel_service, nozzle_service, sales_service, db_service, parent=None):
        """Initialize dialog."""
        super().__init__(parent)
        self.fuel_service = fuel_service
        self.nozzle_service = nozzle_service
        self.sales_service = sales_service
        self.db_service = db_service
        self.nozzles = []
        self.fuel_types = []
        self.nozzle_fuel_map = {}
        
        self.setWindowTitle("Record Sales")
        self.setGeometry(300, 200, 1000, 500)
        self.load_data()
        self.init_ui()

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
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels(["Nozzle", "Fuel Type", "Quantity (L)", "Unit Price (Rs)", "Total (Rs)", "Payment Method"])
        self.table.setAlternatingRowColors(True)
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.setStyleSheet(
            "QTableWidget { background-color: white; alternate-background-color: #f9f9f9; border: 1px solid #ddd; }"
            "QHeaderView::section { background-color: #2196F3; color: white; padding: 5px; border: none; font-weight: bold; }"
            "QTableWidget::item { padding: 5px; border-bottom: 1px solid #e0e0e0; }"
        )
        layout.addWidget(self.table)

        # Buttons
        button_layout = QHBoxLayout()
        
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

        # Add empty rows and connect signal
        self.add_empty_rows(1)
        self.table.itemChanged.connect(self.on_cell_changed)

    def load_data(self):
        """Load nozzles and fuel types."""
        try:
            self.nozzles = self.nozzle_service.list_nozzles()
            self.fuel_types = self.fuel_service.list_fuel_types()
            
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
            nozzle_combo.currentIndexChanged.connect(lambda idx, r=row: self.on_nozzle_changed(r))
            self.table.setCellWidget(row, 0, nozzle_combo)
            
            # Fuel Type combo (auto-populated from nozzle)
            fuel_combo = QComboBox()
            fuel_combo.addItem("-- Auto-populated --", "")
            for fuel in self.fuel_types:
                fuel_combo.addItem(fuel.name, fuel.id)
            fuel_combo.setEnabled(False)
            self.table.setCellWidget(row, 1, fuel_combo)
            
            # Quantity cell
            self.table.setItem(row, 2, QTableWidgetItem(""))
            
            # Unit Price cell
            self.table.setItem(row, 3, QTableWidgetItem(""))
            
            # Total cell (read-only, calculated)
            total_item = QTableWidgetItem("0.00")
            total_item.setFlags(total_item.flags() & ~Qt.ItemIsEditable)
            self.table.setItem(row, 4, total_item)
            
            # Payment Method combo
            payment_combo = QComboBox()
            payment_combo.addItems(["Cash", "Credit Card", "Bank Transfer", "Credit Account"])
            self.table.setCellWidget(row, 5, payment_combo)

    def on_nozzle_changed(self, row):
        """Update fuel type when nozzle changes."""
        nozzle_combo = self.table.cellWidget(row, 0)
        fuel_combo = self.table.cellWidget(row, 1)
        
        if nozzle_combo and fuel_combo:
            nozzle_id = nozzle_combo.currentData()
            if nozzle_id and nozzle_id in self.nozzle_fuel_map:
                fuel_type_id = self.nozzle_fuel_map[nozzle_id]
                index = fuel_combo.findData(fuel_type_id)
                if index >= 0:
                    fuel_combo.setCurrentIndex(index)

    def on_cell_changed(self, item):
        """Handle cell changes for auto-expand and calculations."""
        self.table.itemChanged.disconnect(self.on_cell_changed)
        
        # Calculate totals for all rows
        for row in range(self.table.rowCount()):
            qty_item = self.table.item(row, 2)
            price_item = self.table.item(row, 3)
            total_item = self.table.item(row, 4)
            
            try:
                qty = float(qty_item.text()) if qty_item and qty_item.text() else 0
                price = float(price_item.text()) if price_item and price_item.text() else 0
                total = qty * price
                if total_item:
                    total_item.setText(f"{total:.2f}")
            except ValueError:
                pass
        
        # Check if last row has data
        last_row = self.table.rowCount() - 1
        if last_row >= 0:
            last_row_data = []
            for col in range(4):
                if col == 0:
                    widget = self.table.cellWidget(last_row, col)
                    if widget:
                        last_row_data.append(widget.currentData())
                elif col == 1:
                    continue
                else:
                    cell = self.table.item(last_row, col)
                    if cell:
                        last_row_data.append(cell.text())
            
            # If last row has any data, add a new empty row
            if any(last_row_data):
                self.add_empty_rows(1)
        
        self.table.itemChanged.connect(self.on_cell_changed)

    def save_all_sales(self):
        """Save all non-empty sales to database."""
        try:
            errors = {}
            saved_rows = []
            
            for row in range(self.table.rowCount()):
                # Get row data
                nozzle_combo = self.table.cellWidget(row, 0)
                fuel_combo = self.table.cellWidget(row, 1)
                qty_item = self.table.item(row, 2)
                price_item = self.table.item(row, 3)
                payment_combo = self.table.cellWidget(row, 5)
                
                nozzle_id = nozzle_combo.currentData() if nozzle_combo else ""
                qty_text = qty_item.text().strip() if qty_item else ""
                price_text = price_item.text().strip() if price_item else ""
                
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
                
                # Try to convert to numbers
                try:
                    quantity = float(qty_text)
                    unit_price = float(price_text)
                except ValueError:
                    errors[row + 1] = "Quantity and Price must be numbers"
                    continue
                
                if quantity <= 0:
                    errors[row + 1] = "Quantity must be greater than 0"
                    continue
                
                # Get payment method
                payment_method = payment_combo.currentText() if payment_combo else "Cash"
                
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
                        'payment_method': payment_method,
                        'status': 'completed'
                    }
                    
                    success, msg = self.db_service.create_document('sales', sale_id, data)
                    
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
                    error_msg += f"\n{len(saved_rows)} sale(s) saved successfully."
                QMessageBox.warning(self, "Validation Errors", error_msg)
            else:
                QMessageBox.information(self, "Success", f"All {len(saved_rows)} sale(s) saved successfully!")
            
            # Clear saved rows
            for row in sorted(saved_rows, reverse=True):
                self.table.removeRow(row)
            
            if not self.table.rowCount():
                self.add_empty_rows(1)
            
            if not errors:
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
            columns = ["ID", "Nozzle", "Fuel Type", "Quantity (L)", "Price", "Total (Rs)", "Payment", "Date"]
            data = []
            
            for sale in sales_data:
                data.append([
                    sale.get('id', '')[:8],
                    sale.get('nozzle_id', ''),
                    sale.get('fuel_type', ''),
                    f"{sale.get('quantity', 0):.2f}",
                    f"{sale.get('price', 0):.2f}",
                    f"{sale.get('total_amount', 0):.2f}",
                    sale.get('payment_method', ''),
                    sale.get('timestamp', '')[:10]
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
        self.setGeometry(300, 200, 1000, 500)
        self.init_ui()

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
        self.table.setHorizontalHeaderLabels(["Name", "Phone", "Email", "Address", "Credit Limit (Rs)", "Type"])
        self.table.setAlternatingRowColors(True)
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.setStyleSheet(
            "QTableWidget { background-color: white; alternate-background-color: #f9f9f9; border: 1px solid #ddd; }"
            "QHeaderView::section { background-color: #2196F3; color: white; padding: 5px; border: none; font-weight: bold; }"
            "QTableWidget::item { padding: 5px; border-bottom: 1px solid #e0e0e0; }"
        )
        layout.addWidget(self.table)

        # Buttons
        button_layout = QHBoxLayout()
        
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

        # Add empty rows and connect signal
        self.add_empty_rows(1)
        self.table.itemChanged.connect(self.on_cell_changed)

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

    def on_cell_changed(self, item):
        """Handle cell changes for auto-expand."""
        self.table.itemChanged.disconnect(self.on_cell_changed)
        
        # Check if last row has data
        last_row = self.table.rowCount() - 1
        if last_row >= 0:
            last_row_data = []
            for col in range(5):
                if col == 5:
                    continue
                cell = self.table.item(last_row, col)
                if cell:
                    last_row_data.append(cell.text())
            
            # If last row has any data, add a new empty row
            if any(last_row_data):
                self.add_empty_rows(1)
        
        self.table.itemChanged.connect(self.on_cell_changed)

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
            
            # Clear saved rows
            for row in sorted(saved_rows, reverse=True):
                self.table.removeRow(row)
            
            if not self.table.rowCount():
                self.add_empty_rows(1)
            
            if not errors:
                self.view_customers_list()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"An error occurred: {str(e)}")

    def view_customers_list(self):
        """View customers records in grid."""
        try:
            customers_data = self.db_service.list_documents('customers')
            columns = ["ID", "Name", "Phone", "Email", "Address", "Credit Limit (Rs)", "Type"]
            data = []
            
            for customer in customers_data:
                data.append([
                    customer.get('id', '')[:8],
                    customer.get('name', ''),
                    customer.get('phone', ''),
                    customer.get('email', ''),
                    customer.get('address', ''),
                    f"{customer.get('credit_limit', 0):.2f}",
                    customer.get('customer_type', '')
                ])
            
            if not data:
                data = [["No customers found", "", "", "", "", "", ""]]
            
            dialog = DataViewDialog("Customers", columns, data, self)
            dialog.exec_()
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Failed to load customers: {str(e)}")


class RecordPurchaseDialog(QDialog):
    """Dialog for recording multiple fuel purchases with grid interface."""

    def __init__(self, fuel_service, tank_service, db_service, parent=None):
        """Initialize dialog."""
        super().__init__(parent)
        self.fuel_service = fuel_service
        self.tank_service = tank_service
        self.db_service = db_service
        self.tanks = []
        
        self.setWindowTitle("Record Purchases")
        self.setGeometry(300, 200, 1000, 500)
        self.load_tanks()
        self.init_ui()

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
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels(["Tank", "Supplier Name", "Quantity (L)", "Unit Cost (Rs)", "Total (Rs)", "Invoice Number"])
        self.table.setAlternatingRowColors(True)
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.setStyleSheet(
            "QTableWidget { background-color: white; alternate-background-color: #f9f9f9; border: 1px solid #ddd; }"
            "QHeaderView::section { background-color: #2196F3; color: white; padding: 5px; border: none; font-weight: bold; }"
            "QTableWidget::item { padding: 5px; border-bottom: 1px solid #e0e0e0; }"
        )
        layout.addWidget(self.table)

        # Buttons
        button_layout = QHBoxLayout()
        
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

        # Add empty rows and connect signal
        self.add_empty_rows(1)
        self.table.itemChanged.connect(self.on_cell_changed)

    def load_tanks(self):
        """Load tanks into memory."""
        try:
            self.tanks = self.tank_service.list_tanks()
        except Exception as e:
            print(f"Error loading tanks: {str(e)}")

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
            
            # Invoice Number cell
            self.table.setItem(row, 5, QTableWidgetItem(""))

    def on_cell_changed(self, item):
        """Handle cell changes for auto-expand and calculations."""
        self.table.itemChanged.disconnect(self.on_cell_changed)
        
        # Calculate totals for all rows
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
            except ValueError:
                pass
        
        # Check if last row has data
        last_row = self.table.rowCount() - 1
        if last_row >= 0:
            last_row_data = []
            for col in range(5):
                if col == 0:
                    widget = self.table.cellWidget(last_row, col)
                    if widget:
                        last_row_data.append(widget.currentData())
                elif col == 4:
                    continue
                else:
                    cell = self.table.item(last_row, col)
                    if cell:
                        last_row_data.append(cell.text())
            
            # If last row has any data, add a new empty row
            if any(last_row_data):
                self.add_empty_rows(1)
        
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
                invoice_item = self.table.item(row, 5)
                
                tank_id = tank_combo.currentData() if tank_combo else ""
                supplier = supplier_item.text().strip() if supplier_item else ""
                qty_text = qty_item.text().strip() if qty_item else ""
                cost_text = cost_item.text().strip() if cost_item else ""
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
                        'invoice_number': invoice,
                        'purchase_date': datetime.now().isoformat(),
                        'status': 'completed'
                    }

                    success, msg = self.db_service.create_document('purchases', purchase_id, data)

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
                    error_msg += f"\n{len(saved_rows)} purchase(s) saved successfully."
                QMessageBox.warning(self, "Validation Errors", error_msg)
            else:
                QMessageBox.information(self, "Success", f"All {len(saved_rows)} purchase(s) saved successfully!")
            
            # Clear saved rows
            for row in sorted(saved_rows, reverse=True):
                self.table.removeRow(row)
            
            if not self.table.rowCount():
                self.add_empty_rows(1)
            
            if not errors:
                self.view_purchases()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"An error occurred: {str(e)}")

    def view_purchases(self):
        """View purchase records in grid."""
        try:
            purchases_data = self.db_service.list_documents('purchases')
            columns = ["ID", "Tank", "Supplier", "Quantity (L)", "Unit Cost", "Total (Rs)", "Invoice", "Date"]
            data = []
            
            for purchase in purchases_data:
                data.append([
                    purchase.get('id', '')[:8],
                    purchase.get('tank_id', ''),
                    purchase.get('supplier_name', ''),
                    f"{purchase.get('quantity', 0):.2f}",
                    f"{purchase.get('unit_cost', 0):.2f}",
                    f"{purchase.get('total_cost', 0):.2f}",
                    purchase.get('invoice_number', ''),
                    purchase.get('timestamp', '')[:10]
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
        self.setGeometry(400, 300, 500, 300)
        self.init_ui()

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
            columns = ["ID", "From Currency", "To Currency", "Rate", "Effective Date"]
            data = []
            
            for rate in rates_data:
                data.append([
                    rate.get('id', '')[:8],
                    rate.get('from_currency', ''),
                    rate.get('to_currency', ''),
                    f"{rate.get('rate', 0):.4f}",
                    rate.get('effective_date', '')
                ])
            
            if not data:
                data = [["No exchange rates found", "", "", "", ""]]
            
            dialog = DataViewDialog("Exchange Rates", columns, data, self)
            dialog.exec_()
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Failed to load exchange rates: {str(e)}")


class RecordExpenseDialog(QDialog):
    """Dialog for recording expenses."""

    def __init__(self, db_service, parent=None):
        """Initialize dialog."""
        super().__init__(parent)
        self.db_service = db_service
        
        self.setWindowTitle("Record Expense")
        self.setGeometry(300, 200, 550, 450)
        self.init_ui()

    def init_ui(self):
        """Initialize UI components."""
        layout = QFormLayout()
        layout.setSpacing(12)
        layout.setContentsMargins(20, 20, 20, 20)

        # Expense Category
        category_label = QLabel("Expense Category:")
        self.category_combo = QComboBox()
        self.category_combo.addItems([
            "Utilities",
            "Maintenance",
            "Salaries",
            "Transportation",
            "Office Supplies",
            "Insurance",
            "Equipment",
            "Other"
        ])
        layout.addRow(category_label, self.category_combo)

        # Description
        desc_label = QLabel("Description:")
        self.desc_input = QLineEdit()
        self.desc_input.setPlaceholderText("Expense details")
        layout.addRow(desc_label, self.desc_input)

        # Amount
        amount_label = QLabel("Amount (Rs.):")
        self.amount_input = QDoubleSpinBox()
        self.amount_input.setMinimum(0)
        self.amount_input.setMaximum(999999999)
        self.amount_input.setDecimals(2)
        layout.addRow(amount_label, self.amount_input)

        # Payment Method
        payment_label = QLabel("Payment Method:")
        self.payment_combo = QComboBox()
        self.payment_combo.addItems(["Cash", "Bank Transfer", "Cheque", "Credit Card"])
        layout.addRow(payment_label, self.payment_combo)

        # Reference/Invoice
        ref_label = QLabel("Reference Number:")
        self.ref_input = QLineEdit()
        self.ref_input.setPlaceholderText("Invoice or receipt number")
        layout.addRow(ref_label, self.ref_input)

        # Notes
        notes_label = QLabel("Notes:")
        self.notes_input = QLineEdit()
        self.notes_input.setPlaceholderText("Additional information")
        layout.addRow(notes_label, self.notes_input)

        # Buttons
        button_layout = QHBoxLayout()
        
        record_btn = QPushButton("Record Expense")
        record_btn.setStyleSheet(
            "QPushButton { background-color: #4CAF50; color: white; padding: 8px 20px; border-radius: 5px; }"
            "QPushButton:hover { background-color: #45a049; }"
        )
        record_btn.clicked.connect(self.record_expense)
        button_layout.addWidget(record_btn)
        
        view_btn = QPushButton("View Records")
        view_btn.setStyleSheet(
            "QPushButton { background-color: #2196F3; color: white; padding: 8px 20px; border-radius: 5px; }"
            "QPushButton:hover { background-color: #0b7dda; }"
        )
        view_btn.clicked.connect(self.view_expenses_list)
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

    def record_expense(self):
        """Record the expense."""
        try:
            category = self.category_combo.currentText()
            description = self.desc_input.text().strip()
            amount = self.amount_input.value()
            payment_method = self.payment_combo.currentText()
            reference = self.ref_input.text().strip()
            notes = self.notes_input.text().strip()

            if not description:
                QMessageBox.warning(self, "Error", "Please enter expense description")
                return

            if amount <= 0:
                QMessageBox.warning(self, "Error", "Amount must be greater than 0")
                return

            # Create expense record
            import uuid
            expense_id = str(uuid.uuid4())
            
            data = {
                'id': expense_id,
                'category': category,
                'description': description,
                'amount': amount,
                'payment_method': payment_method,
                'reference_number': reference,
                'notes': notes,
                'expense_date': datetime.now().isoformat(),
                'status': 'recorded'
            }

            success, msg = self.db_service.create_document('expenses', expense_id, data)

            if success:
                QMessageBox.information(self, "Success", f"Expense recorded successfully!\nExpense ID: {expense_id}\nAmount: Rs. {amount:,.2f}")
                self.accept()
            else:
                QMessageBox.critical(self, "Error", f"Failed to record expense: {msg}")

        except Exception as e:
            QMessageBox.critical(self, "Error", f"An error occurred: {str(e)}")

    def view_expenses_list(self):
        """View expenses records in grid."""
        try:
            expenses_data = self.db_service.list_documents('expenses')
            columns = ["ID", "Category", "Description", "Amount (Rs)", "Payment Method", "Reference", "Date"]
            data = []
            
            for expense in expenses_data:
                data.append([
                    expense.get('id', '')[:8],
                    expense.get('category', ''),
                    expense.get('description', ''),
                    f"{expense.get('amount', 0):.2f}",
                    expense.get('payment_method', ''),
                    expense.get('reference_number', ''),
                    expense.get('timestamp', '')[:10]
                ])
            
            if not data:
                data = [["No expenses found", "", "", "", "", "", ""]]
            
            dialog = DataViewDialog("Expenses", columns, data, self)
            dialog.exec_()
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Failed to load expenses: {str(e)}")
