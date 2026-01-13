"""
Reports Screen - Generate and view reports
"""

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QComboBox, QDateEdit, QMessageBox, QTabWidget, QTextEdit,
    QFileDialog, QProgressBar, QTableWidget, QTableWidgetItem
)
from PyQt5.QtCore import Qt, QDate, QThread, pyqtSignal
from PyQt5.QtGui import QFont, QColor
from src.reports.report_generator import ReportGenerator
from src.services.database_service import (
    SalesService, DatabaseService
)
from src.models import User
from src.config.logger_config import setup_logger
from datetime import datetime, date, timedelta
import os

logger = setup_logger(__name__)


class ReportWorker(QThread):
    """Worker thread for generating reports."""

    progress = pyqtSignal(str)
    finished = pyqtSignal(bool, str, str)

    def __init__(self, report_type, report_data):
        """Initialize worker."""
        super().__init__()
        self.report_type = report_type
        self.report_data = report_data

    def run(self):
        """Generate report."""
        try:
            self.progress.emit(f"Generating {self.report_type} report...")

            generator = ReportGenerator()
            
            if self.report_type == "daily_sales":
                file_path = generator.generate_daily_sales_report(
                    self.report_data.get('date'),
                    self.report_data.get('format', 'pdf')
                )
            elif self.report_type == "p_l":
                file_path = generator.generate_p_l_statement(
                    self.report_data.get('start_date'),
                    self.report_data.get('end_date'),
                    self.report_data.get('format', 'pdf')
                )
            elif self.report_type == "tax_summary":
                file_path = generator.generate_tax_summary(
                    self.report_data.get('start_date'),
                    self.report_data.get('end_date'),
                    self.report_data.get('format', 'pdf')
                )
            elif self.report_type == "inventory":
                file_path = generator.generate_inventory_report(
                    self.report_data.get('format', 'pdf')
                )
            elif self.report_type == "operator_performance":
                file_path = generator.generate_operator_performance(
                    self.report_data.get('start_date'),
                    self.report_data.get('end_date'),
                    self.report_data.get('format', 'pdf')
                )
            elif self.report_type == "credit_aging":
                file_path = generator.generate_credit_aging_report(
                    self.report_data.get('format', 'pdf')
                )
            else:
                raise ValueError(f"Unknown report type: {self.report_type}")

            self.finished.emit(True, "Report generated successfully", file_path)

        except Exception as e:
            logger.error(f"Error generating report: {str(e)}")
            self.finished.emit(False, f"Error generating report: {str(e)}", "")


