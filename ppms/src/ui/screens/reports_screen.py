"""
Reports Screen - Generate and view reports
"""

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QComboBox, QDateEdit, QMessageBox, QTabWidget, QTextEdit,
    QFileDialog, QProgressBar
)
from PyQt5.QtCore import Qt, QDate, QThread, pyqtSignal
from PyQt5.QtGui import QFont
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

        # Controls
        controls_layout = QHBoxLayout()
        controls_layout.addWidget(QLabel("Select Date:"))

        self.daily_sales_date = QDateEdit()
        self.daily_sales_date.setDate(QDate.currentDate())
        controls_layout.addWidget(self.daily_sales_date)

        # Format selection
        controls_layout.addWidget(QLabel("Format:"))
        self.daily_sales_format = QComboBox()
        self.daily_sales_format.addItems(["PDF", "Excel"])
        controls_layout.addWidget(self.daily_sales_format)

        # Generate button
        generate_btn = QPushButton("Generate Report")
        generate_btn.clicked.connect(self.generate_daily_sales_report)
        controls_layout.addWidget(generate_btn)
        controls_layout.addStretch()

        layout.addLayout(controls_layout)

        # Preview
        self.daily_sales_preview = QTextEdit()
        self.daily_sales_preview.setReadOnly(True)
        layout.addWidget(QLabel("Preview:"))
        layout.addWidget(self.daily_sales_preview)

        # Progress
        self.daily_sales_progress = QProgressBar()
        self.daily_sales_progress.setVisible(False)
        layout.addWidget(self.daily_sales_progress)

        widget.setLayout(layout)
        return widget

    def create_p_l_tab(self) -> QWidget:
        """Create P&L statement tab."""
        widget = QWidget()
        layout = QVBoxLayout()

        # Controls
        controls_layout = QHBoxLayout()
        controls_layout.addWidget(QLabel("Start Date:"))

        self.pl_start_date = QDateEdit()
        self.pl_start_date.setDate(QDate(QDate.currentDate().year, QDate.currentDate().month, 1))
        controls_layout.addWidget(self.pl_start_date)

        controls_layout.addWidget(QLabel("End Date:"))
        self.pl_end_date = QDateEdit()
        self.pl_end_date.setDate(QDate.currentDate())
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

        # Preview
        self.pl_preview = QTextEdit()
        self.pl_preview.setReadOnly(True)
        layout.addWidget(QLabel("Preview:"))
        layout.addWidget(self.pl_preview)

        # Progress
        self.pl_progress = QProgressBar()
        self.pl_progress.setVisible(False)
        layout.addWidget(self.pl_progress)

        widget.setLayout(layout)
        return widget

    def create_tax_summary_tab(self) -> QWidget:
        """Create tax summary tab."""
        widget = QWidget()
        layout = QVBoxLayout()

        # Controls
        controls_layout = QHBoxLayout()
        controls_layout.addWidget(QLabel("Start Date:"))

        self.tax_start_date = QDateEdit()
        self.tax_start_date.setDate(QDate(QDate.currentDate().year, QDate.currentDate().month, 1))
        controls_layout.addWidget(self.tax_start_date)

        controls_layout.addWidget(QLabel("End Date:"))
        self.tax_end_date = QDateEdit()
        self.tax_end_date.setDate(QDate.currentDate())
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

        # Preview
        self.tax_preview = QTextEdit()
        self.tax_preview.setReadOnly(True)
        layout.addWidget(QLabel("Preview:"))
        layout.addWidget(self.tax_preview)

        # Progress
        self.tax_progress = QProgressBar()
        self.tax_progress.setVisible(False)
        layout.addWidget(self.tax_progress)

        widget.setLayout(layout)
        return widget

    def create_inventory_tab(self) -> QWidget:
        """Create inventory report tab."""
        widget = QWidget()
        layout = QVBoxLayout()

        # Controls
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

        # Preview
        self.inventory_preview = QTextEdit()
        self.inventory_preview.setReadOnly(True)
        layout.addWidget(QLabel("Preview:"))
        layout.addWidget(self.inventory_preview)

        # Progress
        self.inventory_progress = QProgressBar()
        self.inventory_progress.setVisible(False)
        layout.addWidget(self.inventory_progress)

        widget.setLayout(layout)
        return widget

    def create_operator_performance_tab(self) -> QWidget:
        """Create operator performance tab."""
        widget = QWidget()
        layout = QVBoxLayout()

        # Controls
        controls_layout = QHBoxLayout()
        controls_layout.addWidget(QLabel("Start Date:"))

        self.operator_start_date = QDateEdit()
        self.operator_start_date.setDate(QDate(QDate.currentDate().year, QDate.currentDate().month, 1))
        controls_layout.addWidget(self.operator_start_date)

        controls_layout.addWidget(QLabel("End Date:"))
        self.operator_end_date = QDateEdit()
        self.operator_end_date.setDate(QDate.currentDate())
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

        # Preview
        self.operator_preview = QTextEdit()
        self.operator_preview.setReadOnly(True)
        layout.addWidget(QLabel("Preview:"))
        layout.addWidget(self.operator_preview)

        # Progress
        self.operator_progress = QProgressBar()
        self.operator_progress.setVisible(False)
        layout.addWidget(self.operator_progress)

        widget.setLayout(layout)
        return widget

    def create_credit_aging_tab(self) -> QWidget:
        """Create credit aging tab."""
        widget = QWidget()
        layout = QVBoxLayout()

        # Controls
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

        # Preview
        self.credit_preview = QTextEdit()
        self.credit_preview.setReadOnly(True)
        layout.addWidget(QLabel("Preview:"))
        layout.addWidget(self.credit_preview)

        # Progress
        self.credit_progress = QProgressBar()
        self.credit_progress.setVisible(False)
        layout.addWidget(self.credit_progress)

        widget.setLayout(layout)
        return widget

    def load_summary_data(self):
        """Load summary data for preview."""
        try:
            # Load sample data for previews
            pass
        except Exception as e:
            logger.error(f"Error loading summary data: {str(e)}")

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