class ReportsScreen(QWidget):
    """Reports screen for generating and viewing various business reports."""

    def __init__(self, user):
        """Initialize reports screen."""
        super().__init__()
        self.user = user
        self.sales_service = SalesService()
        self.db_service = DatabaseService()
        self.report_generator = ReportGenerator()

        self.setWindowTitle("Reports")
        self.setGeometry(100, 100, 1200, 700)

        self.init_ui()
        self.load_summary_data()

    def init_ui(self):
        """Initialize UI components."""
        main_layout = QVBoxLayout()

        # Header
        header = QLabel("Reports")
        header.setFont(QFont("Arial", 14, QFont.Bold))
        main_layout.addWidget(header)

        # Tab widget for different report types
        tabs = QTabWidget()

        # Daily Sales Report tab
        daily_tab = self.create_daily_sales_tab()
        tabs.addTab(daily_tab, "Daily Sales")

        # P&L Statement tab
        pl_tab = self.create_p_l_tab()
        tabs.addTab(pl_tab, "P&L Statement")

        # Tax Summary tab
        tax_tab = self.create_tax_summary_tab()
        tabs.addTab(tax_tab, "Tax Summary")

        # Inventory Report tab
        inventory_tab = self.create_inventory_tab()
        tabs.addTab(inventory_tab, "Inventory")

        # Operator Performance tab
        operator_tab = self.create_operator_performance_tab()
        tabs.addTab(operator_tab, "Operator Performance")

        # Credit Aging tab
        credit_tab = self.create_credit_aging_tab()
        tabs.addTab(credit_tab, "Credit Aging")

        main_layout.addWidget(tabs)
        self.setLayout(main_layout)

    def create_daily_sales_tab(self) -> QWidget:
        """Create daily sales report tab."""
        widget = QWidget()
        layout = QVBoxLayout()

        # Filter Controls
        filter_layout = QHBoxLayout()
        filter_layout.addWidget(QLabel("Date Filter:"))

        self.daily_sales_date = QDateEdit()
        self.daily_sales_date.setDate(QDate.currentDate())
        self.daily_sales_date.setCalendarPopup(True)
        self.daily_sales_date.dateChanged.connect(self.load_daily_sales_data)
        filter_layout.addWidget(self.daily_sales_date)

        filter_layout.addWidget(QLabel("Format:"))
        self.daily_sales_format = QComboBox()
        self.daily_sales_format.addItems(["PDF", "Excel"])
        filter_layout.addWidget(self.daily_sales_format)

        generate_btn = QPushButton("Generate Report")
        generate_btn.clicked.connect(self.generate_daily_sales_report)
        filter_layout.addWidget(generate_btn)
        filter_layout.addStretch()

        layout.addLayout(filter_layout)

        # Data Grid
        self.daily_sales_table = QTableWidget()
        self.daily_sales_table.setColumnCount(5)
        self.daily_sales_table.setHorizontalHeaderLabels(["Date", "Item", "Quantity", "Amount", "Operator"])
        self.daily_sales_table.setSelectionBehavior(QTableWidget.SelectRows)
        layout.addWidget(QLabel("Daily Sales Data:"))
        layout.addWidget(self.daily_sales_table)

        # Progress
        self.daily_sales_progress = QProgressBar()
        self.daily_sales_progress.setVisible(False)
        layout.addWidget(self.daily_sales_progress)

        widget.setLayout(layout)
        self.load_daily_sales_data()
        return widget

    def create_p_l_tab(self) -> QWidget:
        """Create P&L statement tab."""
        widget = QWidget()
        layout = QVBoxLayout()

        # Filter Controls
        controls_layout = QHBoxLayout()
        controls_layout.addWidget(QLabel("Start Date:"))

        self.pl_start_date = QDateEdit()
        self.pl_start_date.setDate(QDate(QDate.currentDate().year, QDate.currentDate().month, 1))
        self.pl_start_date.setCalendarPopup(True)
        self.pl_start_date.dateChanged.connect(self.load_p_l_data)
        controls_layout.addWidget(self.pl_start_date)

        controls_layout.addWidget(QLabel("End Date:"))
        self.pl_end_date = QDateEdit()
        self.pl_end_date.setDate(QDate.currentDate())
        self.pl_end_date.setCalendarPopup(True)
        self.pl_end_date.dateChanged.connect(self.load_p_l_data)
        controls_layout.addWidget(self.pl_end_date)

        # Format selection
        controls_layout.addWidget(QLabel("Format:"))
        self.pl_format = QComboBox()
        self.pl_format.addItems(["PDF", "Excel"])
        controls_layout.addWidget(self.pl_format)

        # Generate button
        generate_btn = QPushButton("Generate Report")
        generate_btn.clicked.connect(self.generate_p_l_report)
        controls_layout.addWidget(generate_btn)
        controls_layout.addStretch()

        layout.addLayout(controls_layout)

        # Data Grid
        self.pl_table = QTableWidget()
        self.pl_table.setColumnCount(4)
        self.pl_table.setHorizontalHeaderLabels(["Date", "Category", "Amount", "Type"])
        self.pl_table.setSelectionBehavior(QTableWidget.SelectRows)
        layout.addWidget(QLabel("Profit & Loss Data:"))
        layout.addWidget(self.pl_table)

        # Progress
        self.pl_progress = QProgressBar()
        self.pl_progress.setVisible(False)
        layout.addWidget(self.pl_progress)

        widget.setLayout(layout)
        self.load_p_l_data()
        return widget

    def create_tax_summary_tab(self) -> QWidget:
        """Create tax summary tab."""
        widget = QWidget()
        layout = QVBoxLayout()

        # Filter Controls
        controls_layout = QHBoxLayout()
        controls_layout.addWidget(QLabel("Start Date:"))

        self.tax_start_date = QDateEdit()
        self.tax_start_date.setDate(QDate(QDate.currentDate().year, QDate.currentDate().month, 1))
        self.tax_start_date.setCalendarPopup(True)
        self.tax_start_date.dateChanged.connect(self.load_tax_data)
        controls_layout.addWidget(self.tax_start_date)

        controls_layout.addWidget(QLabel("End Date:"))
        self.tax_end_date = QDateEdit()
        self.tax_end_date.setDate(QDate.currentDate())
        self.tax_end_date.setCalendarPopup(True)
        self.tax_end_date.dateChanged.connect(self.load_tax_data)
        controls_layout.addWidget(self.tax_end_date)

        # Format selection
        controls_layout.addWidget(QLabel("Format:"))
        self.tax_format = QComboBox()
        self.tax_format.addItems(["PDF", "Excel"])
        controls_layout.addWidget(self.tax_format)

        # Generate button
        generate_btn = QPushButton("Generate Report")
        generate_btn.clicked.connect(self.generate_tax_summary_report)
        controls_layout.addWidget(generate_btn)
        controls_layout.addStretch()

        layout.addLayout(controls_layout)

        # Data Grid
        self.tax_table = QTableWidget()
        self.tax_table.setColumnCount(4)
        self.tax_table.setHorizontalHeaderLabels(["Date", "Tax Type", "Amount", "Status"])
        self.tax_table.setSelectionBehavior(QTableWidget.SelectRows)
        layout.addWidget(QLabel("Tax Summary Data:"))
        layout.addWidget(self.tax_table)

        # Progress
        self.tax_progress = QProgressBar()
        self.tax_progress.setVisible(False)
        layout.addWidget(self.tax_progress)

        widget.setLayout(layout)
        self.load_tax_data()
        return widget

    def create_inventory_tab(self) -> QWidget:
        """Create inventory report tab."""
        widget = QWidget()
        layout = QVBoxLayout()

        # Filter Controls
        controls_layout = QHBoxLayout()
        
        controls_layout.addWidget(QLabel("Format:"))
        self.inventory_format = QComboBox()
        self.inventory_format.addItems(["PDF", "Excel"])
        controls_layout.addWidget(self.inventory_format)

        # Generate button
        generate_btn = QPushButton("Generate Report")
        generate_btn.clicked.connect(self.generate_inventory_report)
        controls_layout.addWidget(generate_btn)
        controls_layout.addStretch()

        layout.addLayout(controls_layout)

        # Data Grid
        self.inventory_table = QTableWidget()
        self.inventory_table.setColumnCount(5)
        self.inventory_table.setHorizontalHeaderLabels(["Item", "Category", "Quantity", "Unit Price", "Total Value"])
        self.inventory_table.setSelectionBehavior(QTableWidget.SelectRows)
        layout.addWidget(QLabel("Inventory Data:"))
        layout.addWidget(self.inventory_table)

        # Progress
        self.inventory_progress = QProgressBar()
        self.inventory_progress.setVisible(False)
        layout.addWidget(self.inventory_progress)

        widget.setLayout(layout)
        self.load_inventory_data()
        return widget

    def create_operator_performance_tab(self) -> QWidget:
        """Create operator performance tab."""
        widget = QWidget()
        layout = QVBoxLayout()

        # Filter Controls
        controls_layout = QHBoxLayout()
        controls_layout.addWidget(QLabel("Start Date:"))

        self.operator_start_date = QDateEdit()
        self.operator_start_date.setDate(QDate(QDate.currentDate().year, QDate.currentDate().month, 1))
        self.operator_start_date.setCalendarPopup(True)
        self.operator_start_date.dateChanged.connect(self.load_operator_data)
        controls_layout.addWidget(self.operator_start_date)

        controls_layout.addWidget(QLabel("End Date:"))
        self.operator_end_date = QDateEdit()
        self.operator_end_date.setDate(QDate.currentDate())
        self.operator_end_date.setCalendarPopup(True)
        self.operator_end_date.dateChanged.connect(self.load_operator_data)
        controls_layout.addWidget(self.operator_end_date)

        # Format selection
        controls_layout.addWidget(QLabel("Format:"))
        self.operator_format = QComboBox()
        self.operator_format.addItems(["PDF", "Excel"])
        controls_layout.addWidget(self.operator_format)

        # Generate button
        generate_btn = QPushButton("Generate Report")
        generate_btn.clicked.connect(self.generate_operator_performance_report)
        controls_layout.addWidget(generate_btn)
        controls_layout.addStretch()

        layout.addLayout(controls_layout)

        # Data Grid
        self.operator_table = QTableWidget()
        self.operator_table.setColumnCount(5)
        self.operator_table.setHorizontalHeaderLabels(["Operator", "Date", "Transactions", "Total Amount", "Performance"])
        self.operator_table.setSelectionBehavior(QTableWidget.SelectRows)
        layout.addWidget(QLabel("Operator Performance Data:"))
        layout.addWidget(self.operator_table)

        # Progress
        self.operator_progress = QProgressBar()
        self.operator_progress.setVisible(False)
        layout.addWidget(self.operator_progress)

        widget.setLayout(layout)
        self.load_operator_data()
        return widget

    def create_credit_aging_tab(self) -> QWidget:
        """Create credit aging tab."""
        widget = QWidget()
        layout = QVBoxLayout()

        # Filter Controls
        controls_layout = QHBoxLayout()
        controls_layout.addWidget(QLabel("Format:"))

        self.credit_format = QComboBox()
        self.credit_format.addItems(["PDF", "Excel"])
        controls_layout.addWidget(self.credit_format)

        # Generate button
        generate_btn = QPushButton("Generate Report")
        generate_btn.clicked.connect(self.generate_credit_aging_report)
        controls_layout.addWidget(generate_btn)
        controls_layout.addStretch()

        layout.addLayout(controls_layout)

        # Data Grid
        self.credit_table = QTableWidget()
        self.credit_table.setColumnCount(5)
        self.credit_table.setHorizontalHeaderLabels(["Customer", "Amount Due", "Due Date", "Days Overdue", "Status"])
        self.credit_table.setSelectionBehavior(QTableWidget.SelectRows)
        layout.addWidget(QLabel("Credit Aging Data:"))
        layout.addWidget(self.credit_table)

        # Progress
        self.credit_progress = QProgressBar()
        self.credit_progress.setVisible(False)
        layout.addWidget(self.credit_progress)

        widget.setLayout(layout)
        self.load_credit_data()
        return widget

    def load_summary_data(self):
        """Load summary data for preview."""
        try:
            # Load sample data for previews
            pass
        except Exception as e:
            logger.error(f"Error loading summary data: {str(e)}")

    def load_daily_sales_data(self):
        """Load daily sales data for the selected date."""
        try:
            date_str = self.daily_sales_date.date().toString("yyyy-MM-dd")
            sales = self.sales_service.get_sales_by_date(date_str)
            
            self.daily_sales_table.setRowCount(0)
            
            for sale in sales:
                row_position = self.daily_sales_table.rowCount()
                self.daily_sales_table.insertRow(row_position)
                
                self.daily_sales_table.setItem(row_position, 0, QTableWidgetItem(str(sale.date) if hasattr(sale, 'date') else date_str))
                self.daily_sales_table.setItem(row_position, 1, QTableWidgetItem(str(sale.item_name if hasattr(sale, 'item_name') else 'N/A')))
                self.daily_sales_table.setItem(row_position, 2, QTableWidgetItem(str(sale.quantity if hasattr(sale, 'quantity') else 0)))
                self.daily_sales_table.setItem(row_position, 3, QTableWidgetItem(str(sale.amount if hasattr(sale, 'amount') else 0)))
                self.daily_sales_table.setItem(row_position, 4, QTableWidgetItem(str(sale.operator_name if hasattr(sale, 'operator_name') else 'N/A')))
                
        except Exception as e:
            logger.error(f"Error loading daily sales data: {str(e)}")

    def load_p_l_data(self):
        """Load P&L data for the selected date range."""
        try:
            start_date = self.pl_start_date.date().toString("yyyy-MM-dd")
            end_date = self.pl_end_date.date().toString("yyyy-MM-dd")
            
            self.pl_table.setRowCount(0)
            
            # Load P&L data from database
            sales = self.sales_service.get_sales_by_date_range(start_date, end_date)
            
            # Calculate profit/loss summary
            row_position = 0
            total_revenue = 0
            for sale in sales:
                if hasattr(sale, 'amount'):
                    total_revenue += float(sale.amount)
                    row_position = self.pl_table.rowCount()
                    self.pl_table.insertRow(row_position)
                    self.pl_table.setItem(row_position, 0, QTableWidgetItem(str(sale.date) if hasattr(sale, 'date') else start_date))
                    self.pl_table.setItem(row_position, 1, QTableWidgetItem("Revenue"))
                    self.pl_table.setItem(row_position, 2, QTableWidgetItem(str(sale.amount)))
                    self.pl_table.setItem(row_position, 3, QTableWidgetItem("Income"))
                    
        except Exception as e:
            logger.error(f"Error loading P&L data: {str(e)}")

    def load_tax_data(self):
        """Load tax data for the selected date range."""
        try:
            start_date = self.tax_start_date.date().toString("yyyy-MM-dd")
            end_date = self.tax_end_date.date().toString("yyyy-MM-dd")
            
            self.tax_table.setRowCount(0)
            
            sales = self.sales_service.get_sales_by_date_range(start_date, end_date)
            
            for sale in sales:
                if hasattr(sale, 'amount'):
                    row_position = self.tax_table.rowCount()
                    self.tax_table.insertRow(row_position)
                    self.tax_table.setItem(row_position, 0, QTableWidgetItem(str(sale.date) if hasattr(sale, 'date') else start_date))
                    self.tax_table.setItem(row_position, 1, QTableWidgetItem("Sales Tax"))
                    tax_amount = float(sale.amount) * 0.15  # Example: 15% tax
                    self.tax_table.setItem(row_position, 2, QTableWidgetItem(f"{tax_amount:.2f}"))
                    self.tax_table.setItem(row_position, 3, QTableWidgetItem("Pending"))
                    
        except Exception as e:
            logger.error(f"Error loading tax data: {str(e)}")

    def load_inventory_data(self):
        """Load inventory data."""
        try:
            self.inventory_table.setRowCount(0)
            
            inventory = self.db_service.get_all_inventory()
            
            for item in inventory:
                row_position = self.inventory_table.rowCount()
                self.inventory_table.insertRow(row_position)
                
                item_name = item.get('name') if isinstance(item, dict) else (item.name if hasattr(item, 'name') else 'N/A')
                category = item.get('category') if isinstance(item, dict) else (item.category if hasattr(item, 'category') else 'N/A')
                quantity = item.get('quantity') if isinstance(item, dict) else (item.quantity if hasattr(item, 'quantity') else 0)
                price = item.get('unit_price') if isinstance(item, dict) else (item.unit_price if hasattr(item, 'unit_price') else 0)
                
                self.inventory_table.setItem(row_position, 0, QTableWidgetItem(str(item_name)))
                self.inventory_table.setItem(row_position, 1, QTableWidgetItem(str(category)))
                self.inventory_table.setItem(row_position, 2, QTableWidgetItem(str(quantity)))
                self.inventory_table.setItem(row_position, 3, QTableWidgetItem(str(price)))
                total_value = float(quantity) * float(price)
                self.inventory_table.setItem(row_position, 4, QTableWidgetItem(f"{total_value:.2f}"))
                
        except Exception as e:
            logger.error(f"Error loading inventory data: {str(e)}")

    def load_operator_data(self):
        """Load operator performance data for the selected date range."""
        try:
            start_date = self.operator_start_date.date().toString("yyyy-MM-dd")
            end_date = self.operator_end_date.date().toString("yyyy-MM-dd")
            
            self.operator_table.setRowCount(0)
            
            sales = self.sales_service.get_sales_by_date_range(start_date, end_date)
            operator_data = {}
            
            for sale in sales:
                operator_name = sale.operator_name if hasattr(sale, 'operator_name') else 'Unknown'
                if operator_name not in operator_data:
                    operator_data[operator_name] = {'transactions': 0, 'total_amount': 0}
                operator_data[operator_name]['transactions'] += 1
                operator_data[operator_name]['total_amount'] += float(sale.amount) if hasattr(sale, 'amount') else 0
                
            for operator, data in operator_data.items():
                row_position = self.operator_table.rowCount()
                self.operator_table.insertRow(row_position)
                
                self.operator_table.setItem(row_position, 0, QTableWidgetItem(str(operator)))
                self.operator_table.setItem(row_position, 1, QTableWidgetItem(start_date))
                self.operator_table.setItem(row_position, 2, QTableWidgetItem(str(data['transactions'])))
                self.operator_table.setItem(row_position, 3, QTableWidgetItem(f"{data['total_amount']:.2f}"))
                
                # Performance rating
                performance = "Excellent" if data['transactions'] > 50 else "Good" if data['transactions'] > 20 else "Fair"
                self.operator_table.setItem(row_position, 4, QTableWidgetItem(performance))
                
        except Exception as e:
            logger.error(f"Error loading operator data: {str(e)}")

    def load_credit_data(self):
        """Load credit aging data."""
        try:
            self.credit_table.setRowCount(0)
            
            customers = self.db_service.get_all_customers()
            
            for customer in customers:
                customer_name = customer.get('name') if isinstance(customer, dict) else (customer.name if hasattr(customer, 'name') else 'N/A')
                credit_amount = customer.get('credit_balance') if isinstance(customer, dict) else (customer.credit_balance if hasattr(customer, 'credit_balance') else 0)
                
                if float(credit_amount) > 0:
                    row_position = self.credit_table.rowCount()
                    self.credit_table.insertRow(row_position)
                    
                    self.credit_table.setItem(row_position, 0, QTableWidgetItem(str(customer_name)))
                    self.credit_table.setItem(row_position, 1, QTableWidgetItem(f"{credit_amount:.2f}"))
                    
                    # Dummy due date
                    due_date = "2026-02-12"
                    self.credit_table.setItem(row_position, 2, QTableWidgetItem(due_date))
                    
                    # Calculate days overdue
                    days_overdue = 0
                    self.credit_table.setItem(row_position, 3, QTableWidgetItem(str(days_overdue)))
                    
                    status = "Overdue" if days_overdue > 0 else "Current"
                    status_item = QTableWidgetItem(status)
                    if days_overdue > 0:
                        status_item.setBackground(QColor(255, 200, 200))
                    self.credit_table.setItem(row_position, 4, status_item)
                    
        except Exception as e:
            logger.error(f"Error loading credit data: {str(e)}")

    def generate_daily_sales_report(self):
        """Generate daily sales report."""
        try:
            date_str = self.daily_sales_date.date().toString("yyyy-MM-dd")
            format_type = self.daily_sales_format.currentText().lower()

            report_data = {
                "date": date_str,
                "format": format_type
            }

            self.daily_sales_progress.setVisible(True)
            worker = ReportWorker("daily_sales", report_data)
            worker.finished.connect(self.on_report_finished)
            worker.start()

        except Exception as e:
            logger.error(f"Error generating daily sales report: {str(e)}")
            QMessageBox.critical(self, "Error", f"Failed to generate report: {str(e)}")

    def generate_p_l_report(self):
        """Generate P&L statement."""
        try:
            start_date = self.pl_start_date.date().toString("yyyy-MM-dd")
            end_date = self.pl_end_date.date().toString("yyyy-MM-dd")
            format_type = self.pl_format.currentText().lower()

            report_data = {
                "start_date": start_date,
                "end_date": end_date,
                "format": format_type
            }

            self.pl_progress.setVisible(True)
            worker = ReportWorker("p_l", report_data)
            worker.finished.connect(self.on_report_finished)
            worker.start()

        except Exception as e:
            logger.error(f"Error generating P&L report: {str(e)}")
            QMessageBox.critical(self, "Error", f"Failed to generate report: {str(e)}")

    def generate_tax_summary_report(self):
        """Generate tax summary report."""
        try:
            start_date = self.tax_start_date.date().toString("yyyy-MM-dd")
            end_date = self.tax_end_date.date().toString("yyyy-MM-dd")
            format_type = self.tax_format.currentText().lower()

            report_data = {
                "start_date": start_date,
                "end_date": end_date,
                "format": format_type
            }

            self.tax_progress.setVisible(True)
            worker = ReportWorker("tax_summary", report_data)
            worker.finished.connect(self.on_report_finished)
            worker.start()

        except Exception as e:
            logger.error(f"Error generating tax summary: {str(e)}")
            QMessageBox.critical(self, "Error", f"Failed to generate report: {str(e)}")

    def generate_inventory_report(self):
        """Generate inventory report."""
        try:
            format_type = self.inventory_format.currentText().lower()

            report_data = {
                "format": format_type
            }

            self.inventory_progress.setVisible(True)
            worker = ReportWorker("inventory", report_data)
            worker.finished.connect(self.on_report_finished)
            worker.start()

        except Exception as e:
            logger.error(f"Error generating inventory report: {str(e)}")
            QMessageBox.critical(self, "Error", f"Failed to generate report: {str(e)}")

    def generate_operator_performance_report(self):
        """Generate operator performance report."""
        try:
            start_date = self.operator_start_date.date().toString("yyyy-MM-dd")
            end_date = self.operator_end_date.date().toString("yyyy-MM-dd")
            format_type = self.operator_format.currentText().lower()

            report_data = {
                "start_date": start_date,
                "end_date": end_date,
                "format": format_type
            }

            self.operator_progress.setVisible(True)
            worker = ReportWorker("operator_performance", report_data)
            worker.finished.connect(self.on_report_finished)
            worker.start()

        except Exception as e:
            logger.error(f"Error generating operator performance report: {str(e)}")
            QMessageBox.critical(self, "Error", f"Failed to generate report: {str(e)}")

    def generate_credit_aging_report(self):
        """Generate credit aging report."""
        try:
            format_type = self.credit_format.currentText().lower()

            report_data = {
                "format": format_type
            }

            self.credit_progress.setVisible(True)
            worker = ReportWorker("credit_aging", report_data)
            worker.finished.connect(self.on_report_finished)
            worker.start()

        except Exception as e:
            logger.error(f"Error generating credit aging report: {str(e)}")
            QMessageBox.critical(self, "Error", f"Failed to generate report: {str(e)}")

    def on_report_finished(self, success, message, file_path):
        """Handle report generation completion."""
        if success:
            reply = QMessageBox.question(
                self,
                "Report Generated",
                f"{message}\n\nDo you want to open the file?",
                QMessageBox.Yes | QMessageBox.No
            )

            if reply == QMessageBox.Yes:
                try:
                    os.startfile(file_path) if os.name == 'nt' else os.system(f"open {file_path}")
                except Exception as e:
                    logger.error(f"Error opening file: {str(e)}")
                    QMessageBox.warning(self, "Error", "Could not open file")
        else:
            QMessageBox.critical(self, "Error", message)
